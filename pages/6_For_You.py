import streamlit as st
import pandas as pd
import plotly.express as px
import json

from utils.db import run_query, get_user_profile, log_activity, add_watchlist, remove_watchlist, get_user_insights, submit_feedback, save_preferences
from utils.helper import section_header, format_inr_cr
from utils.load_data import list_unique_values
from utils.sidebar import render_sidebar



# -------------------------------------------------
# PAGE ACCESS CHECK
# -------------------------------------------------
st.set_page_config(layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("❌ You must log in to access this page.")
    st.stop()

# Render shared sidebar
render_sidebar(st.session_state.user_email, st.session_state.user_id)
# -------------------------------------------------
# LOAD USER INFO
# -------------------------------------------------
user_email = st.session_state.user_email
user = get_user_profile(user_email)

section_header(
    "🎯 For You — Personalized Recommendations",
    f"Hi **{user['name'] or user['email']}**, here are insights tailored for you."
)

# -------------------------------------------------
# LOAD DATASETS
# -------------------------------------------------
data = st.session_state.DATA
df_company  = data["company"]
df_enh      = data["enhanced"]
df_investor = data["investor"]
df_market   = data["market"]


# -------------------------------------------------
# FETCH USER PREFERENCES
# -------------------------------------------------
pref_query = """
    SELECT * FROM user_preferences WHERE user_id = %s
"""
prefs = run_query(pref_query, (user["id"],), fetch=True)

if prefs:
    prefs = prefs[0]
else:
    prefs = {}

# Parse JSON fields
user_sectors = json.loads(prefs.get("sectors", "[]"))
user_stages = json.loads(prefs.get("stages", "[]"))
user_geo = json.loads(prefs.get("geography", "[]"))
user_budget = json.loads(prefs.get("budget_ranges", "[]"))
user_goals = prefs.get("investment_goals", "")
user_experience = prefs.get("experience_level", "Intermediate")
user_insights_pref = json.loads(prefs.get("preferred_insights", "[]"))

# Fetch recent activity for interest boosting (last 30 days, top sectors/companies)
activity_query = """
    SELECT action_type, target, COUNT(*) as count
    FROM user_activity 
    WHERE user_id=%s AND timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY action_type, target 
    ORDER BY count DESC LIMIT 10
"""
recent_activity = run_query(activity_query, (user["id"],), fetch=True)
activity_interests = {row["target"]: row["count"] for row in recent_activity if "view" in row["action_type"] or "filter" in row["action_type"]}

# New: Fetch pre-computes
insights = get_user_insights(user["id"])
if insights:
    top_sectors = json.loads(insights.get("top_sectors", "{}"))
    top_companies = json.loads(insights.get("top_companies", "[]"))
    recent_trends = insights.get("recent_trends", "")


# -------------------------------------------------
# UI — UPDATE USER PREFERENCES
# -------------------------------------------------
st.subheader("⚙️ Your Preferences")

# Sectors
sectors = list_unique_values(df_company, "Sub_Sector")
preferred_sectors = st.multiselect(
    "Preferred Sub-Sectors",
    sectors,
    default=user_sectors
)

# Stages
stage_opts = ["Seed", "Pre-Seed", "Series A", "Series B", "Series C", "Growth", "Late"]
preferred_stages = st.multiselect(
    "Preferred Funding Stages",
    stage_opts,
    default=user_stages
)

# Countries
geo_opts = list_unique_values(df_company, "Country")
preferred_geo = st.multiselect(
    "Preferred Markets (Country)",
    geo_opts,
    default=user_geo
)

risk_opts = ["Low", "Medium", "High"]
risk = st.selectbox("Risk Preference", risk_opts, index=risk_opts.index(prefs.get("risk_level", "Medium")))

invest_size_opts = ["< 100 Cr", "100–300 Cr", "300–1000 Cr", "> 1000 Cr"]
invest_size = st.selectbox("Funding Comfort Size", invest_size_opts,
                           index=invest_size_opts.index(prefs.get("investment_size", "100–300 Cr")))

# New fields
st.markdown("### Additional Preferences")
goals = st.text_area("Your Investment Goals", value=user_goals, placeholder="e.g., Scale my portfolio in AI", max_chars=200)
budget_opts = ["1-10", "10-50", "50-100", "100+"]
preferred_budget = st.multiselect("Budget Ranges (Cr)", budget_opts, default=user_budget)
experience_opts = ["Beginner", "Intermediate", "Expert"]
experience = st.radio("Experience Level", experience_opts, index=experience_opts.index(user_experience))
insights_opts = ["Deal Alerts", "Sector Trends", "Investor Matches", "Forecasts"]
preferred_insights = st.multiselect("Preferred Insights", insights_opts, default=user_insights_pref)

# ✅ SAVE
if st.button("💾 Save Preferences"):
    save_preferences(
        user["id"], preferred_sectors, preferred_stages, preferred_geo, risk, invest_size,
        goals=goals, budget=preferred_budget, experience=experience, insights_pref=preferred_insights
    )
    st.success("✅ Preferences Saved!")
    st.rerun()


# -------------------------------------------------
# PERSONALIZED — STARTUP RECOMMENDATIONS
# -------------------------------------------------
st.markdown("---")
st.subheader("🚀 Recommended Startups")

df_like = df_company.copy()

# ✅ Filter by sector
if preferred_sectors:
    df_like = df_like[df_like["Sub_Sector"].isin(preferred_sectors)]

# ✅ Filter by geography
if preferred_geo:
    df_like = df_like[df_like["Country"].isin(preferred_geo)]

# ✅ Simple score (demo — can be upgraded to ML)
df_like["score"] = (
    df_like["Total_Funding"].rank(ascending=False) * 0.6 +
    df_like["Num_Rounds"].rank(ascending=False) * 0.2 +
    df_like["Last_Year"].rank(ascending=False) * 0.2
)

# Updated: Add budget/experience boosts
df_like["score"] += df_like["Total_Funding"].apply(lambda x: 0.5 if any(b in str(x) for b in preferred_budget) else 0)  # Budget match
if experience == "Expert":
    df_like["score"] += df_like["Num_Rounds"] * 0.1  # Favor multi-round companies

# Boost by activity
for target, count in activity_interests.items():
    if "company" in target.lower():
        df_like.loc[df_like["Company_Cleaned"] == target.split("_")[-1], "score"] += count

df_like = df_like.sort_values("score", ascending=False).head(15)

# ✅ WATCHLIST BUTTONS
def render_company_row(row):
    col1, col2 = st.columns([6,1])
    col1.write(f"**{row['Company_Cleaned']}** — {row['Sub_Sector']}")
    col1.caption(f"Funding: {format_inr_cr(row['Total_Funding'])} | Rounds: {row['Num_Rounds']}")

    w = run_query(
        "SELECT id FROM watchlist WHERE user_id=%s AND company=%s",
        (user["id"], row["Company_Cleaned"]),
        fetch=True
    )

    if w:
        if col2.button("⭐ Remove", key=row["Company_Cleaned"]+"_r"):
            remove_watchlist(user["id"], row["Company_Cleaned"])
            st.rerun()
    else:
        if col2.button("+ Watch", key=row["Company_Cleaned"]+"_a"):
            add_watchlist(user["id"], row["Company_Cleaned"])
            log_activity(user["id"], "add_watchlist", row["Company_Cleaned"], "6_For_You.py", st.session_state.get("session_id"))
            st.rerun()


for _, r in df_like.iterrows():
    render_company_row(r)


# -------------------------------------------------
# PERSONALIZED — INVESTOR MATCHES
# -------------------------------------------------
st.markdown("---")
st.subheader("💼 Investors You Might Like")

df_inv_like = df_investor.copy()

if preferred_sectors:
    df_inv_like = df_inv_like[
        df_inv_like["Top_Sub_Sectors"].str.contains("|".join(preferred_sectors), na=False)
    ]

df_inv_like = df_inv_like.sort_values("Num_Investments", ascending=False).head(15)

st.dataframe(
    df_inv_like[["Investor", "Num_Investments", "Top_Sub_Sectors", "Last_Date"]],
    use_container_width=True,
    height=400
)


# -------------------------------------------------
# PERSONALIZED — TRENDING DEALS
# -------------------------------------------------
st.markdown("---")
st.subheader("🔥 Trending Deals for You")

df_deal_like = df_enh.copy()

if preferred_sectors:
    df_deal_like = df_deal_like[df_deal_like["Sub_Sector"].isin(preferred_sectors)]
if preferred_geo:
    df_deal_like = df_deal_like[df_deal_like["country"].isin(preferred_geo)]
if preferred_stages:
    df_deal_like = df_deal_like[df_deal_like["Funding_Round_Type"].isin(preferred_stages)]

# Updated: Filter by budget (example mapping)
budget_min, budget_max = 0, float('inf')
if "1-10" in preferred_budget:
    budget_min, budget_max = 0, 10
elif "10-50" in preferred_budget:
    budget_min, budget_max = 10, 50
# Add more elif as needed
df_deal_like = df_deal_like[(df_deal_like["Amount_Cr"] >= budget_min) & (df_deal_like["Amount_Cr"] <= budget_max)]
df_deal_like = df_deal_like.sort_values("Date", ascending=False).head(5)

st.dataframe(
    df_deal_like[["Company_Cleaned", "Amount_Cr", "Date", "Lead_Investors", "Sub_Sector"]],
    use_container_width=True,
    height=300
)


# -------------------------------------------------
# MARKET HOTSPOTS
# -------------------------------------------------
st.markdown("---")
st.subheader("🔥 Hot Markets to Watch")

df_hot = df_market.sort_values("Avg_6m_Funding", ascending=False).head(10)

fig = px.bar(
    df_hot,
    x="Headquarters",
    y="Avg_6m_Funding",
    title="Top Trending Markets (6-Month Avg Funding)",
)
st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------
# INSIGHTS FROM YOUR PROFILE
# -------------------------------------------------
st.markdown("---")
st.subheader("💡 Insights from Your Profile")
if user_goals:
    st.write(f"**Tailored to your goals:** {user_goals[:100]}...")
if insights and recent_trends:
    st.info(recent_trends)
if user_insights_pref:
    st.caption(f"Showing: {', '.join(user_insights_pref)}")


# -------------------------------------------------
# WATCHLIST VIEW
# -------------------------------------------------
st.markdown("---")
st.subheader("⭐ Your Watchlist")

wl = run_query(
    "SELECT company FROM watchlist WHERE user_id=%s",
    (user["id"],),
    fetch=True
)

if wl:
    df_wl = pd.DataFrame(wl)
    st.dataframe(df_wl, use_container_width=True, height=250)
else:
    st.info("You haven't saved any companies yet.")


# -------------------------------------------------
# FEEDBACK SECTION
# -------------------------------------------------
st.markdown("---")
st.subheader("📝 Quick Feedback")
col1, col2 = st.columns(2)
rating = col1.slider("How useful were these recs?", 1, 5, 3)
comments = col2.text_area("Suggestions?", placeholder="What to improve?")
if st.button("Submit Feedback"):
    submit_feedback(user["id"], "recommendation_rating", "For You page", rating, comments)
    st.success("Thanks! This helps us improve.")


st.caption("Based on your prefs & recent views. Log more actions for better recs!")