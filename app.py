import streamlit as st
from collections import OrderedDict
from utils.data_processing import parse_matches
from utils.api_handler import ALL_TOURNAMENTS, load_tournament_data
from utils.drafting_ai import train_and_save_prediction_model
from utils.data_processing import HERO_PROFILES, HERO_DAMAGE_TYPE
from collections import OrderedDict

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
        default=st.session_state.get('selected_tournaments', []),
        placeholder="Select one or more tournaments"
    )

    # --- Button Grid ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Load Data", type="primary", use_container_width=True):
            if not selected_tournaments:
                st.warning("Please select at least one tournament.")
            else:
                # This logic remains the same
                st.cache_data.clear()
                st.session_state['sim_results'] = None
                st.session_state['pooled_matches'] = None
                st.session_state['parsed_matches'] = None
                st.session_state['selected_tournaments'] = selected_tournaments
                all_matches_raw = []
                with st.spinner("Loading tournament data..."):
                    for name in selected_tournaments:
                        matches = load_tournament_data(name)
                        if matches: all_matches_raw.extend(matches)
                if all_matches_raw:
                    st.session_state['pooled_matches'] = all_matches_raw
                    st.session_state['parsed_matches'] = parse_matches(all_matches_raw)
                    st.success(f"Loaded data for {len(selected_tournaments)} tournament(s).")
                else:
                    st.error("Could not load any match data.")

    with col2:
        if st.button("Clear Live Cache", use_container_width=True):
            live_selected = [t for t in selected_tournaments if ALL_TOURNAMENTS[t].get('live')]
            if not live_selected:
                st.warning("Please select at least one 'live' tournament to clear its cache.")
            else:
                cleared_count = 0
                for name in live_selected:
                    filename = f"{name.replace(' ', '_').replace('/', '_')}.json"
                    filepath = f"data/{filename}"
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        cleared_count += 1
                st.success(f"Cleared cache for {cleared_count} live tournament(s). Click 'Load Data' to refresh.")

    st.markdown("---")
    st.subheader("AI Model Management")

    if st.button("Train Drafting AI Model", use_container_width=True):
        if not selected_tournaments:
            st.warning("Please select tournaments to use for training data.")
        else:
            with st.spinner(f"Fetching data for {len(selected_tournaments)} tournaments to train model..."):
                training_matches = []
                for name in selected_tournaments:
                    matches = load_tournament_data(name)
                    if matches: training_matches.extend(matches)
            
            if not training_matches:
                st.error("No match data could be loaded for training.")
            else:
                st.info(f"Beginning training on {len(training_matches)} raw matches...")
                try:
                    with st.spinner("Training advanced XGBoost model... This may take a minute."):
                        message = train_and_save_prediction_model(training_matches, HERO_PROFILES)
                    st.success(message)
                except Exception as e:
                    st.error(f"An error occurred during training: {e}")

if st.button("Load Data", type="primary"):
    # This command clears the cache for functions like get_hero_drilldown_data
    st.cache_data.clear()

    if not selected_tournaments:
        st.warning("Please select at least one tournament.")
    else:
        # Reset all session state data to ensure a clean slate
        st.session_state['sim_results'] = None
        st.session_state['pooled_matches'] = None
        st.session_state['parsed_matches'] = None
        st.session_state['selected_tournaments'] = selected_tournaments
        
        # This is the line that was missing, causing the NameError
        all_matches_raw = []
        
        with st.spinner("Loading tournament data..."):
            for name in selected_tournaments:
                matches = load_tournament_data(name)
                if matches:
                    all_matches_raw.extend(matches)
        
        if all_matches_raw:
            st.session_state['pooled_matches'] = all_matches_raw
            st.session_state['parsed_matches'] = parse_matches(all_matches_raw)
            st.success(f"Successfully loaded data for {len(selected_tournaments)} tournament(s).")
            st.info("You can now navigate to an analysis page.")
        else:
            st.error("Could not load any match data. Please check your selection and local data files.")
            
# --- Display loaded data status ---
if st.session_state.get('parsed_matches'):
    st.success(f"**Data Loaded:** {len(st.session_state['parsed_matches'])} matches from {len(st.session_state['selected_tournaments'])} tournament(s).")
    st.write("Navigate to a page in the sidebar to view the analysis.")
