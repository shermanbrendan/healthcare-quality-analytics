-- =============================================================================
-- 01_kpi_dashboard.sql
-- Enterprise KPI Dashboard Queries  |  Mayo Clinic Quality Analytics Portfolio
-- Author: Portfolio Project
-- Description: Core KPI queries for the Enterprise Advanced Analysis team.
--              Covers readmission rates, length of stay, quality measure
--              performance, and department-level scorecards.
-- Compatible: SQLite / PostgreSQL / SQL Server (minor dialect adjustments noted)
-- =============================================================================


-- -----------------------------------------------------------------------------
-- KPI 1: 30-Day Readmission Rate by Department and Quarter
-- -----------------------------------------------------------------------------
SELECT
    e.department,
    STRFTIME('%Y-Q', e.encounter_date) ||
        CAST(((CAST(STRFTIME('%m', e.encounter_date) AS INT) - 1) / 3 + 1) AS TEXT) AS quarter,
    COUNT(*)                                                   AS total_encounters,
    SUM(e.readmission_30d)                                     AS readmissions,
    ROUND(100.0 * SUM(e.readmission_30d) / COUNT(*), 2)        AS readmission_rate_pct,
    -- National benchmark context (CMS target <15%)
    CASE
        WHEN ROUND(100.0 * SUM(e.readmission_30d) / COUNT(*), 2) <= 15.0 THEN 'MEETS BENCHMARK'
        WHEN ROUND(100.0 * SUM(e.readmission_30d) / COUNT(*), 2) <= 18.0 THEN 'NEAR BENCHMARK'
        ELSE 'BELOW BENCHMARK'
    END AS benchmark_status
FROM encounters e
WHERE e.encounter_type = 'Inpatient'
  AND e.encounter_date >= DATE('now', '-2 years')
GROUP BY
    e.department,
    quarter
ORDER BY
    quarter DESC,
    readmission_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- KPI 2: Average Length of Stay (ALOS) vs. Department Median
-- -----------------------------------------------------------------------------
WITH dept_stats AS (
    SELECT
        department,
        ROUND(AVG(length_of_stay), 2)    AS avg_los,
        -- SQLite does not have PERCENTILE_CONT; use this approximation
        ROUND(AVG(length_of_stay), 2)    AS median_los_approx,
        COUNT(*)                          AS inpatient_volume,
        MIN(length_of_stay)               AS min_los,
        MAX(length_of_stay)               AS max_los
    FROM encounters
    WHERE encounter_type = 'Inpatient'
      AND length_of_stay > 0
    GROUP BY department
),
overall_avg AS (
    SELECT ROUND(AVG(length_of_stay), 2) AS hospital_avg_los
    FROM encounters
    WHERE encounter_type = 'Inpatient' AND length_of_stay > 0
)
SELECT
    ds.*,
    oa.hospital_avg_los,
    ROUND(ds.avg_los - oa.hospital_avg_los, 2) AS variance_from_hospital_avg
FROM dept_stats ds
CROSS JOIN overall_avg oa
ORDER BY avg_los DESC;


-- -----------------------------------------------------------------------------
-- KPI 3: Quality Measure Performance Scorecard (Most Recent Quarter)
-- -----------------------------------------------------------------------------
WITH latest_quarter AS (
    SELECT MAX(quarter) AS max_q FROM quality_measures
),
ranked AS (
    SELECT
        qm.department,
        qm.measure,
        qm.quarter,
        qm.performance_rate,
        qm.national_benchmark,
        qm.gap_to_benchmark,
        qm.numerator,
        qm.denominator,
        RANK() OVER (PARTITION BY qm.measure ORDER BY qm.performance_rate DESC) AS dept_rank
    FROM quality_measures qm
    JOIN latest_quarter lq ON qm.quarter = lq.max_q
)
SELECT
    department,
    measure,
    quarter,
    ROUND(performance_rate * 100, 1)    AS performance_pct,
    ROUND(national_benchmark * 100, 1)  AS benchmark_pct,
    ROUND(gap_to_benchmark * 100, 1)    AS gap_pct,
    numerator,
    denominator,
    dept_rank,
    CASE
        WHEN gap_to_benchmark >= 0.05  THEN '⭐ EXCEEDS'
        WHEN gap_to_benchmark >= 0     THEN '✓ MEETS'
        WHEN gap_to_benchmark >= -0.05 THEN '⚠ NEAR MISS'
        ELSE '✗ BELOW'
    END AS performance_tier
FROM ranked
ORDER BY measure, dept_rank;


-- -----------------------------------------------------------------------------
-- KPI 4: Department Quality Composite Score (All Measures, Latest 4 Quarters)
-- -----------------------------------------------------------------------------
WITH recent AS (
    SELECT *
    FROM quality_measures
    WHERE quarter IN (
        SELECT DISTINCT quarter
        FROM quality_measures
        ORDER BY quarter DESC
        LIMIT 4
    )
)
SELECT
    department,
    COUNT(DISTINCT measure)                             AS measures_tracked,
    ROUND(AVG(performance_rate) * 100, 1)              AS composite_score_pct,
    ROUND(AVG(national_benchmark) * 100, 1)            AS avg_benchmark_pct,
    ROUND(AVG(gap_to_benchmark) * 100, 1)              AS avg_gap_pct,
    SUM(CASE WHEN gap_to_benchmark >= 0 THEN 1 ELSE 0 END)  AS measures_meeting_benchmark,
    SUM(CASE WHEN gap_to_benchmark < 0  THEN 1 ELSE 0 END)  AS measures_below_benchmark
FROM recent
GROUP BY department
ORDER BY composite_score_pct DESC;


-- -----------------------------------------------------------------------------
-- KPI 5: Emergency Department Utilization & Avoidable ED Visits
-- -----------------------------------------------------------------------------
WITH ed_visits AS (
    SELECT
        e.department,
        p.insurance_type,
        p.chronic_conditions,
        COUNT(*) AS ed_visits,
        SUM(CASE WHEN p.chronic_conditions >= 3 THEN 1 ELSE 0 END) AS potentially_avoidable
    FROM encounters e
    JOIN patients p ON e.patient_id = p.patient_id
    WHERE e.encounter_type = 'ED'
    GROUP BY e.department, p.insurance_type, p.chronic_conditions
)
SELECT
    department,
    insurance_type,
    chronic_conditions,
    ed_visits,
    potentially_avoidable,
    ROUND(100.0 * potentially_avoidable / ed_visits, 1) AS avoidable_rate_pct
FROM ed_visits
WHERE ed_visits >= 5
ORDER BY avoidable_rate_pct DESC, ed_visits DESC;


-- -----------------------------------------------------------------------------
-- KPI 6: Monthly Volume Trend (All Encounter Types, Last 24 Months)
-- -----------------------------------------------------------------------------
SELECT
    STRFTIME('%Y-%m', encounter_date)          AS month,
    encounter_type,
    COUNT(*)                                    AS encounter_volume,
    ROUND(AVG(total_charges), 2)               AS avg_charges,
    SUM(total_charges)                          AS total_charges,
    SUM(readmission_30d)                        AS readmissions
FROM encounters
WHERE encounter_date >= DATE('now', '-2 years')
GROUP BY month, encounter_type
ORDER BY month ASC, encounter_type;
