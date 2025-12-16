import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helper import section_header, kpi_cards, format_inr_cr
from utils.load_data import list_unique_values
from utils.sidebar import render_sidebar  # New: Import shared sidebar

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
    "📊 Overview Dashboard",
    "High-level funding insights across companies, investors & sectors."
)

# Load from session
if "DATA" not in st.session_state:
    st.error("❌ DATA not initialized. Please run from app.py")
    st.stop()

data = st.session_state.DATA

df_raw      = data["raw"]
df_enh      = data["enhanced"]
df_company  = data["company"]
df_investor = data["investor"]
df_market   = data["market"]

# -------------------------------------------------
# KPI METRICS
# -------------------------------------------------
total_funding = df_enh["Amount_Cr"].sum()
num_deals     = len(df_enh)
num_companies = df_company["Company_Cleaned"].nunique()
num_investors = df_investor["Investor"].nunique()

kpi_cards({
    "Total Funding": format_inr_cr(total_funding),
    "Total Deals": num_deals,       # ✅ FIXED (Don't format as INR)
    "Companies": num_companies,
    "Investors": num_investors
})

# -------------------------------------------------
# FUNDING OVER TIME
# -------------------------------------------------
st.subheader("📈 Funding Trend Over Time")

df_time = (
    df_enh.groupby("Date", as_index=False)["Amount_Cr"]
    .sum()
    .sort_values("Date")
)

if len(df_time):
    fig = px.line(
        df_time,
        x="Date",
        y="Amount_Cr",
        markers=True,
        title="Funding Amount Over Time",
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No date data available to display trend.")

# -------------------------------------------------
# TOP SECTORS
# -------------------------------------------------
st.subheader("🏆 Top Sectors by Total Funding")

df_sector = (
    df_enh.groupby("Sector", as_index=False)["Amount_Cr"]
    .sum()
    .sort_values("Amount_Cr", ascending=False)
    .head(15)
)

if len(df_sector):
    fig = px.bar(
        df_sector,
        x="Sector",
        y="Amount_Cr",
        title="Top 15 Sectors",
    )
    fig.update_layout(height=450, xaxis_tickangle=40)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# TOP FUNDED COMPANIES
# -------------------------------------------------
st.subheader("🏢 Top Funded Companies")

df_top_companies = (
    df_company[["Company_Cleaned", "Total_Funding", "Num_Rounds", "Last_Year"]]
    .sort_values("Total_Funding", ascending=False)
    .head(20)
)

st.dataframe(
    df_top_companies,
    use_container_width=True,
    height=450
)

# -------------------------------------------------
# TOP INVESTORS
# -------------------------------------------------
st.subheader("💰 Top Investors by Number of Investments")

df_top_inv = (
    df_investor[["Investor", "Num_Investments"]]
    .sort_values("Num_Investments", ascending=False)
    .head(20)
)

st.dataframe(
    df_top_inv,
    use_container_width=True,
    height=350
)

st.info("Navigate to left sidebar pages for deeper analysis.")