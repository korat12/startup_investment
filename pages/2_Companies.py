import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helper import (
    section_header,
    kpi_cards,
    format_inr_cr,
)
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

# -------------------------------------------------
# LOAD FROM SESSION STATE
# -------------------------------------------------
if "DATA" not in st.session_state:
    st.error("❌ DATA not initialized. Please run from app.py")
    st.stop()

data = st.session_state.DATA
df_company = data["company"]
df_enh = data["enhanced"]

# -------------------------------------------------
# PAGE HEADER
# -------------------------------------------------
section_header(
    "🏢 Company Explorer",
    "Funding summary, investors, and similar peers"
)

# -------------------------------------------------
# SELECT COMPANY
# -------------------------------------------------
companies = ["Select"] + sorted(df_company["Company_Cleaned"].dropna().unique())
selected_company = st.selectbox("Select Company", companies)

if selected_company == "Select":
    st.stop()

rec = df_company[df_company["Company_Cleaned"] == selected_company].iloc[0]

# Updated: Log activity after selection
if "user_id" in st.session_state:
    from utils.db import log_activity
    df_deals = df_enh[df_enh["Company_Cleaned"] == selected_company]  # Compute here for metadata
    metadata = {"rounds_viewed": len(df_deals)}
    log_activity(
        user_id=st.session_state.user_id,
        action_type="view_company",
        target=selected_company,
        page="2_Companies.py",
        session_id=st.session_state.get("session_id"),
        metadata=metadata
    )

# -------------------------------------------------
# KPI CARDS
# -------------------------------------------------
kpi_cards({
    "Total Funding": format_inr_cr(rec.get("Total_Funding", 0)),
    "Max Round": format_inr_cr(rec.get("Max_Funding", 0)),
    "Num Rounds": rec.get("Num_Rounds", 0),
    "Last Year": rec.get("Last_Year", "-"),
})

# -------------------------------------------------
# BASIC DETAILS
# -------------------------------------------------
st.subheader("📌 Company Details")

c1, c2 = st.columns(2)

c1.write(f"**Headquarters:** {rec.get('Headquarters', '-')}")
c1.write(f"**City:** {rec.get('City', '-')}")
c1.write(f"**State:** {rec.get('State', '-')}")
c1.write(f"**Country:** {rec.get('Country', '-')}")

c2.write(f"**Primary Sector:** {rec.get('Sector', '-')}")
c2.write(f"**Sub-Sector:** {rec.get('Sub_Sector', '-')}")
c2.write(f"**First Year:** {rec.get('First_Year', '-')}")
c2.write(f"**Last Year:** {rec.get('Last_Year', '-')}")

# -------------------------------------------------
# FUNDING TREND
# -------------------------------------------------
st.markdown("---")
st.subheader("📈 Funding Over Time")

df_deals = df_enh[df_enh["Company_Cleaned"] == selected_company]

if len(df_deals):
    df_time = (
        df_deals.groupby("Date", as_index=False)["Amount_Cr"]
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
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No funding history available.")

# -------------------------------------------------
# LEAD INVESTORS — CLEAN FORMAT
# -------------------------------------------------
st.markdown("---")
st.subheader("👥 Lead Investors")

if isinstance(rec.get("Investors"), str) and rec.get("Investors").strip():
    raw = rec["Investors"].split(",")
    investors = sorted({i.strip() for i in raw if i.strip()})

    # CLEAN INVESTOR LIST
    clean = []
    for x in investors:
        if len(x) > 2 and "unknown" not in x.lower():
            clean.append(x)
    clean = sorted(set(clean))

    max_show = 25
    show_items = clean[:max_show]

    st.write("\n".join([f"- {i}" for i in show_items]))

    if len(clean) > max_show:
        st.caption(f"... and {len(clean) - max_show} more")
else:
    st.info("No investor data available.")

# -------------------------------------------------
# SIMILAR COMPANIES — FIXED
# -------------------------------------------------
st.markdown("---")
st.subheader("🔎 Similar Companies")

sub_sec = rec.get("Sub_Sector", None)

df_sim = df_company[
    (df_company["Sub_Sector"] == sub_sec)
    & (df_company["Company_Cleaned"] != selected_company)
].sort_values("Total_Funding", ascending=False).head(10)

# **Fix missing values**
df_display = df_sim.copy()
df_display["City"]    = df_display["City"].fillna(df_display["Headquarters"])
df_display["State"]   = df_display["State"].fillna("-")
df_display["Country"] = df_display["Country"].fillna("-")

cols = [
    "Company_Cleaned",
    "Total_Funding",
    "Num_Rounds",
    "Sub_Sector",
    "City",
    "State",
    "Country",
]

if df_display.empty:
    st.info("No similar companies found.")
else:
    st.dataframe(df_display[cols], use_container_width=True, height=350)