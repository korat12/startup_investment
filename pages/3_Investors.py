import streamlit as st
import pandas as pd
import plotly.express as px
from utils.sidebar import render_sidebar  # New: Import shared sidebar

from utils.helper import (
    section_header,
    kpi_cards,
    format_inr_cr,
)
from utils.load_data import list_unique_values
from utils.db import log_activity  # Added for activity logging


# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------
st.set_page_config(layout="wide")

# -------------------------------------------------
# LOGIN CHECK & SIDEBAR
# -------------------------------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("❌ You must log in to access this page.")
    st.stop()

# Render shared sidebar
render_sidebar(st.session_state.user_email, st.session_state.user_id)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
if "DATA" not in st.session_state:
    st.error("❌ DATA not initialized. Please run from app.py")
    st.stop()

data = st.session_state.DATA
df_investor = data["investor"]
df_enh = data["enhanced"]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
section_header(
    "💰 Investor Explorer",
    "Behavior, sector focus, investment style & portfolio insights"
)


# -------------------------------------------------
# FILTERS
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

sector_sel = col1.selectbox(
    "Filter by Sub-Sector",
    ["All"] + list_unique_values(df_investor, "Top_Sub_Sectors")
)

city_sel = col2.selectbox(
    "Filter by City",
    ["All"] + list_unique_values(df_investor, "Top_Cities")
)

stage_sel = col3.selectbox(
    "Filter by Stage",
    ["All"] + list_unique_values(df_investor, "Top_Stages")
)


df_view = df_investor.copy()


def match_any(cell, value):
    if value == "All":
        return True
    if not isinstance(cell, str):
        return False
    return value.lower() in cell.lower()


if sector_sel != "All":
    df_view = df_view[df_view["Top_Sub_Sectors"].apply(lambda x: match_any(x, sector_sel))]

if city_sel != "All":
    df_view = df_view[df_view["Top_Cities"].apply(lambda x: match_any(x, city_sel))]

if stage_sel != "All":
    df_view = df_view[df_view["Top_Stages"].apply(lambda x: match_any(x, stage_sel))]

# Added: Log filter activity if user logged in
if "user_id" in st.session_state:
    session_id = st.session_state.get("session_id")
    if sector_sel != "All":
        metadata = {"city_filter": city_sel if city_sel != "All" else None, "stage_filter": stage_sel if stage_sel != "All" else None}
        log_activity(st.session_state.user_id, "filter_sector", sector_sel, "3_Investors.py", session_id, metadata)
    if city_sel != "All":
        metadata = {"sector_filter": sector_sel if sector_sel != "All" else None, "stage_filter": stage_sel if stage_sel != "All" else None}
        log_activity(st.session_state.user_id, "filter_geography", city_sel, "3_Investors.py", session_id, metadata)
    if stage_sel != "All":
        metadata = {"sector_filter": sector_sel if sector_sel != "All" else None, "city_filter": city_sel if city_sel != "All" else None}
        log_activity(st.session_state.user_id, "filter_stage", stage_sel, "3_Investors.py", session_id, metadata)


# -------------------------------------------------
# TABLE VIEW
# -------------------------------------------------
st.subheader("Investor List")

cols_show = [
    "Investor",
    "Total_Invested",
    "Num_Investments",
    "Top_Sub_Sectors",
    "Top_Stages",
    "Top_Cities",
    "Last_Date",
    "Last_Investment",
]

# ✅ Keep only those columns that really exist
cols_available = [c for c in cols_show if c in df_view.columns]
df_show = df_view[cols_available].sort_values("Num_Investments", ascending=False)

st.dataframe(df_show, use_container_width=True, height=400)
st.caption(f"{df_show.shape[0]} investors found.")


# -------------------------------------------------
# INVESTOR PROFILE
# -------------------------------------------------
st.markdown("---")
st.subheader("🔍 Investor Profile")

inv_list = ["None"] + sorted(df_view["Investor"].unique().tolist())
selected = st.selectbox("Select Investor", inv_list)

# Added: Log investor view if selected and user logged in
if selected != "None" and "user_id" in st.session_state:
    session_id = st.session_state.get("session_id")
    metadata = {"num_deals_viewed": len(df_enh[df_enh["Lead_Investors"].str.contains(selected, case=False, na=False)])}
    log_activity(st.session_state.user_id, "view_investor", selected, "3_Investors.py", session_id, metadata)

if selected != "None":
    info = df_investor[df_investor["Investor"] == selected].iloc[0]

    kpi_cards({
        "Total Invested": format_inr_cr(info["Total_Invested"]),
        "Portfolio Size": info["Num_Investments"],
    })

    # Deals from df_enh
    df_deals = df_enh[
        df_enh["Lead_Investors"].str.contains(selected, case=False, na=False)
    ]

    # -------------------------------------------------
    # SECTOR ALLOCATION
    # -------------------------------------------------
    st.markdown("### 🔹 Sector Allocation")
    if len(df_deals):
        df_sec = (
            df_deals.groupby("Sector", as_index=False)["Amount_Cr"]
            .sum()
            .sort_values("Amount_Cr", ascending=False)
        )
        fig = px.bar(df_sec, x="Sector", y="Amount_Cr", title="Funding by Sector")
        fig.update_layout(height=350, xaxis_tickangle=25)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No deal data available.")

    # -------------------------------------------------
    # PORTFOLIO COMPANIES
    # -------------------------------------------------
    st.markdown("### 🔹 Portfolio Companies")
    if len(df_deals):
        df_port = (
            df_deals.groupby("Company_Cleaned", as_index=False)["Amount_Cr"]
            .sum()
            .rename(columns={"Amount_Cr": "Total_Invested_Cr"})
            .sort_values("Total_Invested_Cr", ascending=False)
        )
        st.dataframe(df_port.head(25), use_container_width=True, height=300)
    else:
        st.info("No portfolio data.")

    # -------------------------------------------------
    # CO-INVESTORS
    # -------------------------------------------------
    st.markdown("### 🔹 Co-Investors")
    if len(df_deals):
        co = (
            df_deals["Lead_Investors"]
            .dropna()
            .str.split(", ")
            .explode()
            .str.strip()
            .dropna()
            .unique()
            .tolist()
        )

        co = [x for x in co if x.lower() != selected.lower()]

        if co:
            co_sorted = sorted(co)
            max_display = 30
            st.write("\n".join([f"- {x}" for x in co_sorted[:max_display]]))
            if len(co_sorted) > max_display:
                st.caption(f"... and {len(co_sorted) - max_display} more")
        else:
            st.info("No co-investors found.")
    else:
        st.info("No co-investor data.")