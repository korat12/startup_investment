# app.py
import streamlit as st
import uuid  # For session_id
import pymysql

from utils.load_data import load_all_data
from utils.helper import section_header
from utils.auth import signup_user, check_credentials
from utils.db import get_user_profile, has_preferences
from utils.sidebar import render_sidebar  # New: Import shared sidebar

st.set_page_config(page_title="Startup & Investor Intelligence Platform", layout="wide")

# -------- Load datasets once --------
if "DATA" not in st.session_state:
    with st.spinner("Loading datasets..."):
        st.session_state.DATA = load_all_data()

# -------- Create DB connection once (so utils.db can use it) --------
if "DB_CONN" not in st.session_state:
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="12082004",
            database="startup_app",   # make sure this DB exists
            port=3306,
            connect_timeout=10,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,  # rows as dicts
        )
        st.session_state.DB_CONN = conn
        print("✅ DB connected via PyMySQL")
    except Exception as e:
        st.session_state.DB_CONN = None
        print("❌ DB connection error:", e)
        st.error(f"Cannot connect to database: {e}")

# -------- Auth state machine --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "login"  # "login" | "signup" | "onboarding"

# -------- UI: step switcher --------
if st.session_state.auth_step == "signup":
    section_header("🆕 Create your account", "Sign up to get started")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Full Name (required)")
    role = st.selectbox("Your Role", ["Founder", "Investor", "Student", "Analyst", "Other"], index=0)

    c1, c2 = st.columns(2)
    if c1.button("Create account"):
        if not (email and password and name):
            st.error("Please fill email, password and name.")
        else:
            try:
                signup_user(email=email, password=password, role=role, name=name)
                # Go straight to onboarding for the just-created user
                st.session_state.user_email = email
                st.session_state.logged_in = False
                st.session_state.auth_step = "onboarding"
                st.success("Account created. Next: personalize your experience.")
                st.rerun()
            except Exception as e:
                import traceback
                traceback.print_exc()
                st.error(f"Error creating account: {e}")

    if c2.button("← Back to Login"):
        st.session_state.auth_step = "login"
        st.rerun()
    st.stop()

elif st.session_state.auth_step == "onboarding":
    # Send them to the onboarding page file
    # IMPORTANT: use the pages/ path
    st.switch_page("pages/7_Onboarding.py")  # this page will send back to login after completion
    st.stop()

else:  # LOGIN
    section_header("🔐 Login", "Sign in to access insights")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    c1, c2 = st.columns(2)
    if c1.button("Login"):
        try:
            if st.session_state.get("DB_CONN") is None:
                st.error("Database connection is not available.")
            elif check_credentials(email, password):
                # If user has no preferences yet, force onboarding even after login
                prof = get_user_profile(email)
                if prof and not has_preferences(prof["id"]):
                    st.session_state.user_email = email
                    st.session_state.logged_in = False
                    st.session_state.auth_step = "onboarding"
                    st.info("Complete onboarding to continue.")
                    st.rerun()

                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_id = prof["id"]  # Set user_id from profile
                st.session_state.session_id = str(uuid.uuid4())  # Generate session_id
                st.success("✅ Login successful!")

                # Optional: Render sidebar briefly before switching (for consistency)
                render_sidebar(st.session_state.user_email, st.session_state.user_id)

                # IMPORTANT: page is under /pages
                st.switch_page("pages/1_Overview.py")
            else:
                st.error("❌ Invalid email / password")
        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"Internal error during login: {e}")

    if c2.button("Sign Up"):
        st.session_state.auth_step = "signup"
        st.rerun()

    # Home text (visible on login screen)
    section_header(
        "🚀 Startup & Investor Intelligence Platform",
        "Analyze Funding, Companies, Investors, Markets & Forecasts",
    )
