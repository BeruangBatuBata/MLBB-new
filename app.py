import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="MLBB Analytics Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Title and Introduction ---
st.title("MLBB Pro-Scene Analytics Dashboard")

st.markdown("""
    Welcome to the Mobile Legends: Bang Bang Analytics Dashboard.

    **This tool provides in-depth analysis of professional tournament data.**

    ### How to Get Started:
    1.  **Select an Analysis Mode** from the sidebar on the left.
    2.  **Choose one or more tournaments** to analyze.
    3.  The results will be displayed on the selected page.

    ---
""")

st.info("Please select an analysis mode from the sidebar to begin.", icon="👈")
