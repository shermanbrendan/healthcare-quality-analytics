"""
generate_dataset.py
Generates synthetic Mayo-style healthcare quality analytics dataset.
Run this first to produce all CSV files used by the portfolio scripts.
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

OUT = "data"
os.makedirs(OUT, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────
def rand_dates(start, end, n):
    delta = (end - start).days
    return [start + timedelta(days=random.randint(0, delta)) for _ in range(n)]

# ── 1. PATIENTS ──────────────────────────────────────────────────────────────
N_PATIENTS = 5000
departments = ["Cardiology", "Oncology", "Neurology", "Orthopedics",
               "Primary Care", "Endocrinology", "Pulmonology", "Nephrology"]
insurances  = ["Medicare", "Medicaid", "BlueCross", "Aetna", "UnitedHealth",
               "Self-Pay", "Cigna", "Humana"]
sexes       = ["M", "F", "Other"]

patients = pd.DataFrame({
    "patient_id":    [f"PT{str(i).zfill(6)}" for i in range(1, N_PATIENTS+1)],
    "age":           np.random.randint(18, 95, N_PATIENTS),
    "sex":           np.random.choice(sexes, N_PATIENTS, p=[0.49, 0.49, 0.02]),
    "zip_code":      np.random.choice([55901,55902,55904,55906,55960,55972,55987], N_PATIENTS),
    "department":    np.random.choice(departments, N_PATIENTS),
    "insurance_type":np.random.choice(insurances, N_PATIENTS,
                         p=[0.28,0.18,0.15,0.12,0.10,0.07,0.05,0.05]),
    "chronic_conditions": np.random.poisson(1.4, N_PATIENTS).clip(0, 6),
    "ehr_system":    np.random.choice(["Epic", "Clarity"], N_PATIENTS, p=[0.75, 0.25]),
})
patients.to_csv(f"{OUT}/patients.csv", index=False)
print(f"✓ patients.csv  ({len(patients):,} rows)")

# ── 2. ENCOUNTERS ────────────────────────────────────────────────────────────
N_ENC = 20000
start_dt = datetime(2023, 1, 1)
end_dt   = datetime(2025, 12, 31)
enc_types = ["Inpatient", "Outpatient", "ED", "Telehealth", "Observation"]
discharge_disp = ["Home", "SNF", "Rehab", "AMA", "Expired", "Transferred"]

pat_ids = patients["patient_id"].tolist()
enc_dates = rand_dates(start_dt, end_dt, N_ENC)

encounters = pd.DataFrame({
    "encounter_id":    [f"ENC{str(i).zfill(7)}" for i in range(1, N_ENC+1)],
    "patient_id":      np.random.choice(pat_ids, N_ENC),
    "encounter_date":  enc_dates,
    "encounter_type":  np.random.choice(enc_types, N_ENC, p=[0.20,0.50,0.12,0.13,0.05]),
    "department":      np.random.choice(departments, N_ENC),
    "length_of_stay":  np.where(
                           np.random.choice(enc_types, N_ENC, p=[0.20,0.50,0.12,0.13,0.05]) == "Inpatient",
                           np.random.exponential(4.5, N_ENC).clip(1, 45).round(1),
                           0),
    "discharge_disposition": np.random.choice(discharge_disp, N_ENC,
                                 p=[0.68,0.10,0.08,0.03,0.02,0.09]),
    "readmission_30d": np.random.choice([0,1], N_ENC, p=[0.84,0.16]),
    "er_visit_flag":   np.random.choice([0,1], N_ENC, p=[0.78,0.22]),
    "primary_icd10":   np.random.choice(
                           ["I10","E11","J18","M79","Z12","I25","N18","C34","F32","G20"],
                           N_ENC),
    "attending_provider": [f"DR{str(random.randint(1,150)).zfill(4)}" for _ in range(N_ENC)],
    "total_charges":   np.round(np.random.lognormal(9.0, 1.1, N_ENC), 2),
})
encounters["encounter_date"] = pd.to_datetime(encounters["encounter_date"])
encounters.to_csv(f"{OUT}/encounters.csv", index=False)
print(f"✓ encounters.csv  ({len(encounters):,} rows)")

# ── 3. QUALITY MEASURES (HEDIS-style) ────────────────────────────────────────
measures = ["BP_Control", "HbA1c_Testing", "Colorectal_Screening",
            "Mammography", "Flu_Vaccine", "Statin_Therapy",
            "Readmission_Rate", "CAHPS_Composite"]
quarters = ["2023-Q1","2023-Q2","2023-Q3","2023-Q4",
            "2024-Q1","2024-Q2","2024-Q3","2024-Q4",
            "2025-Q1","2025-Q2","2025-Q3","2025-Q4"]

rows = []
for dept in departments:
    for measure in measures:
        base = random.uniform(0.58, 0.91)
        trend = random.uniform(-0.005, 0.015)   # slight upward drift
        for q_idx, q in enumerate(quarters):
            val = np.clip(base + trend * q_idx + np.random.normal(0, 0.02), 0, 1)
            national_benchmark = round(random.uniform(0.70, 0.88), 4)
            rows.append({
                "department": dept,
                "measure": measure,
                "quarter": q,
                "performance_rate": round(val, 4),
                "national_benchmark": national_benchmark,
                "gap_to_benchmark": round(val - national_benchmark, 4),
                "denominator": random.randint(80, 600),
                "numerator": 0,   # filled below
            })

qm = pd.DataFrame(rows)
qm["numerator"] = (qm["performance_rate"] * qm["denominator"]).round().astype(int)
qm.to_csv(f"{OUT}/quality_measures.csv", index=False)
print(f"✓ quality_measures.csv  ({len(qm):,} rows)")

# ── 4. PATIENT SATISFACTION SURVEYS (HCAHPS-style) ───────────────────────────
N_SURVEYS = 8000
domains = ["Communication_Nurses", "Communication_Doctors", "Responsiveness",
           "Pain_Management", "Medication_Communication", "Discharge_Info",
           "Hospital_Environment", "Overall_Rating"]

survey_rows = []
for _ in range(N_SURVEYS):
    enc_id = f"ENC{str(random.randint(1, N_ENC)).zfill(7)}"
    base_sat = random.gauss(3.7, 0.6)
    survey_rows.append({
        "survey_id":    f"SRV{str(random.randint(1,9999999)).zfill(7)}",
        "encounter_id": enc_id,
        "survey_date":  rand_dates(start_dt, end_dt, 1)[0],
        **{d: round(np.clip(base_sat + random.gauss(0, 0.3), 1, 5), 1) for d in domains},
        "would_recommend": random.choice([0, 1], p=[0.18, 0.82]) if hasattr(random, 'nothing') else np.random.choice([0,1], p=[0.18,0.82]),
        "top_box_score":  random.randint(0, 1),
    })

surveys = pd.DataFrame(survey_rows)
surveys["would_recommend"] = np.random.choice([0,1], len(surveys), p=[0.18,0.82])
surveys["top_box_score"]   = np.random.choice([0,1], len(surveys), p=[0.22,0.78])
surveys["survey_date"] = pd.to_datetime(surveys["survey_date"])
surveys.to_csv(f"{OUT}/patient_surveys.csv", index=False)
print(f"✓ patient_surveys.csv  ({len(surveys):,} rows)")

# ── 5. DATA GOVERNANCE LOG ────────────────────────────────────────────────────
tables_list = ["patients","encounters","quality_measures","patient_surveys","lab_results"]
issue_types = ["Missing_Value","Duplicate_Record","Out_of_Range","Format_Error",
               "Referential_Integrity","Late_Submission","Coding_Error"]

gov_rows = []
for _ in range(3000):
    detected = rand_dates(start_dt, end_dt, 1)[0]
    resolved = detected + timedelta(days=random.randint(0, 30))
    gov_rows.append({
        "issue_id":      f"DQ{str(random.randint(1,999999)).zfill(6)}",
        "table_name":    random.choice(tables_list),
        "issue_type":    random.choice(issue_types),
        "field_name":    random.choice(["patient_id","encounter_date","icd10_code",
                                        "total_charges","performance_rate","age","zip_code"]),
        "detected_date": detected,
        "resolved_date": resolved,
        "days_to_resolve": (resolved - detected).days,
        "severity":      random.choice(["Low","Medium","High","Critical"],
                                       ),
        "resolved_flag": random.choice([0, 1], p=[0.12, 0.88]) if False else np.random.choice([0,1],p=[0.12,0.88]),
        "source_system": random.choice(["Epic","Clarity","Manual_Entry","External_Feed"]),
    })

gov = pd.DataFrame(gov_rows)
gov["resolved_flag"] = np.random.choice([0,1], len(gov), p=[0.12,0.88])
gov["detected_date"] = pd.to_datetime(gov["detected_date"])
gov["resolved_date"]  = pd.to_datetime(gov["resolved_date"])
gov.to_csv(f"{OUT}/data_governance_log.csv", index=False)
print(f"✓ data_governance_log.csv  ({len(gov):,} rows)")

# ── 6. LAB RESULTS ────────────────────────────────────────────────────────────
N_LABS = 30000
lab_tests = {
    "HbA1c":         (4.0, 14.0, 5.7, 1.8),
    "LDL":           (40,  220,  105, 30),
    "Systolic_BP":   (80,  200,  128, 18),
    "Diastolic_BP":  (50,  120,  80,  12),
    "eGFR":          (5,   120,  75,  22),
    "INR":           (0.8, 4.0,  1.2, 0.5),
    "Hemoglobin":    (6.0, 18.0, 13.5, 2.0),
    "Creatinine":    (0.4, 6.0,  1.0, 0.5),
}
test_names = list(lab_tests.keys())

lab_rows = []
for _ in range(N_LABS):
    test = random.choice(test_names)
    lo, hi, mu, sigma = lab_tests[test]
    val = round(np.clip(np.random.normal(mu, sigma), lo, hi), 2)
    lab_rows.append({
        "lab_id":       f"LAB{str(random.randint(1,9999999)).zfill(7)}",
        "patient_id":   random.choice(pat_ids),
        "test_name":    test,
        "result_value": val,
        "result_date":  rand_dates(start_dt, end_dt, 1)[0],
        "abnormal_flag":int(val < mu - sigma or val > mu + 2*sigma),
        "critical_flag":int(val < lo*1.2 or val > hi*0.9),
    })

labs = pd.DataFrame(lab_rows)
labs["result_date"] = pd.to_datetime(labs["result_date"])
labs.to_csv(f"{OUT}/lab_results.csv", index=False)
print(f"✓ lab_results.csv  ({len(labs):,} rows)")

print("\n✅ All datasets generated in ./data/")
print(f"   Total rows across all files: {N_PATIENTS+N_ENC+len(qm)+N_SURVEYS+3000+N_LABS:,}")
