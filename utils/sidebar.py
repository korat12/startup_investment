import streamlit as st
from utils.db import has_preferences


def render_sidebar(user_email, user_id):
    """
    Renders persistent sidebar with logout and navigation.
    Call this at the top of each page after login check.
    """
    st.sidebar.title(f"👋 Welcome, {user_email.split('@')[0].title()}!")  # Personalized greeting

    # Logout Button
    if st.sidebar.button("🚪 Logout"):
        # Clear session state for security
        for key in list(st.session_state.keys()):
            if key not in ["DATA"]:  # Preserve data load
                del st.session_state[key]
        st.session_state.logged_in = False  # Reset explicitly
        st.success("Logged out successfully!")
        st.switch_page("app.py")  # Redirect to login page
        # No explicit st.rerun() needed – state change triggers natural rerun

    # Sidebar Navigation
    st.sidebar.markdown("---")  # Separator
    st.sidebar.title("📂 Navigation")
    page_names = [
        "📊 Overview", "🏢 Companies", "💰 Investors",
        "🌍 Markets", "🔎 Deals", "📈 Forecasting",
        "✨ For You", "🎯 Onboarding"  # Onboarding only if incomplete
    ]

    # Initialize session state for nav select (defaults to 0; prevents auto-switch on load)
    if "nav_select" not in st.session_state:
        st.session_state.nav_select = 0  # Default to Overview

    # Callback to switch on change only (lazy – no auto-switch)
    def nav_change():
        selected_idx = st.session_state.nav_select  # Get changed value
        if selected_idx == 0:
            st.switch_page("1_Overview.py")
        elif selected_idx == 1:
            st.switch_page("2_Companies.py")
        elif selected_idx == 2:
            st.switch_page("3_Investors.py")
        elif selected_idx == 3:
            st.switch_page("4_Markets.py")
        elif selected_idx == 4:
            st.switch_page("6_Deal_Explorer.py")
        elif selected_idx == 5:
            st.switch_page("5_Forecasting.py")
        elif selected_idx == 6:
            st.switch_page("6_For_You.py")
        elif selected_idx == 7:
            # Check if onboarding needed
            if has_preferences(user_id):
                st.sidebar.info("🎉 Onboarding complete! Use other pages for insights.")
            else:
                st.switch_page("7_Onboarding.py")

    # Selectbox with on_change (changes trigger callback; load doesn't)
    st.sidebar.selectbox(
        "Go to Page",
        range(len(page_names)),
        index=st.session_state.nav_select,
        format_func=lambda i: page_names[i],
        key="nav_key",
        on_change=nav_change
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by startupinvestment")