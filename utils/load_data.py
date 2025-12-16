import pandas as pd
import os

# -------------------------------------------------
# LOCATIONS
# -------------------------------------------------
DATA_DIR = "data"

FILES = {
    "raw": "final_cleaned_dataset_2.csv",
    "enhanced": "df_enhanced_fixed.csv",
    "company": "company_enhanced_fixed.csv",
    "investor": "investor_enhanced_fixed.csv",
    "market": "market_signals_summary_fixed.csv",
}


# -------------------------------------------------
# LOAD ALL DATA
# -------------------------------------------------
def load_all_data():
    """
    Loads all datasets into a single dict.
    Returns:
        {
            "raw": df_raw,
            "enhanced": df_enh,
            "company": df_company,
            "investor": df_investor,
            "market": df_market
        }
    """
    data = {}

    for key, filename in FILES.items():
        path = os.path.join(DATA_DIR, filename)

        try:
            df = pd.read_csv(path)

            # Try to parse Date where available
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # Remove trailing spaces, normalize col names
            df.columns = df.columns.str.strip()

            data[key] = df

        except Exception as e:
            print(f"[ERROR] Could not load {filename}: {e}")
            data[key] = pd.DataFrame()

    return data


# -------------------------------------------------
# Helper: Unique values list
# -------------------------------------------------
def list_unique_values(df, col):
    """Return sorted list of non-null unique values from a column."""
    if col not in df.columns:
        return []
    return sorted(df[col].dropna().unique().tolist())
