import streamlit as st
import pandas as pd
import joblib
from collections import defaultdict
from utils.drafting_ai import predict_draft_outcome, get_all_hero_names
from utils.data_processing import HERO_PROFILES
from utils.api_handler import ALL_TOURNAMENTS

st.set_page_config(layout="wide", page_title="Drafting Assistant")

st.title("🎯 Professional Drafting Assistant")

# --- Load Model and necessary assets ---
try:
    model_assets = joblib.load('draft_predictor.joblib')
    st.session_state.model_loaded = True
except FileNotFoundError:
    st.error("Fatal Error: 'draft_predictor.joblib' not found. Please train the model on the homepage first.")
    st.stop()

# --- Initialize Session State for Draft ---
if 'blue_picks' not in st.session_state:
    st.session_state.blue_picks = {role: None for role in model_assets['roles']}
if 'red_picks' not in st.session_state:
    st.session_state.red_picks = {role: None for role in model_assets['roles']}
if 'blue_bans' not in st.session_state:
    st.session_state.blue_bans = [None] * 5
if 'red_bans' not in st.session_state:
    st.session_state.red_bans = [None] * 5
if 'blue_team' not in st.session_state:
    st.session_state.blue_team = None
if 'red_team' not in st.session_state:
    st.session_state.red_team = None

# --- Data for UI ---
ALL_HERO_NAMES = get_all_hero_names(HERO_PROFILES)

# THIS IS THE CORRECT LOGIC, COPIED FROM YOUR NOTEBOOK'S DESIGN
# It dynamically builds the team list from the currently loaded data.
if 'pooled_matches' in st.session_state and st.session_state['pooled_matches']:
    all_teams_set = set()
    for match in st.session_state['pooled_matches']:
        for opp in match.get("match2opponents", []):
            team_name = opp.get("name", "").strip()
            if team_name:
                all_teams_set.add(team_name)
    ALL_TEAMS = sorted(list(all_teams_set))
else:
    # If no data is loaded, the list will be empty, prompting the user to load data first.
    st.warning("Please load tournament data on the homepage to populate the team lists.")
    ALL_TEAMS = []

hero_options = [None] + ALL_HERO_NAMES
team_options = [None] + ALL_TEAMS
# --- Helper function for dynamic UI updates ---
def update_draft_state():
    # This function will be implicitly called on every widget change by Streamlit's rerun
    pass

# --- Main UI Layout ---
st.markdown("Select teams, then fill in the picks and bans as they happen to see a real-time win probability prediction.")
st.markdown("---")

# --- Prediction Display Area ---
prediction_placeholder = st.empty()

# --- Draft Selection Area ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Blue Side")
    st.session_state.blue_team = st.selectbox("Blue Team", options=team_options, key="sb_blue_team")
    
    st.write("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        st.session_state.blue_bans[i] = ban_cols[i].selectbox(f"B{i+1}", options=hero_options, key=f"blue_ban_{i}")

    st.write("**Picks**")
    for role in model_assets['roles']:
        st.session_state.blue_picks[role] = st.selectbox(role, options=hero_options, key=f"blue_pick_{role}")

with col2:
    st.subheader("Red Side")
    st.session_state.red_team = st.selectbox("Red Team", options=team_options, key="sb_red_team")

    st.write("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        st.session_state.red_bans[i] = ban_cols[i].selectbox(f"B{i+1}", options=hero_options, key=f"red_ban_{i}")

    st.write("**Picks**")
    for role in model_assets['roles']:
        st.session_state.red_picks[role] = st.selectbox(role, options=hero_options, key=f"red_pick_{role}")

# --- Logic to run after every interaction ---
blue_picks_filled = {role: hero for role, hero in st.session_state.blue_picks.items() if hero}
red_picks_filled = {role: hero for role, hero in st.session_state.red_picks.items() if hero}

# A prediction can only be made if there's at least one pick on each side
if blue_picks_filled and red_picks_filled and st.session_state.blue_team and st.session_state.red_team:
    win_prob_blue = predict_draft_outcome(
        blue_picks_filled,
        red_picks_filled,
        st.session_state.blue_team,
        st.session_state.red_team,
        model_assets,
        HERO_PROFILES
    )
    win_prob_red = 1 - win_prob_blue

    # Display the probability bar
    with prediction_placeholder.container():
        st.subheader("Live Win Probability")
        blue_pct = int(win_prob_blue * 100)
        red_pct = 100 - blue_pct
        
        bar_html = f"""
        <div style="display: flex; width: 100%; height: 32px; font-weight: bold; font-size: 16px; border-radius: 5px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);">
            <div style="width: {blue_pct}%; background-color: #4299e1; color: white; display: flex; align-items: center; justify-content: center;">{blue_pct}%</div>
            <div style="width: {red_pct}%; background-color: #f56565; color: white; display: flex; align-items: center; justify-content: center;">{red_pct}%</div>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)
        st.markdown("---")
else:
    with prediction_placeholder.container():
        st.info("Prediction will appear here once teams and at least one pick for each side are selected.")
        st.markdown("---")
