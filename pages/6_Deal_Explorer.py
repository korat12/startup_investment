import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helper import section_header, format_inr_cr
from utils.load_data import list_unique_values
from utils.db import log_activity  # Added for activity tracking
from utils.sidebar import render_sidebar  # New: For shared sidebar

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
    "🔎 Deal Explorer",
    "Search and analyze individual funding rounds."
)

# Load data
data = st.session_state.DATA
df_enh = data["enhanced"]

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
st.subheader("Filters")

c1, c2, c3, c4 = st.columns(4)

# Year
years = sorted(df_enh["Year"].dropna().unique().tolist())
year_sel = c1.selectbox("Year", ["All"] + years)

# Sector
sectors = sorted(df_enh["Sector"].dropna().unique().tolist())
sector_sel = c2.selectbox("Sector", ["All"] + sectors)

# Stage
stages = sorted(df_enh["Funding_Round_Type"].dropna().unique().tolist())
stage_sel = c3.selectbox("Round Type", ["All"] + stages)

# City
cities = sorted(df_enh["city"].dropna().unique().tolist())
city_sel = c4.selectbox("City", ["All"] + cities)

# Additional filters
c5, c6 = st.columns(2)

investors = sorted(
    set(
        sum(
            df_enh["Lead_Investors"]
            .fillna("")
            .str.split(", ")
            .tolist(),
            [],
        )
    )
)
investor_sel = c5.selectbox("Investor", ["All"] + investors)

# Amount_Cr range
min_amt = df_enh["Amount_Cr"].min()
max_amt = df_enh["Amount_Cr"].max()
amount_sel = c6.slider("Amount Range (Cr)", min_amt, max_amt, (min_amt, max_amt))

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
df_view = df_enh.copy()

if year_sel != "All":
    df_view = df_view[df_view["Year"] == year_sel]

if sector_sel != "All":
    df_view = df_view[df_view["Sector"] == sector_sel]

if stage_sel != "All":
    df_view = df_view[df_view["Funding_Round_Type"] == stage_sel]

if city_sel != "All":
    df_view = df_view[df_view["city"] == city_sel]

if investor_sel != "All":
    df_view = df_view[df_view["Lead_Investors"].str.contains(investor_sel, case=False, na=False)]

df_view = df_view[
    (df_view["Amount_Cr"] >= amount_sel[0]) &
    (df_view["Amount_Cr"] <= amount_sel[1])
    ]

# -------------------------------------------------
# LOG ACTIVITY FOR FILTERS (New: After filters applied)
# -------------------------------------------------
if "user_id" in st.session_state:
    user_id = st.session_state.user_id
    page_name = "6_Deal_Explorer.py"
    session_id = st.session_state.get("session_id")
    metadata_base = {"year_filter": year_sel, "amount_range": amount_sel}

    if sector_sel != "All":
        log_activity(
            user_id=user_id,
            action_type="filter_sector",
            target=sector_sel,
            page=page_name,
            session_id=session_id,
            metadata={**metadata_base, "stage_filter": stage_sel if stage_sel != "All" else None,
                      "city_filter": city_sel if city_sel != "All" else None}
        )

    if stage_sel != "All":
        log_activity(
            user_id=user_id,
            action_type="filter_stage",
            target=stage_sel,
            page=page_name,
            session_id=session_id,
            metadata={**metadata_base, "sector_filter": sector_sel if sector_sel != "All" else None,
                      "city_filter": city_sel if city_sel != "All" else None}
        )

    if city_sel != "All":
        log_activity(
            user_id=user_id,
            action_type="filter_geography",
            target=city_sel,
            page=page_name,
            session_id=session_id,
            metadata={**metadata_base, "sector_filter": sector_sel if sector_sel != "All" else None,
                      "stage_filter": stage_sel if stage_sel != "All" else None}
        )

    if investor_sel != "All":
        log_activity(
            user_id=user_id,
            action_type="filter_investor",
            target=investor_sel,
            page=page_name,
            session_id=session_id,
            metadata={**metadata_base, "sector_filter": sector_sel if sector_sel != "All" else None,
                      "stage_filter": stage_sel if stage_sel != "All" else None}
        )

# -------------------------------------------------
# RESULTS
# -------------------------------------------------
st.subheader("Results")

cols = [
    "Date", "Company_Cleaned", "Amount_Cr",
    "Funding_Round_Type", "Lead_Investors",
    "Sector", "Sub_Sector", "city", "state", "country"
]

df_show = df_view[cols].sort_values("Date", ascending=False)

st.dataframe(df_show, use_container_width=True, height=450)
st.caption(f"{df_show.shape[0]} deals found.")

# -------------------------------------------------
# FUNDING OVER TIME
# -------------------------------------------------
st.markdown("---")
st.subheader("Funding Over Time")

if len(df_view):
    df_time = (
        df_view.groupby("Date", as_index=False)["Amount_Cr"]
        .sum()
        .sort_values("Date")
    )

    fig = px.line(
        df_time,
        x="Date",
        y="Amount_Cr",
        markers=True,
        title="Funding Trend",
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected filters.")

# -------------------------------------------------
# BUBBLE — AMOUNT vs STAGE
# -------------------------------------------------
st.markdown("---")
st.subheader("Funding Size by Round Type")

if len(df_view):
    df_plot = df_view.copy()
    df_plot["Label"] = df_plot["Company_Cleaned"] + " (" + df_plot["Funding_Round_Type"] + ")"

    fig = px.scatter(
        df_plot,
        x="Funding_Round_Type",
        y="Amount_Cr",
        size="Amount_Cr",
        color="Sector",
        hover_name="Label",
        title="Bubble: Funding Size vs Round Type",
    )
    fig.update_layout(height=500, xaxis_tickangle=30)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for bubble chart.")