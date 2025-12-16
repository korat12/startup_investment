import streamlit as st
import pandas as pd
from utils.sidebar import render_sidebar  # New: Import shared sidebar

from utils.helper import section_header, format_inr_cr
from utils.ml_models import (
    predict_will_raise,
    predict_next_amount,
    score_investment,
)

# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------
st.set_page_config(layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("❌ Please log in to access this page.")
    st.stop()

# Render shared sidebar
render_sidebar(st.session_state.user_email, st.session_state.user_id)

section_header(
    "📈 Startup Funding Forecasting",
    "AI-assisted predictions: Will the company raise again? How much? Success score?"
)

# -------------------------------------------------
# LOAD DATA FROM session_state
# -------------------------------------------------
if "DATA" not in st.session_state:
    st.error("❌ Data not initialized. Please start from app.py")
    st.stop()

data = st.session_state.DATA
df_enh = data["enhanced"]       # df_enhanced_fixed.csv
df_company = data["company"]    # company_enhanced_fixed.csv


# -------------------------------------------------
# USER SELECT COMPANY
# -------------------------------------------------
st.subheader("🔍 Select a Company to Forecast")

companies = ["Select"] + sorted(df_company["Company_Cleaned"].unique())
selected_company = st.selectbox("Choose a company", companies)

if selected_company == "Select":
    st.stop()

df_deals = df_enh[df_enh["Company_Cleaned"] == selected_company].sort_values("Date")

if df_deals.empty:
    st.warning("⚠ No funding records available for this company.")
    st.stop()


# -------------------------------------------------
# USER SELECT DEAL / ROUND
# -------------------------------------------------
st.subheader("📄 Choose a Funding Round")

# options are still the row indices
round_ids = list(df_deals.index)

def format_round(idx):
    r = df_deals.loc[idx]
    return f"{r['Funding_Round_Type']} — {r['Date'].date()}"


round_id = st.selectbox(
    "Select a specific funding event",
    options=round_ids,
    format_func=format_round,
)

row = df_deals.loc[round_id]


# Display summary of that round
st.markdown("### 💡 Selected Round Details")
c1, c2 = st.columns(2)

with c1:
    st.write(f"**Date:** {row['Date']}")
    st.write(f"**Amount (Cr):** {format_inr_cr(row['Amount_Cr'])}")
    st.write(f"**Sector:** {row['Sector']}")
    st.write(f"**Sub-Sector:** {row['Sub_Sector']}")

with c2:
    st.write(f"**City:** {row['city']}")
    st.write(f"**State:** {row['state']}")
    st.write(f"**Funding Round Type:** {row['Funding_Round_Type']}")
    st.write(f"**Cumulative Raised:** {format_inr_cr(row['Cumulative_Funding_Prior'])}")


st.markdown("---")


# -------------------------------------------------
# RUN ALL 3 PREDICTIONS
# -------------------------------------------------
st.subheader("🤖 AI Forecasting Results")

# 1) Will Raise 12m
prob, will_raise = predict_will_raise(row)

# 2) Next amount
next_amt = predict_next_amount(row)

# 3) Investment score
score = score_investment(row)


# -------------------------------------------------
# DISPLAY RESULTS
# -------------------------------------------------
# ✅ Result 1 — Will Raise in 12 Months
st.markdown("### 🔮 Will this company raise funding again within 12 months?")

if prob is None:
    st.info("⚠ Model not available.")
else:
    percent = round(prob * 100, 2)
    if will_raise == 1:
        st.success(f"✅ Likely to raise again — Probability: **{percent}%**")
    else:
        st.error(f"❌ Not likely to raise soon — Probability: **{percent}%**")


# ✅ Result 2 — Estimated Next Funding Amount
st.markdown("### 💰 Estimated Funding Amount (next round)")

if next_amt is None:
    st.info("⚠ Model not available.")
else:
    if next_amt < 0:
        st.warning("Prediction is negative — likely insufficient signals.")
    else:
        st.write(f"📌 **Estimated Amount:** {format_inr_cr(next_amt)}")


# ✅ Result 3 — Investment Success Score
st.markdown("### ⭐ Investment Success Score")

if score is None:
    st.info("⚠ Model not available.")
else:
    score_pct = round(score * 100, 2)
    if score > 0.7:
        st.success(f"Strong Potential — Score: **{score_pct}%**")
    elif score > 0.4:
        st.warning(f"Moderate Potential — Score: **{score_pct}%**")
    else:
        st.error(f"Low Potential — Score: **{score_pct}%**")


# -------------------------------------------------
# FINAL HINT
# -------------------------------------------------
st.markdown("---")
st.caption(
    """
    ✅ These predictions are AI-powered forecasts based on historical activity, funding patterns,
    sector trends & market signals.\n
    """
)