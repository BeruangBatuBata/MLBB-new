import streamlit as st
import pandas as pd
from utils.analysis_functions import process_hero_drilldown_data

st.set_page_config(layout="wide", page_title="Hero Detail Drilldown")

st.title("🔎 Hero Detail Drilldown")

# --- Check for loaded data ---
if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()

# --- Cache the heavy processing ---
# We now pass the list of tournament names as a "key" to invalidate the cache.
@st.cache_data
def get_hero_drilldown_data(_pooled_matches, _tournament_names):
    # The _tournament_names argument is only used to trigger the cache.
    # The function itself still processes the full _pooled_matches data.
    return process_hero_drilldown_data(_pooled_matches)

# --- UI Controls and Display ---
pooled_matches = st.session_state['pooled_matches']
# Get the list of names to use as our cache key
selected_tournament_names = st.session_state['selected_tournaments']

with st.spinner("Processing all matches for hero details..."):
    # Call the function with both arguments
    all_heroes, hero_stats_map = get_hero_drilldown_data(pooled_matches, selected_tournament_names)

st.sidebar.header("Hero Filters")
selected_hero = st.sidebar.selectbox(
    "Select a Hero:",
    options=all_heroes
)

st.info(f"Displaying detailed statistics for **{selected_hero}** in the selected tournaments: **{', '.join(st.session_state['selected_tournaments'])}**")

if selected_hero and selected_hero in hero_stats_map:
    hero_data = hero_stats_map[selected_hero]
    
    st.subheader(f"Performance by Team")
    df_team = hero_data["per_team_df"].reset_index(drop=True)
    # --- ADD THIS LINE ---
    df_team.index += 1
    st.dataframe(df_team, use_container_width=True)
    
    st.subheader(f"Performance Against Opposing Heroes")
    df_matchups = hero_data["matchups_df"].reset_index(drop=True)
    # --- ADD THIS LINE ---
    df_matchups.index += 1
    st.dataframe(df_matchups, use_container_width=True)
else:
    st.warning("No data available for the selected hero.")
