import streamlit as st
from collections import OrderedDict
from utils.api_handler import ALL_TOURNAMENTS, fetch_tournament_matches
from utils.data_processing import parse_matches

# --- Page Configuration ---
st.set_page_config(
    page_title="MLBB Analytics Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Title and Introduction ---
st.title("MLBB Pro-Scene Analytics Dashboard")
st.markdown("Welcome! Please select the tournaments you wish to analyze in the sidebar, then click 'Load Data'.")

# --- Session State Initialization ---
# This ensures that our app's memory is set up correctly
if 'selected_tournaments' not in st.session_state:
    st.session_state['selected_tournaments'] = []
if 'pooled_matches' not in st.session_state:
    st.session_state['pooled_matches'] = None
if 'parsed_matches' not in st.session_state:
    st.session_state['parsed_matches'] = None

# --- Sidebar for Tournament Selection ---
with st.sidebar:
    st.header("Tournament Selection")

    selected_tournaments = st.multiselect(
        "Choose tournaments:",
        options=list(ALL_TOURNAMENTS.keys()),
        default=st.session_state['selected_tournaments'],
        placeholder="Select one or more tournaments"
    )

    if st.button("Load Data", type="primary"):
    if not selected_tournaments:
        st.warning("Please select at least one tournament.")
    else:
        # --- ADD THESE TWO LINES TO RESET THE DATA ---
        st.session_state['pooled_matches'] = []
        st.session_state['parsed_matches'] = None
        # --- END OF ADDITION ---
        
        st.session_state['selected_tournaments'] = selected_tournaments
        all_matches_raw = []
        has_errors = False
        
        with st.spinner("Fetching data from Liquipedia API..."):
            # (The rest of the code in this block remains exactly the same)
            for name in selected_tournaments:
                    tournament_path = ALL_TOURNAMENTS[name]['path']
                    matches = fetch_tournament_matches(tournament_path)
                    all_matches_raw.extend(matches)
            
            if all_matches_raw:
                st.session_state['pooled_matches'] = all_matches_raw
                st.session_state['parsed_matches'] = parse_matches(all_matches_raw)
                st.success(f"Successfully loaded and parsed data for {len(selected_tournaments)} tournament(s).")
                st.info("You can now navigate to an analysis page.")
            else:
                st.error("Failed to load any match data. Please check the API status or your selection.")

# --- Display loaded data status ---
if st.session_state.get('parsed_matches'):
    st.success(f"**Data Loaded:** {len(st.session_state['parsed_matches'])} matches from {len(st.session_state['selected_tournaments'])} tournament(s).")
    st.write("Navigate to a page in the sidebar to view the analysis.")
