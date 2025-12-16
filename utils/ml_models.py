import os
import pickle
import pandas as pd
import numpy as np

MODEL_DIR = "models"


# -----------------------------------------------------
# SAFE LOAD
# -----------------------------------------------------
def load_pickle(path: str):
    """Safe pickle load with graceful failure."""
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except:
        return None


# -----------------------------------------------------
# LOAD TRAINED MODELS
# -----------------------------------------------------
funding_round_model = load_pickle(os.path.join(MODEL_DIR, "funding_round_model.pkl"))
funding_amount_model = load_pickle(os.path.join(MODEL_DIR, "funding_amount_model.pkl"))
invest_score_model = load_pickle(os.path.join(MODEL_DIR, "invest_score_model.pkl"))


# -----------------------------------------------------
# REQUIRED MODEL FEATURES
# -----------------------------------------------------
FEATURES = [
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


# -----------------------------------------------------
# CLEAN INPUT FORMATTER
# -----------------------------------------------------
def clean_input(df_row: pd.Series) -> pd.DataFrame:
    """
    Takes a single company deal row and returns the formatted model input DataFrame.
    Ensures missing numeric values default to 0; categorical to "Unknown".
    """
    d = {}

    for col in FEATURES:
        val = df_row.get(col, np.nan)

        if isinstance(val, (float, int)) or pd.isna(val):
            # numeric
            d[col] = 0.0 if pd.isna(val) else float(val)
        else:
            # strings
            d[col] = str(val)

    return pd.DataFrame([d])


# -----------------------------------------------------
# ✅ MODEL 1 — Will a company raise again within 12 months?
# -----------------------------------------------------
def predict_will_raise(df_row: pd.Series):
    """
    Returns probability + decision for: Will the company raise again within 12 months?
    """
    if funding_round_model is None:
        return None, "Model not loaded"

    X = clean_input(df_row)

    prob = funding_round_model.predict_proba(X)[0][1]   # positive class
    label = int(prob >= 0.5)

    return prob, label


# -----------------------------------------------------
# ✅ MODEL 2 — What might be the funding amount next round?
# -----------------------------------------------------
def predict_next_amount(df_row: pd.Series):
    """
    Returns predicted next round funding amount in crores.
    If model not available → returns None
    """
    if funding_amount_model is None:
        return None

    X = clean_input(df_row)
    pred = funding_amount_model.predict(X)[0]
    return float(pred)


# -----------------------------------------------------
# ✅ MODEL 3 — Investment Success Score
#     (same target as Model 1)
# -----------------------------------------------------
def score_investment(df_row: pd.Series):
    """
    Returns a score 0–1 representing success likelihood.
    """
    if invest_score_model is None:
        return None

    X = clean_input(df_row)
    prob = invest_score_model.predict_proba(X)[0][1]
    return float(prob)


# -----------------------------------------------------
# BATCH WRAPPERS
# -----------------------------------------------------
def batch_predict_raise(df: pd.DataFrame):
    """Returns probability to raise again for all rows."""
    out = []
    for _, r in df.iterrows():
        p, _ = predict_will_raise(r)
        out.append(p)
    return out


def batch_predict_amount(df: pd.DataFrame):
    """Returns predicted next amount for all rows."""
    out = []
    for _, r in df.iterrows():
        val = predict_next_amount(r)
        out.append(val)
    return out


def batch_score(df: pd.DataFrame):
    """Returns score for all rows."""
    out = []
    for _, r in df.iterrows():
        val = score_investment(r)
        out.append(val)
    return out
