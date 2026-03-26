"""
01_exploratory_quality_analysis.py
Exploratory Data Analysis & Quality Measure Insights
Mayo Clinic Informatics Analyst Portfolio

Demonstrates:
- Data loading & validation
- Descriptive statistics on healthcare quality data
- Trend analysis across departments and quarters
- Matplotlib / Seaborn visualizations saved to ./outputs/
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.gridspec import GridSpec

OUT = "outputs"
os.makedirs(OUT, exist_ok=True)

# ── palette ───────────────────────────────────────────────────────────────────
MAYO_BLUE  = "#002F6C"
MAYO_TEAL  = "#007398"
ACCENT     = "#E87722"
LIGHT_GRAY = "#F5F5F5"
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.0)

# ── 1. Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
patients   = pd.read_csv("data/patients.csv")
encounters = pd.read_csv("data/encounters.csv", parse_dates=["encounter_date"])
qm         = pd.read_csv("data/quality_measures.csv")
surveys    = pd.read_csv("data/patient_surveys.csv", parse_dates=["survey_date"])
labs       = pd.read_csv("data/lab_results.csv", parse_dates=["result_date"])
gov        = pd.read_csv("data/data_governance_log.csv",
                          parse_dates=["detected_date","resolved_date"])

print(f"  patients:   {len(patients):,}")
print(f"  encounters: {len(encounters):,}")
print(f"  quality_measures: {len(qm):,}")
print(f"  surveys:    {len(surveys):,}")
print(f"  labs:       {len(labs):,}")
print(f"  governance: {len(gov):,}")

# ── 2. Patient Demographics ───────────────────────────────────────────────────
print("\n── Patient Demographics ──")
print(patients[["age","chronic_conditions"]].describe().round(2))
print("\nInsurance mix:\n", patients["insurance_type"].value_counts())
print("\nDepartment mix:\n", patients["department"].value_counts())

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Patient Demographics Overview", fontsize=14, fontweight="bold",
             color=MAYO_BLUE, y=1.02)

axes[0].hist(patients["age"], bins=20, color=MAYO_BLUE, edgecolor="white")
axes[0].set_title("Age Distribution")
axes[0].set_xlabel("Age"); axes[0].set_ylabel("Count")

ins_counts = patients["insurance_type"].value_counts()
axes[1].barh(ins_counts.index, ins_counts.values, color=MAYO_TEAL)
axes[1].set_title("Insurance Type")
axes[1].set_xlabel("Patient Count")

cc = patients["chronic_conditions"].value_counts().sort_index()
axes[2].bar(cc.index, cc.values, color=ACCENT)
axes[2].set_title("Chronic Conditions Count")
axes[2].set_xlabel("# Conditions"); axes[2].set_ylabel("Patients")

plt.tight_layout()
plt.savefig(f"{OUT}/01a_patient_demographics.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  ✓ Saved 01a_patient_demographics.png")

# ── 3. Encounter Volume Trend ─────────────────────────────────────────────────
encounters["year_month"] = encounters["encounter_date"].dt.to_period("M")
monthly = (encounters.groupby(["year_month","encounter_type"])
           .size().reset_index(name="count"))
monthly["year_month_dt"] = monthly["year_month"].dt.to_timestamp()

fig, ax = plt.subplots(figsize=(14, 5))
for enc_type, grp in monthly.groupby("encounter_type"):
    ax.plot(grp["year_month_dt"], grp["count"], marker="o", markersize=3,
            linewidth=1.8, label=enc_type)
ax.set_title("Monthly Encounter Volume by Type", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel("Month"); ax.set_ylabel("Encounters")
ax.legend(loc="upper left", fontsize=9)
ax.xaxis.set_major_locator(mticker.MaxNLocator(12))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{OUT}/01b_encounter_volume_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 01b_encounter_volume_trend.png")

# ── 4. Quality Measure Performance Heatmap ────────────────────────────────────
latest_q = qm["quarter"].max()
pivot = (qm[qm["quarter"] == latest_q]
         .pivot(index="department", columns="measure", values="performance_rate"))

fig, ax = plt.subplots(figsize=(14, 7))
sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn",
            vmin=0.5, vmax=1.0, ax=ax,
            linewidths=0.5, linecolor="white",
            cbar_kws={"label": "Performance Rate"})
ax.set_title(f"Quality Measure Performance Heatmap — {latest_q}",
             fontsize=13, fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel(""); ax.set_ylabel("")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(f"{OUT}/01c_quality_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 01c_quality_heatmap.png")

# ── 5. Readmission Rate by Department ────────────────────────────────────────
inpatient = encounters[encounters["encounter_type"] == "Inpatient"]
readm = (inpatient.groupby("department")["readmission_30d"]
         .agg(["mean","sum","count"])
         .rename(columns={"mean":"rate","sum":"readmissions","count":"total"})
         .sort_values("rate", ascending=True))

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(readm.index, readm["rate"] * 100,
               color=[ACCENT if r > 16 else MAYO_TEAL for r in readm["rate"]])
ax.axvline(15, color="red", linestyle="--", linewidth=1.5, label="CMS Benchmark (15%)")
ax.set_title("30-Day Readmission Rate by Department", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel("Readmission Rate (%)"); ax.legend()
for bar, val in zip(bars, readm["rate"] * 100):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUT}/01d_readmission_by_dept.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 01d_readmission_by_dept.png")

# ── 6. Quality Trend for Top 3 Measures Across Quarters ─────────────────────
top_measures = ["BP_Control", "HbA1c_Testing", "Readmission_Rate"]
trend_data = qm[qm["measure"].isin(top_measures)].copy()
trend_agg = (trend_data.groupby(["quarter","measure"])["performance_rate"]
             .mean().reset_index())

fig, ax = plt.subplots(figsize=(13, 5))
for measure, grp in trend_agg.groupby("measure"):
    ax.plot(grp["quarter"], grp["performance_rate"] * 100,
            marker="o", markersize=5, linewidth=2, label=measure)
ax.set_title("Quality Measure Trend — Hospital Average", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel("Quarter"); ax.set_ylabel("Performance Rate (%)")
ax.legend(); plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{OUT}/01e_quality_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 01e_quality_trend.png")

# ── 7. Lab Abnormal Rate by Test ──────────────────────────────────────────────
lab_abn = (labs.groupby("test_name")
           .agg(total=("lab_id","count"),
                abnormal=("abnormal_flag","sum"),
                critical=("critical_flag","sum"))
           .assign(abnormal_rate=lambda d: d["abnormal"]/d["total"],
                   critical_rate=lambda d: d["critical"]/d["total"])
           .sort_values("abnormal_rate", ascending=False))

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(lab_abn))
w = 0.35
ax.bar(x - w/2, lab_abn["abnormal_rate"] * 100, w, label="Abnormal %", color=MAYO_TEAL)
ax.bar(x + w/2, lab_abn["critical_rate"]  * 100, w, label="Critical %", color=ACCENT)
ax.set_xticks(x); ax.set_xticklabels(lab_abn.index, rotation=30, ha="right")
ax.set_title("Lab Result Abnormal & Critical Rates by Test", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
ax.set_ylabel("Rate (%)"); ax.legend()
plt.tight_layout()
plt.savefig(f"{OUT}/01f_lab_abnormal_rates.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 01f_lab_abnormal_rates.png")

print("\n✅  Script 01 complete — all plots saved to ./outputs/")
