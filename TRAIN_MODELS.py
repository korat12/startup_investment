import os
import pickle
import numpy as np
import pandas as pd

from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier, XGBRegressor

# -----------------------------------------
# Paths
# -----------------------------------------
INPUT = "data/df_enhanced_fixed.csv"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------------------------
# Load
# -----------------------------------------
df = pd.read_csv(INPUT, parse_dates=["Date"], dayfirst=False)

# -----------------------------------------
# Build labels from event history
# -----------------------------------------
# Sort within company by date
df = df.sort_values(["Company_Cleaned", "Date"], kind="mergesort")

# Next event per company
df["next_date"]   = df.groupby("Company_Cleaned")["Date"].shift(-1)
df["next_amount"] = df.groupby("Company_Cleaned")["Amount_Cr"].shift(-1)

# Time-to-next (days)
df["time_to_next_round"] = (df["next_date"] - df["Date"]).dt.days

# Labels
df["raised_again_12m"]   = np.where(df["time_to_next_round"].notna() & (df["time_to_next_round"] <= 365), 1,
                             np.where(df["time_to_next_round"].notna(), 0, np.nan))
df["amount_next_round"]  = df["next_amount"]

# -----------------------------------------
# Feature set
# -----------------------------------------
features = [
    "Amount_Cr",
    "Cumulative_Funding_Prior",
    "Rolling_6m_Funding_Lagged",
    "Rolling_12m_Funding_Lagged",
    "Rolling_6m_Rounds_Lagged",
    "Rolling_12m_Rounds_Lagged",
    "Sector",
    "Sub_Sector",
    "city",
    "state",
]

# Keep only rows with all features present
df_feat = df.dropna(subset=features).copy()

cat_cols = ["Sector", "Sub_Sector", "city", "state"]
num_cols = [c for c in features if c not in cat_cols]

preprocess = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", "passthrough", num_cols),
    ],
    remainder="drop",
)

# =========================================================
# 1) Funding Round Prediction (Classification)
#    Target: raised_again_12m (0/1)
# =========================================================
df_cls = df_feat[df_feat["raised_again_12m"].notna()].copy()
X1 = df_cls[features]
y1 = df_cls["raised_again_12m"].astype(int)

clf_pipeline = Pipeline(
    steps=[
        ("prep", preprocess),
        ("clf", XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1
        )),
    ]
)

clf_pipeline.fit(X1, y1)

with open(os.path.join(MODEL_DIR, "funding_round_model.pkl"), "wb") as f:
    pickle.dump(clf_pipeline, f)

print(f"✅ Saved: {os.path.join(MODEL_DIR, 'funding_round_model.pkl')}  |  rows: {len(df_cls)}")

# =========================================================
# 2) Funding Amount Prediction (Regression)
#    Target: amount_next_round (Cr)
# =========================================================
df_reg = df_feat[df_feat["amount_next_round"].notna()].copy()
X2 = df_reg[features]
y2 = df_reg["amount_next_round"].astype(float)

reg_pipeline = Pipeline(
    steps=[
        ("prep", preprocess),
        ("reg", XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1
        )),
    ]
)

reg_pipeline.fit(X2, y2)

with open(os.path.join(MODEL_DIR, "funding_amount_model.pkl"), "wb") as f:
    pickle.dump(reg_pipeline, f)

print(f"✅ Saved: {os.path.join(MODEL_DIR, 'funding_amount_model.pkl')}  |  rows: {len(df_reg)}")

# =========================================================
# 3) Investment Score / Probability of Success (Classification)
#    Same target as (1): raised_again_12m
# =========================================================
score_pipeline = Pipeline(
    steps=[
        ("prep", preprocess),
        ("clf", XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1
        )),
    ]
)

score_pipeline.fit(X1, y1)

with open(os.path.join(MODEL_DIR, "invest_score_model.pkl"), "wb") as f:
    pickle.dump(score_pipeline, f)

print(f"✅ Saved: {os.path.join(MODEL_DIR, 'invest_score_model.pkl')}  |  rows: {len(df_cls)}")

print("\nAll models trained and saved successfully.")
