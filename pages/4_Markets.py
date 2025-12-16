import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helper import (
    section_header,
    kpi_cards,
    format_inr_cr,
)
from utils.load_data import list_unique_values
from utils.db import log_activity  # Added for activity tracking
from utils.sidebar import render_sidebar  # New: For shared sidebar

# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------
st.set_page_config(layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("❌ You must log in to access this page.")
    st.stop()

# Render shared sidebar
render_sidebar(st.session_state.user_email, st.session_state.user_id)

section_header(
    "🌍 Market Intelligence",
    "Analyze funding momentum across (Headquarters × Sector)."
)


# -------------------------
# LOAD DATA
# -------------------------
data = st.session_state.DATA
df_market = data["market"]      # market_signals_summary_fixed.csv
df_enh    = data["enhanced"]


# -------------------------------------------------
# FILTERS
# -------------------------------------------------
col1, col2 = st.columns(2)

cities = ["All"] + list_unique_values(df_market, "Headquarters")
city_sel = col1.selectbox("Select Headquarters", cities)

sectors = ["All"] + list_unique_values(df_market, "Sector")
sector_sel = col2.selectbox("Select Sector", sectors)


# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
df_view = df_market.copy()

if city_sel != "All":
    df_view = df_view[df_view["Headquarters"] == city_sel]

if sector_sel != "All":
    df_view = df_view[df_view["Sector"] == sector_sel]


# -------------------------------------------------
# LOG ACTIVITY (Added: Track filter selections for personalization)
# -------------------------------------------------
if "user_id" in st.session_state and st.session_state.get("logged_in", False):
    if city_sel != "All":
        metadata = {"sector_filter": sector_sel if sector_sel != "All" else None}
        log_activity(
            user_id=st.session_state.user_id,
            action_type="filter_geography",
            target=city_sel,
            page="4_Markets.py",
            session_id=st.session_state.get("session_id"),
            metadata=metadata
        )
    if sector_sel != "All":
        metadata = {"city_filter": city_sel if city_sel != "All" else None}
        log_activity(
            user_id=st.session_state.user_id,
            action_type="filter_sector",
            target=sector_sel,
            page="4_Markets.py",
            session_id=st.session_state.get("session_id"),
            metadata=metadata
        )


# -------------------------------------------------
# KPIs (aggregated view)
# -------------------------------------------------
total_funding = df_view["Total_Funding"].sum()
total_rounds  = int(df_view["Total_Rounds"].sum())

avg_6m = df_view["Avg_6m_Funding"].mean()
avg_12m = df_view["Avg_12m_Funding"].mean()

kpi_cards({
    "Total Funding": format_inr_cr(total_funding),
    "Total Rounds": f"{total_rounds:,}",      # ✅ FIXED
    "Avg 6m Funding": format_inr_cr(avg_6m),
    "Avg 12m Funding": format_inr_cr(avg_12m),
})


# -------------------------------------------------
# TOP MARKETS TABLE
# -------------------------------------------------
st.subheader("Top Markets (HQ × Sector)")

cols = [
    "Headquarters", "Sector",
    "Avg_6m_Funding", "Avg_12m_Funding",
    "Total_Funding", "Total_Rounds"
]

df_top = (
    df_view[cols]
    .sort_values("Total_Funding", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(df_top, use_container_width=True, height=400)


# -------------------------------------------------
# HEATMAP — SECTOR FUNDING
# -------------------------------------------------
st.subheader("Sector Funding Heatmap")

if len(df_view):
    df_pivot = df_view.pivot_table(
        index="Headquarters",
        columns="Sector",
        values="Total_Funding",
        aggfunc="sum",
        fill_value=0
    )

    if not df_pivot.empty:
        fig = px.imshow(
            df_pivot,
            aspect="auto",
            title="Funding Heatmap (Cr)",
            labels=dict(color="Funding Cr")
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected filters.")


# -------------------------------------------------
# BUBBLE — MARKET MOMENTUM
# -------------------------------------------------
st.subheader("Momentum Map")

df_view["Momentum"] = df_view["Avg_6m_Funding"] - df_view["Avg_12m_Funding"]

if len(df_view):
    fig = px.scatter(
        df_view,
        x="Avg_12m_Funding",
        y="Avg_6m_Funding",
        size="Total_Funding",
        color="Momentum",
        hover_name="Headquarters",
        hover_data=["Sector"],
        title="Market Momentum (6m vs 12m)",
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data to display.")


# -------------------------------------------------
# BAR — TOP CITIES
# -------------------------------------------------
st.subheader("Top Cities (by Total Funding)")

df_city = (
    df_market.groupby("Headquarters", as_index=False)["Total_Funding"]
    .sum()
    .sort_values("Total_Funding", ascending=False)
    .head(15)
)

if len(df_city):
    fig = px.bar(
        df_city,
        x="Headquarters",
        y="Total_Funding",
        title="Top Cities — Total Funding",
    )
    fig.update_layout(height=450, xaxis_tickangle=30)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No city data available.")