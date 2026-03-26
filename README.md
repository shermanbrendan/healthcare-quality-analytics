# Healthcare Quality Analytics Portfolio
### Informatics Analyst — Enterprise Advanced Analysis

A production-style analytics portfolio built to demonstrate competency in
healthcare data analytics, statistical modeling, and data governance — aligned
with the skills required for an Informatics Analyst role on an Enterprise
Advanced Analysis team.

---

## Repository Structure

```
healthcare-quality-analytics/
│
├── data/                          # Generated synthetic datasets (66,768 rows)
│   ├── patients.csv               # 5,000 de-identified patient records
│   ├── encounters.csv             # 20,000 clinical encounters (2023–2025)
│   ├── quality_measures.csv       # 768 HEDIS-style measure records
│   ├── patient_surveys.csv        # 8,000 HCAHPS-style survey responses
│   ├── data_governance_log.csv    # 3,000 data quality issue records
│   └── lab_results.csv            # 30,000 lab results (HbA1c, LDL, BP, etc.)
│
├── sql/
│   ├── 01_kpi_dashboard.sql       # Readmission, LOS, quality measure KPIs
│   ├── 02_data_governance.sql     # Data quality, SLA tracking, integrity checks
│   └── 03_survey_analytics.sql   # HCAHPS domain scoring & outcome correlation
│
├── python/
│   ├── 01_exploratory_quality_analysis.py    # EDA, demographics, quality trends
│   ├── 02_readmission_prediction_model.py    # ML models: LR, RF, GBM + risk tiers
│   ├── 03_survey_satisfaction_analytics.py  # Satisfaction trends & CMS reporting
│   └── 04_data_governance_optimization.py   # SPC charts, Pareto, LP optimization
│
├── outputs/                       # All generated charts and BI-ready exports
│
├── generate_dataset.py            # Run this first to regenerate all data
└── README.md
```

---

## Skills Demonstrated

### SQL
- Multi-table JOINs, CTEs, window functions (`RANK`, `NTILE`, `LAG`)
- KPI aggregation: readmission rates, ALOS, quality composite scores
- Data governance queries: SLA breach detection, referential integrity checks
- Pearson correlation approximation in pure SQL
- CMS-aligned survey analysis with domain scoring

### Python
- **Pandas / NumPy** — data wrangling, feature engineering, cohort analysis
- **Scikit-learn** — Logistic Regression, Random Forest, Gradient Boosting
- **SciPy** — statistical testing (t-tests, Pearson r), Linear Programming
- **Matplotlib / Seaborn** — dashboard-style visualizations, SPC charts
- ML pipeline with imputation, scaling, cross-validation, ROC/AUC evaluation

### Healthcare Domain Knowledge
- HEDIS quality measures (BP Control, HbA1c Testing, Colorectal Screening, etc.)
- HCAHPS survey domains and top-box rate calculation
- CMS 30-day readmission benchmarks
- EHR systems: Epic / Clarity data structures
- ICD-10 coding, data governance, and data stewardship workflows

### Analytics & Modeling
- Predictive risk stratification (4-tier readmission risk model)
- Statistical Process Control (Shewhart X-bar chart) for data quality monitoring
- Linear Programming for analyst resource allocation optimization
- Pareto analysis for root-cause prioritization
- Tableau/Power BI-ready flat-file exports

---

## Project Summaries

### `01_exploratory_quality_analysis.py`
Full EDA across all six datasets. Outputs six charts covering patient
demographics, encounter volume trends, a quality measure performance heatmap
by department, readmission rates by department vs. the CMS 15% benchmark,
and lab result abnormality rates.

### `02_readmission_prediction_model.py`
Trains three classifiers (Logistic Regression, Random Forest, Gradient
Boosting) on inpatient encounter data to predict 30-day readmission risk.
Includes feature importance analysis, ROC curve comparison, and a 4-tier
risk stratification table ready for care management workflows.

### `03_survey_satisfaction_analytics.py`
HCAHPS-style patient satisfaction analysis: domain scoring, top-box rates,
monthly trend charts, domain correlation heatmap, and a clinical outcomes
comparison (LOS and readmission rate by satisfaction quartile). Exports a
CMS submission-formatted summary CSV.

### `04_data_governance_optimization.py`
Monitors data quality issues with SLA compliance analysis by severity level.
Produces a Statistical Process Control chart for weekly issue volume and a
Pareto chart of issue types. Includes a Linear Programming optimization model
to allocate analyst hours across departments to maximize quality improvement.

---

## SQL Highlights

| Script | Key Queries |
|---|---|
| `01_kpi_dashboard.sql` | Readmission rate by dept/quarter, ALOS by dept, quality scorecard, ED utilization, volume trend |
| `02_data_governance.sql` | SLA breach detection, source system grading, orphan record detection, completeness report |
| `03_survey_analytics.sql` | Domain correlation (Pearson in SQL), top-box trends, satisfaction vs. outcomes join, low-score flagging |

---

## Setup & Usage

### Requirements
```
Python 3.9+
pandas, numpy, matplotlib, seaborn, scikit-learn, scipy
```

### Install
```bash
pip install pandas numpy matplotlib seaborn scikit-learn scipy
```

### Run (in order)
```bash
python generate_dataset.py                             # Generate all data
python python/01_exploratory_quality_analysis.py
python python/02_readmission_prediction_model.py
python python/03_survey_satisfaction_analytics.py
python python/04_data_governance_optimization.py
```

SQL scripts can be run against any SQLite, PostgreSQL, or SQL Server database
after loading the CSV files. SQLite example:
```bash
sqlite3 healthcare.db
.mode csv
.import data/encounters.csv encounters
.import data/patients.csv patients
# ... repeat for other tables
.read sql/01_kpi_dashboard.sql
```

---

## Data Notes

All data is **fully synthetic** — generated with seeded random processes to
simulate realistic distributions without any PHI. The data is modeled after
common patterns in:
- CMS Hospital Compare datasets
- HEDIS technical specifications
- HCAHPS survey methodology
- Epic/Clarity EHR data structures

---

## Contact

Built as a demonstration of skills for a Healthcare Informatics Analyst role.
Feel free to reach out with questions or collaboration opportunities.
