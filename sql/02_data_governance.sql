-- =============================================================================
-- 02_data_governance.sql
-- Data Quality & Governance Queries  |  Mayo Clinic Quality Analytics Portfolio
-- Author: Portfolio Project
-- Description: Data governance monitoring, issue tracking, SLA compliance,
--              referential integrity checks, and data quality scorecards.
--              Mirrors real-world EHR data stewardship workflows.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- GOV 1: Data Quality Issue Summary by Table and Severity
-- -----------------------------------------------------------------------------
SELECT
    table_name,
    issue_type,
    severity,
    COUNT(*)                                                      AS issue_count,
    SUM(resolved_flag)                                            AS resolved_count,
    COUNT(*) - SUM(resolved_flag)                                 AS open_count,
    ROUND(100.0 * SUM(resolved_flag) / COUNT(*), 1)              AS resolution_rate_pct,
    ROUND(AVG(days_to_resolve), 1)                               AS avg_days_to_resolve
FROM data_governance_log
GROUP BY table_name, issue_type, severity
ORDER BY
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'High'     THEN 2
        WHEN 'Medium'   THEN 3
        WHEN 'Low'      THEN 4
    END,
    issue_count DESC;


-- -----------------------------------------------------------------------------
-- GOV 2: Open Critical & High Issues (SLA Breach Risk)
-- -----------------------------------------------------------------------------
-- SLA targets: Critical = resolve within 2 days, High = 7 days,
--              Medium = 14 days, Low = 30 days
SELECT
    issue_id,
    table_name,
    issue_type,
    field_name,
    severity,
    source_system,
    detected_date,
    days_to_resolve,
    CASE severity
        WHEN 'Critical' THEN 2
        WHEN 'High'     THEN 7
        WHEN 'Medium'   THEN 14
        ELSE 30
    END AS sla_days,
    CASE
        WHEN days_to_resolve > (
            CASE severity
                WHEN 'Critical' THEN 2
                WHEN 'High'     THEN 7
                WHEN 'Medium'   THEN 14
                ELSE 30
            END
        ) THEN 'SLA BREACHED'
        ELSE 'WITHIN SLA'
    END AS sla_status
FROM data_governance_log
WHERE resolved_flag = 0
   OR (resolved_flag = 1 AND days_to_resolve > (
        CASE severity
            WHEN 'Critical' THEN 2
            WHEN 'High'     THEN 7
            WHEN 'Medium'   THEN 14
            ELSE 30
        END
    ))
ORDER BY
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'High'     THEN 2
        WHEN 'Medium'   THEN 3
        ELSE 4
    END,
    days_to_resolve DESC;


-- -----------------------------------------------------------------------------
-- GOV 3: Source System Data Quality Scorecard
-- -----------------------------------------------------------------------------
WITH issue_counts AS (
    SELECT
        source_system,
        COUNT(*)                                            AS total_issues,
        SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) AS critical,
        SUM(CASE WHEN severity = 'High'     THEN 1 ELSE 0 END) AS high,
        SUM(CASE WHEN severity = 'Medium'   THEN 1 ELSE 0 END) AS medium,
        SUM(CASE WHEN severity = 'Low'      THEN 1 ELSE 0 END) AS low_sev,
        SUM(resolved_flag)                                  AS resolved,
        ROUND(AVG(days_to_resolve), 1)                     AS avg_resolution_days,
        -- Weighted severity score (lower = better quality)
        ROUND(
            (SUM(CASE WHEN severity = 'Critical' THEN 4.0 ELSE 0 END) +
             SUM(CASE WHEN severity = 'High'     THEN 3.0 ELSE 0 END) +
             SUM(CASE WHEN severity = 'Medium'   THEN 2.0 ELSE 0 END) +
             SUM(CASE WHEN severity = 'Low'      THEN 1.0 ELSE 0 END))
            / COUNT(*), 2
        ) AS weighted_severity_score
    FROM data_governance_log
    GROUP BY source_system
)
SELECT
    *,
    ROUND(100.0 * resolved / total_issues, 1) AS resolution_rate_pct,
    -- Data quality grade
    CASE
        WHEN weighted_severity_score < 1.5 AND resolution_rate_pct >= 90 THEN 'A'
        WHEN weighted_severity_score < 2.0 AND resolution_rate_pct >= 80 THEN 'B'
        WHEN weighted_severity_score < 2.5 AND resolution_rate_pct >= 70 THEN 'C'
        ELSE 'D'
    END AS quality_grade
FROM issue_counts
ORDER BY weighted_severity_score ASC;


-- -----------------------------------------------------------------------------
-- GOV 4: Referential Integrity Check — Orphaned Encounters
-- (Encounters with no matching patient record)
-- -----------------------------------------------------------------------------
SELECT
    e.encounter_id,
    e.patient_id,
    e.encounter_date,
    e.encounter_type,
    e.department,
    'ORPHANED_ENCOUNTER' AS issue_type
FROM encounters e
LEFT JOIN patients p ON e.patient_id = p.patient_id
WHERE p.patient_id IS NULL
LIMIT 500;   -- cap output for readability


-- -----------------------------------------------------------------------------
-- GOV 5: Data Completeness Report by Table Field
-- -----------------------------------------------------------------------------
-- Patients table completeness
SELECT 'patients'    AS table_name, 'age'              AS field, COUNT(*) AS total,
       SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END)        AS nulls FROM patients
UNION ALL
SELECT 'patients', 'sex', COUNT(*),
       SUM(CASE WHEN sex IS NULL THEN 1 ELSE 0 END) FROM patients
UNION ALL
SELECT 'patients', 'zip_code', COUNT(*),
       SUM(CASE WHEN zip_code IS NULL THEN 1 ELSE 0 END) FROM patients
UNION ALL
SELECT 'patients', 'insurance_type', COUNT(*),
       SUM(CASE WHEN insurance_type IS NULL THEN 1 ELSE 0 END) FROM patients
-- Encounters table completeness
UNION ALL
SELECT 'encounters', 'encounter_date', COUNT(*),
       SUM(CASE WHEN encounter_date IS NULL THEN 1 ELSE 0 END) FROM encounters
UNION ALL
SELECT 'encounters', 'primary_icd10', COUNT(*),
       SUM(CASE WHEN primary_icd10 IS NULL THEN 1 ELSE 0 END) FROM encounters
UNION ALL
SELECT 'encounters', 'total_charges', COUNT(*),
       SUM(CASE WHEN total_charges IS NULL THEN 1 ELSE 0 END) FROM encounters
-- Lab results completeness
UNION ALL
SELECT 'lab_results', 'result_value', COUNT(*),
       SUM(CASE WHEN result_value IS NULL THEN 1 ELSE 0 END) FROM lab_results
ORDER BY table_name, field;


-- -----------------------------------------------------------------------------
-- GOV 6: Monthly Data Quality Trend (Issues Opened vs. Resolved)
-- -----------------------------------------------------------------------------
SELECT
    STRFTIME('%Y-%m', detected_date)   AS month,
    COUNT(*)                            AS issues_opened,
    SUM(resolved_flag)                  AS issues_resolved,
    COUNT(*) - SUM(resolved_flag)       AS net_open_delta,
    ROUND(AVG(days_to_resolve), 1)     AS avg_days_to_resolve,
    SUM(CASE WHEN severity IN ('Critical','High') THEN 1 ELSE 0 END) AS high_critical_count
FROM data_governance_log
GROUP BY month
ORDER BY month ASC;
