"""
03_survey_satisfaction_analytics.py
Patient Satisfaction (HCAHPS-Style) Analytics & Reporting
Mayo Clinic Informatics Analyst Portfolio

Demonstrates:
- HCAHPS domain scoring and top-box rate calculation
- Trend analysis and CMS submission-ready summaries
- Correlation analysis between satisfaction domains and clinical outcomes
- Matplotlib dashboard-style output
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings("ignore")

OUT = "outputs"
os.makedirs(OUT, exist_ok=True)
MAYO_BLUE = "#002F6C"; ACCENT = "#E87722"; MAYO_TEAL = "#007398"
GREEN = "#2E8B57"; RED = "#C0392B"

# ── 1. Load data ──────────────────────────────────────────────────────────────
surveys    = pd.read_csv("data/patient_surveys.csv", parse_dates=["survey_date"])
encounters = pd.read_csv("data/encounters.csv", parse_dates=["encounter_date"])

df = surveys.merge(encounters[["encounter_id","department","encounter_type",
                                "readmission_30d","length_of_stay","total_charges"]],
                   on="encounter_id", how="left")
print(f"Surveys merged with encounters: {len(df):,} rows")

DOMAINS = ["Communication_Nurses","Communication_Doctors","Responsiveness",
           "Pain_Management","Medication_Communication","Discharge_Info",
           "Hospital_Environment","Overall_Rating"]

# ── 2. Domain Summary ─────────────────────────────────────────────────────────
summary = df[DOMAINS].agg(["mean","std","median"]).T.round(3)
summary.columns = ["Mean","StdDev","Median"]
summary["Top_Box_Pct"] = [(df[d] >= 4.5).mean() * 100 for d in DOMAINS]
summary = summary.round(2)
print("\nDomain Score Summary:")
print(summary.to_string())

# ── 3. Dashboard: Domain Scores Bar + Trend ───────────────────────────────────
fig = plt.figure(figsize=(16, 12))
fig.suptitle("Patient Satisfaction Analytics Dashboard",
             fontsize=16, fontweight="bold", color=MAYO_BLUE, y=1.01)

from matplotlib.gridspec import GridSpec
gs = GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

# 3a: Domain mean scores
ax1 = fig.add_subplot(gs[0, 0])
colors = [GREEN if v >= 3.8 else ACCENT if v >= 3.4 else RED
          for v in summary["Mean"]]
bars = ax1.barh(summary.index, summary["Mean"], color=colors)
ax1.axvline(3.5, color="gray", linestyle="--", alpha=0.6, label="Acceptable threshold")
ax1.set_xlim(1, 5)
ax1.set_title("Mean Domain Scores", fontweight="bold", color=MAYO_BLUE)
ax1.set_xlabel("Score (1-5)")
for bar, val in zip(bars, summary["Mean"]):
    ax1.text(bar.get_width() + 0.04, bar.get_y() + bar.get_height()/2,
             f"{val:.2f}", va="center", fontsize=8)
ax1.legend(fontsize=8)

# 3b: Top-box percentages
ax2 = fig.add_subplot(gs[0, 1])
ax2.barh(summary.index, summary["Top_Box_Pct"],
         color=[GREEN if v >= 40 else ACCENT if v >= 25 else RED
                for v in summary["Top_Box_Pct"]])
ax2.set_title("Top-Box Rate (Score ≥ 4.5)", fontweight="bold", color=MAYO_BLUE)
ax2.set_xlabel("Top-Box Rate (%)")
ax2.set_xlim(0, 70)
for i, val in enumerate(summary["Top_Box_Pct"]):
    ax2.text(val + 0.5, i, f"{val:.0f}%", va="center", fontsize=8)

# 3c: Monthly trend — Overall Rating & Recommend Rate
df["month"] = df["survey_date"].dt.to_period("M")
monthly = df.groupby("month").agg(
    overall=("Overall_Rating","mean"),
    recommend=("would_recommend","mean"),
    n=("survey_id","count")
).reset_index()
monthly["month_dt"] = monthly["month"].dt.to_timestamp()

ax3 = fig.add_subplot(gs[1, :])
ax3.plot(monthly["month_dt"], monthly["overall"], color=MAYO_BLUE,
         marker="o", markersize=4, linewidth=2, label="Avg Overall Rating (left)")
ax3_r = ax3.twinx()
ax3_r.plot(monthly["month_dt"], monthly["recommend"] * 100,
           color=ACCENT, marker="s", markersize=4, linewidth=2,
           label="Would Recommend % (right)")
ax3.set_ylabel("Overall Rating (1-5)", color=MAYO_BLUE)
ax3_r.set_ylabel("Would Recommend (%)", color=ACCENT)
ax3.set_title("Monthly Satisfaction Trend", fontweight="bold", color=MAYO_BLUE)
lines1, labels1 = ax3.get_legend_handles_labels()
lines2, labels2 = ax3_r.get_legend_handles_labels()
ax3.legend(lines1+lines2, labels1+labels2, loc="lower left", fontsize=9)
plt.xticks(rotation=30)

plt.savefig(f"{OUT}/03a_satisfaction_dashboard.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 03a_satisfaction_dashboard.png")

# ── 4. Domain Correlation Heatmap ────────────────────────────────────────────
corr_matrix = df[DOMAINS].corr()
fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm",
            vmin=-1, vmax=1, ax=ax, mask=mask,
            linewidths=0.5, square=True)
ax.set_title("Survey Domain Correlation Matrix",
              fontsize=13, fontweight="bold", color=MAYO_BLUE)
plt.tight_layout()
plt.savefig(f"{OUT}/03b_domain_correlation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 03b_domain_correlation.png")

# ── 5. Satisfaction vs. Clinical Outcomes ────────────────────────────────────
inpatient = df[df["encounter_type"] == "Inpatient"].dropna(
    subset=["Overall_Rating","readmission_30d","length_of_stay"])

# Bin by satisfaction quartile
inpatient["sat_quartile"] = pd.qcut(inpatient["Overall_Rating"], q=4,
                                     labels=["Q1 (Low)","Q2","Q3","Q4 (High)"])
outcomes = inpatient.groupby("sat_quartile", observed=True).agg(
    avg_los=("length_of_stay","mean"),
    readmit_rate=("readmission_30d","mean"),
    n=("survey_id","count")
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(outcomes["sat_quartile"], outcomes["avg_los"],
            color=[MAYO_BLUE, MAYO_TEAL, ACCENT, GREEN])
axes[0].set_title("Avg Length of Stay by Satisfaction Quartile",
                   fontweight="bold", color=MAYO_BLUE)
axes[0].set_xlabel("Satisfaction Quartile"); axes[0].set_ylabel("Avg LOS (days)")

axes[1].bar(outcomes["sat_quartile"], outcomes["readmit_rate"] * 100,
            color=[RED, ACCENT, MAYO_TEAL, GREEN])
axes[1].axhline(15, color="gray", linestyle="--", label="CMS 15% benchmark")
axes[1].set_title("30-Day Readmission Rate by Satisfaction Quartile",
                   fontweight="bold", color=MAYO_BLUE)
axes[1].set_xlabel("Satisfaction Quartile"); axes[1].set_ylabel("Readmission Rate (%)")
axes[1].legend()

plt.suptitle("Satisfaction vs. Clinical Outcomes", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
plt.tight_layout()
plt.savefig(f"{OUT}/03c_satisfaction_vs_outcomes.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 03c_satisfaction_vs_outcomes.png")

# ── 6. Statistical significance: Overall Rating vs Readmission ───────────────
readmit_scores    = df[df["readmission_30d"] == 1]["Overall_Rating"].dropna()
no_readmit_scores = df[df["readmission_30d"] == 0]["Overall_Rating"].dropna()
from scipy.stats import ttest_ind
t, p = ttest_ind(readmit_scores, no_readmit_scores)
print(f"\nSatisfaction t-test (readmitted vs not):")
print(f"  Readmitted mean: {readmit_scores.mean():.3f}")
print(f"  Not readmitted:  {no_readmit_scores.mean():.3f}")
print(f"  t={t:.3f}, p={p:.4f} {'*** Significant' if p < 0.05 else 'Not significant'}")

# Pearson correlation: Overall Rating vs LOS
valid = df.dropna(subset=["Overall_Rating","length_of_stay"])
r, p_r = pearsonr(valid["Overall_Rating"], valid["length_of_stay"])
print(f"\nPearson r (Overall Rating vs LOS): r={r:.3f}, p={p_r:.4f}")

# ── 7. CMS-style submission summary ──────────────────────────────────────────
cms_report = pd.DataFrame({
    "Domain": DOMAINS,
    "Mean_Score": [df[d].mean() for d in DOMAINS],
    "Top_Box_Pct": [(df[d] >= 4.5).mean() * 100 for d in DOMAINS],
    "N_Responses": [df[d].notna().sum() for d in DOMAINS],
})
cms_report = cms_report.round(2)
cms_report.to_csv(f"{OUT}/03d_cms_submission_summary.csv", index=False)
print("\nCMS Submission Summary:")
print(cms_report.to_string(index=False))
print(f"\n  ✓ Saved 03d_cms_submission_summary.csv")

print("\n✅  Script 03 complete — all outputs saved to ./outputs/")
