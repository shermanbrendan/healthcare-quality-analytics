-- =============================================================================
-- 03_survey_analytics.sql
-- Patient Satisfaction Survey Analytics  |  Mayo Clinic Quality Analytics Portfolio
-- Author: Portfolio Project
-- Description: HCAHPS-style survey analysis including domain scores, top-box
--              rates, trend analysis, and correlation with clinical outcomes.
--              Mirrors CMS survey submission workflows.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- SRV 1: Survey Domain Scores Summary (All Departments)
-- -----------------------------------------------------------------------------
SELECT
    ROUND(AVG(Communication_Nurses), 2)        AS avg_comm_nurses,
    ROUND(AVG(Communication_Doctors), 2)        AS avg_comm_doctors,
    ROUND(AVG(Responsiveness), 2)               AS avg_responsiveness,
    ROUND(AVG(Pain_Management), 2)              AS avg_pain_mgmt,
    ROUND(AVG(Medication_Communication), 2)     AS avg_med_comm,
    ROUND(AVG(Discharge_Info), 2)               AS avg_discharge_info,
    ROUND(AVG(Hospital_Environment), 2)         AS avg_environment,
    ROUND(AVG(Overall_Rating), 2)               AS avg_overall,
    ROUND(100.0 * AVG(would_recommend), 1)      AS pct_would_recommend,
    ROUND(100.0 * AVG(top_box_score), 1)        AS top_box_pct,
    COUNT(*)                                     AS total_surveys
FROM patient_surveys;


-- -----------------------------------------------------------------------------
-- SRV 2: Top-Box Rates by Survey Quarter
-- -----------------------------------------------------------------------------
SELECT
    STRFTIME('%Y-Q', survey_date) ||
        CAST(((CAST(STRFTIME('%m', survey_date) AS INT) - 1) / 3 + 1) AS TEXT) AS quarter,
    COUNT(*)                                          AS responses,
    ROUND(100.0 * SUM(top_box_score) / COUNT(*), 1)  AS top_box_pct,
    ROUND(100.0 * SUM(would_recommend) / COUNT(*), 1) AS recommend_pct,
    ROUND(AVG(Overall_Rating), 2)                     AS avg_overall_rating
FROM patient_surveys
GROUP BY quarter
ORDER BY quarter ASC;


-- -----------------------------------------------------------------------------
-- SRV 3: Domain Score Correlation with Overall Rating
--         (Identifies highest-impact improvement areas)
-- -----------------------------------------------------------------------------
-- Pearson correlation approximation using SQLite-compatible math
WITH base AS (
    SELECT
        Overall_Rating                 AS y,
        Communication_Nurses           AS x1,
        Communication_Doctors          AS x2,
        Responsiveness                 AS x3,
        Pain_Management                AS x4,
        Medication_Communication       AS x5,
        Discharge_Info                 AS x6,
        Hospital_Environment           AS x7
    FROM patient_surveys
),
means AS (
    SELECT
        AVG(y) AS my, AVG(x1) AS mx1, AVG(x2) AS mx2,
        AVG(x3) AS mx3, AVG(x4) AS mx4, AVG(x5) AS mx5,
        AVG(x6) AS mx6, AVG(x7) AS mx7
    FROM base
),
corr_vals AS (
    SELECT
        -- Correlation = SUM((x-mx)*(y-my)) / SQRT(SUM((x-mx)^2)*SUM((y-my)^2))
        ROUND(SUM((b.x1-m.mx1)*(b.y-m.my)) /
              (SQRT(SUM((b.x1-m.mx1)*(b.x1-m.mx1))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_comm_nurses,
        ROUND(SUM((b.x2-m.mx2)*(b.y-m.my)) /
              (SQRT(SUM((b.x2-m.mx2)*(b.x2-m.mx2))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_comm_doctors,
        ROUND(SUM((b.x3-m.mx3)*(b.y-m.my)) /
              (SQRT(SUM((b.x3-m.mx3)*(b.x3-m.mx3))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_responsiveness,
        ROUND(SUM((b.x4-m.mx4)*(b.y-m.my)) /
              (SQRT(SUM((b.x4-m.mx4)*(b.x4-m.mx4))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_pain_mgmt,
        ROUND(SUM((b.x5-m.mx5)*(b.y-m.my)) /
              (SQRT(SUM((b.x5-m.mx5)*(b.x5-m.mx5))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_med_comm,
        ROUND(SUM((b.x6-m.mx6)*(b.y-m.my)) /
              (SQRT(SUM((b.x6-m.mx6)*(b.x6-m.mx6))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_discharge_info,
        ROUND(SUM((b.x7-m.mx7)*(b.y-m.my)) /
              (SQRT(SUM((b.x7-m.mx7)*(b.x7-m.mx7))) *
               SQRT(SUM((b.y-m.my)*(b.y-m.my)))), 4)  AS corr_environment
    FROM base b CROSS JOIN means m
)
SELECT
    'Communication_Nurses'       AS domain, corr_comm_nurses    AS correlation FROM corr_vals
UNION ALL SELECT 'Communication_Doctors',       corr_comm_doctors   FROM corr_vals
UNION ALL SELECT 'Responsiveness',              corr_responsiveness FROM corr_vals
UNION ALL SELECT 'Pain_Management',             corr_pain_mgmt      FROM corr_vals
UNION ALL SELECT 'Medication_Communication',    corr_med_comm       FROM corr_vals
UNION ALL SELECT 'Discharge_Info',              corr_discharge_info FROM corr_vals
UNION ALL SELECT 'Hospital_Environment',        corr_environment    FROM corr_vals
ORDER BY ABS(correlation) DESC;


-- -----------------------------------------------------------------------------
-- SRV 4: Surveys Joined to Clinical Outcomes
--         (Do satisfied patients have better outcomes?)
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN s.Overall_Rating >= 4.5 THEN 'High Satisfaction (4.5-5.0)'
        WHEN s.Overall_Rating >= 3.5 THEN 'Mid Satisfaction (3.5-4.4)'
        ELSE 'Low Satisfaction (<3.5)'
    END AS satisfaction_tier,
    COUNT(*)                                        AS n,
    ROUND(AVG(e.length_of_stay), 2)                AS avg_los,
    ROUND(100.0 * AVG(e.readmission_30d), 1)       AS readmission_rate_pct,
    ROUND(AVG(e.total_charges), 0)                 AS avg_charges
FROM patient_surveys s
JOIN encounters e ON s.encounter_id = e.encounter_id
WHERE e.encounter_type = 'Inpatient'
GROUP BY satisfaction_tier
ORDER BY satisfaction_tier DESC;


-- -----------------------------------------------------------------------------
-- SRV 5: Low-Scoring Encounters Needing Follow-Up (Bottom 10%)
-- -----------------------------------------------------------------------------
WITH survey_scores AS (
    SELECT
        survey_id,
        encounter_id,
        Overall_Rating,
        NTILE(10) OVER (ORDER BY Overall_Rating ASC) AS decile
    FROM patient_surveys
)
SELECT
    ss.survey_id,
    ss.encounter_id,
    ss.Overall_Rating,
    e.department,
    e.encounter_type,
    e.encounter_date,
    e.attending_provider,
    'FOLLOW_UP_REQUIRED' AS action_flag
FROM survey_scores ss
JOIN encounters e ON ss.encounter_id = e.encounter_id
WHERE ss.decile = 1
ORDER BY ss.Overall_Rating ASC
LIMIT 200;
