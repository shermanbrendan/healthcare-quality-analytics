"""
02_readmission_prediction_model.py
Statistical & Predictive Modeling — 30-Day Readmission Risk
Mayo Clinic Informatics Analyst Portfolio

Demonstrates:
- Feature engineering on EHR-style data
- Logistic regression + Random Forest classification
- Model evaluation (ROC, confusion matrix, feature importance)
- Statistical significance testing
- Actionable risk stratification output
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection   import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model      import LogisticRegression
from sklearn.ensemble          import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing     import StandardScaler, LabelEncoder
from sklearn.metrics           import (roc_auc_score, roc_curve, confusion_matrix,
                                       classification_report, ConfusionMatrixDisplay)
from sklearn.pipeline          import Pipeline
from sklearn.impute            import SimpleImputer
from scipy                     import stats
import warnings
warnings.filterwarnings("ignore")

OUT = "outputs"
os.makedirs(OUT, exist_ok=True)
MAYO_BLUE = "#002F6C"; ACCENT = "#E87722"; MAYO_TEAL = "#007398"

# ── 1. Load & merge ───────────────────────────────────────────────────────────
print("Loading data...")
patients   = pd.read_csv("data/patients.csv")
encounters = pd.read_csv("data/encounters.csv", parse_dates=["encounter_date"])

df = encounters.merge(patients, on="patient_id", how="left")
df = df[df["encounter_type"] == "Inpatient"].copy()
print(f"  Inpatient encounters for modeling: {len(df):,}")

# ── 2. Feature Engineering ────────────────────────────────────────────────────
print("Engineering features...")
df["encounter_month"]   = df["encounter_date"].dt.month
df["encounter_dow"]     = df["encounter_date"].dt.dayofweek
df["is_weekend_admit"]  = df["encounter_dow"].isin([5, 6]).astype(int)
df["age_group"]         = pd.cut(df["age"], bins=[0,40,60,75,120],
                                  labels=["<40","40-60","60-75","75+"])

# Encode categoricals
cat_cols = ["department_x", "insurance_type", "primary_icd10",
            "discharge_disposition", "age_group", "ehr_system"]
df_enc = df.copy()
le = LabelEncoder()
for col in cat_cols:
    if col in df_enc.columns:
        df_enc[col] = df_enc[col].fillna("Unknown")
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))

feature_cols = [
    "age", "chronic_conditions", "length_of_stay", "total_charges",
    "er_visit_flag", "is_weekend_admit", "encounter_month",
    "department_x", "insurance_type", "primary_icd10",
    "discharge_disposition", "age_group", "ehr_system"
]
feature_cols = [c for c in feature_cols if c in df_enc.columns]

X = df_enc[feature_cols].fillna(0)
y = df_enc["readmission_30d"]

print(f"  Features: {len(feature_cols)}")
print(f"  Readmission rate: {y.mean():.1%}")

# ── 3. Train / Test Split ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# ── 4. Logistic Regression ────────────────────────────────────────────────────
print("\nTraining Logistic Regression...")
lr_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
    ("model",   LogisticRegression(max_iter=1000, C=0.5, random_state=42))
])
lr_pipe.fit(X_train, y_train)
lr_probs = lr_pipe.predict_proba(X_test)[:, 1]
lr_auc = roc_auc_score(y_test, lr_probs)
print(f"  Logistic Regression AUC: {lr_auc:.4f}")

# ── 5. Random Forest ──────────────────────────────────────────────────────────
print("Training Random Forest...")
rf_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("model",   RandomForestClassifier(n_estimators=200, max_depth=8,
                                        min_samples_leaf=20, random_state=42,
                                        n_jobs=-1))
])
rf_pipe.fit(X_train, y_train)
rf_probs = rf_pipe.predict_proba(X_test)[:, 1]
rf_auc = roc_auc_score(y_test, rf_probs)
print(f"  Random Forest AUC: {rf_auc:.4f}")

# ── 6. Gradient Boosting ──────────────────────────────────────────────────────
print("Training Gradient Boosting...")
gb_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("model",   GradientBoostingClassifier(n_estimators=150, max_depth=4,
                                            learning_rate=0.05, random_state=42))
])
gb_pipe.fit(X_train, y_train)
gb_probs = gb_pipe.predict_proba(X_test)[:, 1]
gb_auc = roc_auc_score(y_test, gb_probs)
print(f"  Gradient Boosting AUC: {gb_auc:.4f}")

# ── 7. ROC Curve Comparison ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for name, probs, color in [
        ("Logistic Regression", lr_probs, MAYO_TEAL),
        ("Random Forest",       rf_probs, MAYO_BLUE),
        ("Gradient Boosting",   gb_probs, ACCENT)]:
    fpr, tpr, _ = roc_curve(y_test, probs)
    auc = roc_auc_score(y_test, probs)
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", linewidth=2, color=color)

axes[0].plot([0,1],[0,1],"k--", alpha=0.4)
axes[0].set_xlabel("False Positive Rate"); axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC Curves — 30-Day Readmission Models",
                   fontsize=12, fontweight="bold", color=MAYO_BLUE)
axes[0].legend(fontsize=9)

# Confusion matrix for best model (Gradient Boosting)
best_preds = (gb_probs >= 0.5).astype(int)
cm = confusion_matrix(y_test, best_preds)
ConfusionMatrixDisplay(cm, display_labels=["No Readmit","Readmit"]).plot(
    ax=axes[1], colorbar=False, cmap="Blues")
axes[1].set_title("Confusion Matrix — Gradient Boosting",
                   fontsize=12, fontweight="bold", color=MAYO_BLUE)
plt.tight_layout()
plt.savefig(f"{OUT}/02a_model_evaluation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 02a_model_evaluation.png")

# ── 8. Feature Importance ─────────────────────────────────────────────────────
rf_model = rf_pipe.named_steps["model"]
importances = pd.Series(rf_model.feature_importances_, index=feature_cols)
importances = importances.sort_values(ascending=True).tail(12)

fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(importances.index, importances.values,
               color=[ACCENT if v > importances.mean() else MAYO_TEAL
                      for v in importances.values])
ax.set_title("Feature Importances — Random Forest\n(30-Day Readmission Prediction)",
              fontsize=12, fontweight="bold", color=MAYO_BLUE)
ax.set_xlabel("Importance Score")
plt.tight_layout()
plt.savefig(f"{OUT}/02b_feature_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 02b_feature_importance.png")

# ── 9. Risk Stratification ────────────────────────────────────────────────────
test_df = X_test.copy()
test_df["readmission_30d"] = y_test.values
test_df["risk_score"] = gb_probs
test_df["risk_tier"]  = pd.cut(gb_probs,
                                 bins=[0, 0.10, 0.20, 0.35, 1.0],
                                 labels=["Low (<10%)", "Moderate (10-20%)",
                                         "High (20-35%)", "Very High (>35%)"])

strat = (test_df.groupby("risk_tier", observed=True)
         .agg(patients=("readmission_30d","count"),
              actual_readmits=("readmission_30d","sum"),
              avg_risk_score=("risk_score","mean"))
         .assign(actual_rate=lambda d: d["actual_readmits"]/d["patients"]))

print("\nRisk Stratification Summary:")
print(strat.to_string())

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(strat))
ax.bar(x, strat["patients"], color=MAYO_BLUE, alpha=0.7, label="Total Patients")
ax2 = ax.twinx()
ax2.plot(x, strat["actual_rate"] * 100, "o-", color=ACCENT,
         linewidth=2.5, markersize=8, label="Actual Readmit Rate %")
ax.set_xticks(x); ax.set_xticklabels(strat.index, rotation=15)
ax.set_ylabel("Patient Count", color=MAYO_BLUE)
ax2.set_ylabel("Actual Readmission Rate (%)", color=ACCENT)
ax.set_title("Risk Tier Distribution vs. Actual Readmission Rate",
              fontsize=12, fontweight="bold", color=MAYO_BLUE)
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labels1+labels2, loc="upper left")
plt.tight_layout()
plt.savefig(f"{OUT}/02c_risk_stratification.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ Saved 02c_risk_stratification.png")

# ── 10. Statistical Test: LOS difference by readmission ──────────────────────
readmit_los  = df[df["readmission_30d"] == 1]["length_of_stay"].dropna()
no_readm_los = df[df["readmission_30d"] == 0]["length_of_stay"].dropna()
t_stat, p_val = stats.ttest_ind(readmit_los, no_readm_los)
print(f"\nT-test: LOS (readmitted vs. not)")
print(f"  Readmitted mean LOS:     {readmit_los.mean():.2f} days")
print(f"  Non-readmitted mean LOS: {no_readm_los.mean():.2f} days")
print(f"  t={t_stat:.3f}, p={p_val:.4f} {'*** Significant' if p_val < 0.05 else 'Not significant'}")

# Print classification report
print("\nClassification Report — Gradient Boosting:")
print(classification_report(y_test, best_preds, target_names=["No Readmit","Readmit"]))

print("\n✅  Script 02 complete — all plots saved to ./outputs/")
