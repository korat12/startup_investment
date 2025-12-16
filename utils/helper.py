import streamlit as st

# ------------------------------
# BASIC FORMATTERS
# ------------------------------

def format_inr_cr(value):
    """Format number as Cr with 2 decimals."""
    try:
        return f"₹{value:,.2f} Cr"
    except:
        return value


def format_number(value):
    """General purpose number formatting."""
    try:
        return f"{value:,.0f}"
    except:
        return value


def format_percent(value):
    """Percent formatting: 2 decimal places."""
    try:
        return f"{value:.2f}%"
    except:
        return value


# ------------------------------
# SECTION HEADER
# ------------------------------

def section_header(title: str, subtitle: str = ""):
    """
    Display section header with optional subtitle.
    """
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"**{subtitle}**")
    st.markdown("---")


# ------------------------------
# KPI CARDS
# ------------------------------

def kpi_cards(metrics: dict):
    """
    metrics = {
        "Total Funding": "₹500 Cr",
        "Total Rounds": 320,
        "Companies": 180
    }
    """
    cols = st.columns(len(metrics))
    for (col, (label, value)) in zip(cols, metrics.items()):
        col.metric(label, value)


# ------------------------------
# CSS INJECTION (OPTIONAL)
# ------------------------------

def inject_local_css():
    """
    Inject minimal CSS to improve spacing + font size.
    Run once inside app.py
    """
    st.markdown(
        """
        <style>
        /* Larger base font */
        html, body, [class*="css"] {
            font-size: 16px !important;
        }

        /* Enlarge metric fonts */
        div[data-testid="metric-container"] > div {
            font-size: 20px !important;
        }

        /* Section spacing */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
