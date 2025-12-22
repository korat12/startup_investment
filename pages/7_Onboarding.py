import streamlit as st
import json  # If you need JSON handling later

from pydantic import ValidationError

from utils.db import run_query, get_user_profile, save_preferences
from utils.helper import section_header
from utils.load_data import list_unique_values

from utils.schemas import PreferencesSchema


st.set_page_config(layout="wide")

# -------------------------------------------------
# ACCESS GUARD: allow logged-in OR onboarding flow
# -------------------------------------------------
if not (
    st.session_state.get("logged_in", False)
    or st.session_state.get("auth_step") == "onboarding"
):
    st.error("Open the app and login/signup to continue.")
    st.switch_page("app.py")
    st.stop()

# Still require user_email to know which user
if "user_email" not in st.session_state or not st.session_state.user_email:
    st.error("Open the app and login/signup to continue.")
    st.switch_page("app.py")
    st.stop()

user_email = st.session_state.user_email

# -------------------------------------------------
# UI HEADER
# -------------------------------------------------
section_header(
    "📝 Onboarding",
    "Tell us about your interests so we can personalize your experience."
)

# Access shared data
data = st.session_state.DATA
df_company = data["company"]

# Load profile from DB
profile = get_user_profile(user_email) or {}

# -------------------------------------------------
# BASIC DETAILS
# -------------------------------------------------
st.subheader("👤 Basic Details")

role_options = ["Founder", "Investor", "Student", "Analyst", "Other"]

name = st.text_input("Your Name *", value=profile.get("name") or "")

# Determine role index
default_role = profile.get("role")
role_index = role_options.index(default_role) if default_role in role_options else 0
role = st.selectbox("Your Role *", role_options, index=role_index)

# -------------------------------------------------
# PREFERENCES
# -------------------------------------------------
st.markdown("---")
st.subheader("🎯 Investment / Interest Preferences")

sectors = list_unique_values(df_company, "Sub_Sector")
pref_sectors = st.multiselect("Preferred Sub-Sectors *", sectors)

stages = ["Seed", "Pre-Seed", "Series A", "Series B", "Series C", "Growth", "Late"]
pref_stages = st.multiselect("Preferred Funding Stages *", stages)

geos = list_unique_values(df_company, "Country")
pref_geo = st.multiselect("Preferred Geography Countries *", geos)

risk_opts = ["Low", "Medium", "High"]
risk = st.selectbox("Risk Preference *", risk_opts, index=1)

invest_size_opts = ["< 100 Cr", "100–300 Cr", "300–1000 Cr", "> 1000 Cr"]
invest_size = st.selectbox("Funding Comfort Size *", invest_size_opts, index=1)

# -------------------------------------------------
# EXTRA QUESTIONS
# -------------------------------------------------
st.markdown("### Your Investment Goals")
goals = st.text_area(
    "What are your main goals? (e.g., 'Scale in AI startups')",
    placeholder="Tell us briefly...",
    max_chars=200,
)

st.markdown("### Budget & Experience")
col1, col2 = st.columns(2)
budget_opts = ["1-10", "10-50", "50-100", "100+"]
budget = col1.multiselect("Budget Ranges (Cr)", budget_opts, default=[])
experience = col2.radio("Experience Level", ["Beginner", "Intermediate", "Expert"])

st.markdown("### Preferred Insights")
insights_pref = st.multiselect(
    "What content do you want?",
    ["Deal Alerts", "Sector Trends", "Investor Matches", "Forecasts"],
    default=["Deal Alerts"],
)

st.markdown("---")

# -------------------------------------------------
# BASIC UI VALIDATION (UNCHANGED)
# -------------------------------------------------
required_ok = all(
    [
        name.strip(),
        role.strip(),
        len(pref_sectors) > 0,
        len(pref_stages) > 0,
        len(pref_geo) > 0,
        risk in risk_opts,
        invest_size in invest_size_opts,
    ]
)

# -------------------------------------------------
# ACTION BUTTONS
# -------------------------------------------------
c1, c2 = st.columns([1, 1])

with c1:
    if st.button("✅ Complete", disabled=not required_ok):
        try:
            # ✅ Pydantic validation (NEW – does NOT change flow)
            prefs = PreferencesSchema(
                sectors=pref_sectors,
                stages=pref_stages,
                geography=pref_geo,
                risk_level=risk,
                investment_size=invest_size,
            )

            # Save name/role in users table (UNCHANGED)
            run_query(
                "UPDATE users SET name=%s, role=%s WHERE email=%s",
                (name, role, user_email),
            )

            # Upsert preferences (UNCHANGED)
            save_preferences(
                profile["id"],
                prefs.sectors,
                prefs.stages,
                prefs.geography,
                prefs.risk_level,
                prefs.investment_size,
                goals=goals,
                budget=budget,
                experience=experience,
                insights_pref=insights_pref,
            )

            # Flow unchanged
            st.success("✅ Onboarding completed. Please login now.")
            st.session_state.logged_in = False
            st.session_state.auth_step = "login"
            st.session_state.user_email = None
            st.switch_page("app.py")

        except ValidationError as e:
            # Clean error from schema
            st.error(e.errors()[0]["msg"])

        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"Error saving preferences: {e}")

with c2:
    if st.button("Why can't I complete?"):
        if required_ok:
            st.info("All good. Click ‘Complete’.")
        else:
            st.error("Fill all required fields (*) to enable the Complete button.")
