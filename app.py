# app.py
import streamlit as st
import uuid  # For session_id
import pymysql

from pydantic import ValidationError

from utils.load_data import load_all_data
from utils.helper import section_header
from utils.auth import signup_user, check_credentials
from utils.db import get_user_profile, has_preferences
from utils.sidebar import render_sidebar

from utils.schemas import SignupSchema, LoginSchema


st.set_page_config(page_title="Startup & Investor Intelligence Platform", layout="wide")

# -------- Load datasets once --------
if "DATA" not in st.session_state:
    with st.spinner("Loading datasets..."):
        st.session_state.DATA = load_all_data()

# -------- Create DB connection once --------
if "DB_CONN" not in st.session_state:
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="12082004",
            database="startup_app",
            port=3306,
            connect_timeout=10,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
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
    st.session_state.auth_step = "login"  # login | signup | onboarding


# =========================================================
# SIGNUP
# =========================================================
if st.session_state.auth_step == "signup":
    section_header("🆕 Create your account", "Sign up to get started")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Full Name (required)")
    role = st.selectbox(
        "Your Role",
        ["Founder", "Investor", "Student", "Analyst", "Other"],
        index=0,
    )

    c1, c2 = st.columns(2)

    if c1.button("Create account"):
        try:
            # ✅ Pydantic validation
            data = SignupSchema(
                email=email,
                password=password,
                name=name,
                role=role,
            )

            signup_user(
                email=data.email,
                password=data.password,
                role=data.role,
                name=data.name,
            )

            # Go straight to onboarding
            st.session_state.user_email = data.email
            st.session_state.logged_in = False
            st.session_state.auth_step = "onboarding"
            st.success("Account created. Next: personalize your experience.")
            st.rerun()

        except ValidationError as e:
            # Clean validation error for UI
            st.error(e.errors()[0]["msg"])

        except ValueError as e:
            # Known business case (duplicate email, validation, etc.)
            st.warning(str(e))
            st.info("You can login using your existing account.")

        except Exception as e:
            # Unexpected system error
            import traceback

            traceback.print_exc()
            st.error("Something went wrong while creating your account. Please try again.")

    if c2.button("← Back to Login"):
        st.session_state.auth_step = "login"
        st.rerun()

    st.stop()


# =========================================================
# ONBOARDING REDIRECT
# =========================================================
elif st.session_state.auth_step == "onboarding":
    st.switch_page("pages/7_Onboarding.py")
    st.stop()


# =========================================================
# LOGIN
# =========================================================
else:
    section_header("🔐 Login", "Sign in to access insights")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    c1, c2 = st.columns(2)

    if c1.button("Login"):
        try:
            # ✅ Pydantic validation
            data = LoginSchema(email=email, password=password)

            if st.session_state.get("DB_CONN") is None:
                st.error("Database connection is not available.")

            elif check_credentials(data.email, data.password):
                prof = get_user_profile(data.email)

                # Force onboarding if preferences missing
                if prof and not has_preferences(prof["id"]):
                    st.session_state.user_email = data.email
                    st.session_state.logged_in = False
                    st.session_state.auth_step = "onboarding"
                    st.info("Complete onboarding to continue.")
                    st.rerun()

                st.session_state.logged_in = True
                st.session_state.user_email = data.email
                st.session_state.user_id = prof["id"]
                st.session_state.session_id = str(uuid.uuid4())

                st.success("✅ Login successful!")

                # Render sidebar briefly (unchanged behavior)
                render_sidebar(st.session_state.user_email, st.session_state.user_id)

                st.switch_page("pages/1_Overview.py")

            else:
                st.error("❌ Invalid email / password")

        except ValidationError:
            st.error("Please enter a valid email and password")

        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"Internal error during login: {e}")

    if c2.button("Sign Up"):
        st.session_state.auth_step = "signup"
        st.rerun()

    # Home text
    section_header(
        "🚀 Startup & Investor Intelligence Platform",
        "Analyze Funding, Companies, Investors, Markets & Forecasts",
    )
