"""
04_data_governance_optimization.py
Data Governance Monitoring & Statistical Optimization Modeling
Mayo Clinic Informatics Analyst Portfolio

Demonstrates:
- Data quality monitoring & SLA tracking
- Statistical process control (SPC) charts
- Optimization: resource allocation simulation
- Real-time-style alerting logic
- Tableau/Power BI-ready export formatting
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from scipy.optimize import linprog
import warnings
warnings.filterwarnings("ignore")

OUT = "outputs"
os.makedirs(OUT, exist_ok=True)
MAYO_BLUE = "#002F6C"; ACCENT = "#E87722"; MAYO_TEAL = "#007398"
GREEN = "#2E8B57"; RED = "#C0392B"

# ── 1. Load data ──────────────────────────────────────────────────────────────
gov        = pd.read_csv("data/data_governance_log.csv",
                          parse_dates=["detected_date","resolved_date"])
encounters = pd.read_csv("data/encounters.csv", parse_dates=["encounter_date"])
qm         = pd.read_csv("data/quality_measures.csv")

# ── 2. SLA Compliance Analysis ───────────────────────────────────────────────
sla_days = {"Critical": 2, "High": 7, "Medium": 14, "Low": 30}
gov["sla_target"] = gov["severity"].map(sla_days)
gov["sla_breached"] = (gov["days_to_resolve"] > gov["sla_target"]).astype(int)

sla_summary = (gov.groupby("severity")
               .agg(total=("issue_id","count"),
                    breached=("sla_breached","sum"),
                    resolved=("resolved_flag","sum"),
                    avg_days=("days_to_resolve","mean"))
               .assign(breach_rate=lambda d: d["breached"]/d["total"] * 100,
                       resolution_rate=lambda d: d["resolved"]/d["total"] * 100)
               .round(2))
print("SLA Compliance Summary:")
print(sla_summary.to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

severity_order = ["Critical","High","Medium","Low"]
sla_ordered = sla_summary.reindex(severity_order)

colors_sev = [RED, ACCENT, MAYO_TEAL, GREEN]
axes[0].bar(severity_order, sla_ordered["breach_rate"], color=colors_sev)
axes[0].axhline(20, color="gray", linestyle="--", alpha=0.6, label="20% threshold")
axes[0].set_title("SLA Breach Rate by Severity", fontweight="bold", color=MAYO_BLUE)
axes[0].set_ylabel("Breach Rate (%)"); axes[0].legend()

axes[1].bar(severity_order, sla_ordered["avg_days"], color=colors_sev, alpha=0.8)
for i, (sev, row) in enumerate(sla_ordered.iterrows()):
    axes[1].axhline(sla_days[sev], xmin=i/4, xmax=(i+1)/4,
                    color="black", linewidth=2.5, linestyle="--")
axes[1].set_title("Avg Days to Resolve vs. SLA Target (--)",
                   fontweight="bold", color=MAYO_BLUE)
axes[1].set_ylabel("Days")

plt.suptitle("Data Governance SLA Compliance", fontsize=13,
             fontweight="bold", color=MAYO_BLUE)
plt.tight_layout()
plt.savefig(f"{OUT}/04a_sla_compliance.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 04a_sla_compliance.png")

# ── 3. Statistical Process Control (SPC) — Weekly Issue Volume ───────────────
gov["week"] = gov["detected_date"].dt.to_period("W")
weekly = gov.groupby("week").size().reset_index(name="issues")
weekly["week_dt"] = weekly["week"].dt.to_timestamp()

mean_issues = weekly["issues"].mean()
std_issues  = weekly["issues"].std()
ucl = mean_issues + 3 * std_issues   # Upper Control Limit
lcl = max(0, mean_issues - 3 * std_issues)

weekly["out_of_control"] = (weekly["issues"] > ucl) | (weekly["issues"] < lcl)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(weekly["week_dt"], weekly["issues"], color=MAYO_BLUE, linewidth=1.5,
        marker="o", markersize=3, label="Weekly Issues")
ax.axhline(mean_issues, color=GREEN,  linestyle="-",  linewidth=1.5, label=f"Mean ({mean_issues:.0f})")
ax.axhline(ucl,         color=RED,    linestyle="--", linewidth=1.5, label=f"UCL ({ucl:.0f})")
ax.axhline(lcl,         color=ACCENT, linestyle="--", linewidth=1.5, label=f"LCL ({lcl:.0f})")
# Highlight out-of-control points
ooc = weekly[weekly["out_of_control"]]
ax.scatter(ooc["week_dt"], ooc["issues"], color=RED, s=80, zorder=5, label="Out of Control")
ax.fill_between(weekly["week_dt"], lcl, ucl, alpha=0.07, color=GREEN)
ax.set_title("Statistical Process Control Chart — Weekly Data Quality Issues",
              fontsize=12, fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel("Week"); ax.set_ylabel("Issue Count")
ax.legend(fontsize=9); plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(f"{OUT}/04b_spc_chart.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 04b_spc_chart.png")

# ── 4. Issue Type Pareto Analysis ─────────────────────────────────────────────
pareto = (gov.groupby("issue_type").size()
            .sort_values(ascending=False)
            .reset_index(name="count"))
pareto["cum_pct"] = pareto["count"].cumsum() / pareto["count"].sum() * 100

fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.bar(pareto["issue_type"], pareto["count"], color=MAYO_BLUE)
ax2 = ax1.twinx()
ax2.plot(pareto["issue_type"], pareto["cum_pct"], color=ACCENT,
         marker="o", linewidth=2.5)
ax2.axhline(80, color="gray", linestyle="--", alpha=0.7, label="80% threshold")
ax1.set_title("Pareto Analysis — Data Quality Issue Types",
               fontsize=12, fontweight="bold", color=MAYO_BLUE)
ax1.set_xlabel("Issue Type"); ax1.set_ylabel("Count", color=MAYO_BLUE)
ax2.set_ylabel("Cumulative %", color=ACCENT)
plt.xticks(rotation=25, ha="right")
ax2.legend(fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUT}/04c_pareto_issues.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 04c_pareto_issues.png")

# ── 5. Optimization: Staffing Allocation Model ───────────────────────────────
# Simulate optimal allocation of analyst hours across departments
# to maximize quality measure improvement subject to capacity constraints

print("\nRunning optimization model...")
departments = ["Cardiology","Oncology","Neurology","Orthopedics",
               "Primary Care","Endocrinology","Pulmonology","Nephrology"]
n = len(departments)

# Expected quality improvement per analyst-hour (simulated, from historical data)
np.random.seed(99)
improvement_per_hour = np.random.uniform(0.005, 0.025, n)

# Constraints: total hours = 200/week; min 15 hrs per dept; max 40 hrs
# Objective: maximize total improvement = -minimize negative improvement
c = -improvement_per_hour   # negate for minimization

A_ub = np.eye(n)              # each dept <= 40
b_ub = np.full(n, 40.0)

A_eq = np.ones((1, n))        # total = 200
b_eq = np.array([200.0])

bounds = [(15, 40)] * n       # min 15, max 40 per dept

result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)

opt_hours = result.x.round(1)
alloc_df = pd.DataFrame({
    "Department": departments,
    "Optimal_Hours": opt_hours,
    "Improvement_Per_Hour": improvement_per_hour.round(4),
    "Expected_Improvement_Pts": (opt_hours * improvement_per_hour * 100).round(2)
}).sort_values("Expected_Improvement_Pts", ascending=False)

print("Optimal Analyst Hour Allocation:")
print(alloc_df.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].barh(alloc_df["Department"], alloc_df["Optimal_Hours"], color=MAYO_BLUE)
axes[0].axvline(200/n, color="gray", linestyle="--", label=f"Equal split ({200/n:.0f} hrs)")
axes[0].set_title("Optimal Analyst Hours by Department",
                   fontweight="bold", color=MAYO_BLUE)
axes[0].set_xlabel("Hours per Week"); axes[0].legend()

axes[1].barh(alloc_df["Department"], alloc_df["Expected_Improvement_Pts"],
             color=[ACCENT if v > alloc_df["Expected_Improvement_Pts"].mean() else MAYO_TEAL
                    for v in alloc_df["Expected_Improvement_Pts"]])
axes[1].axvline(alloc_df["Expected_Improvement_Pts"].mean(),
                color="gray", linestyle="--", label="Avg")
axes[1].set_title("Expected Quality Score Improvement (%pts)",
                   fontweight="bold", color=MAYO_BLUE)
axes[1].set_xlabel("Improvement (percentage points)"); axes[1].legend()

plt.suptitle("Linear Programming: Analyst Resource Optimization",
             fontsize=13, fontweight="bold", color=MAYO_BLUE)
plt.tight_layout()
plt.savefig(f"{OUT}/04d_optimization_allocation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 04d_optimization_allocation.png")

# ── 6. Tableau/Power BI Ready Export ─────────────────────────────────────────
# Flatten quality measures with trend direction for BI tools
qm_export = qm.copy()
qm_export["above_benchmark"] = (qm_export["gap_to_benchmark"] >= 0).astype(int)
qm_export["performance_pct"] = (qm_export["performance_rate"] * 100).round(1)
qm_export["benchmark_pct"]   = (qm_export["national_benchmark"] * 100).round(1)
qm_export["gap_pct"]         = (qm_export["gap_to_benchmark"] * 100).round(1)
qm_export.to_csv(f"{OUT}/04e_bi_ready_quality_measures.csv", index=False)
print("  ✓ Saved 04e_bi_ready_quality_measures.csv (Tableau/Power BI ready)")

print("\n✅  Script 04 complete — all outputs saved to ./outputs/")
