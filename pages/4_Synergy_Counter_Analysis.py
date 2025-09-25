# beruangbatubata/mlbb-new/MLBB-new-44d3b1513eb1b302f1f96286fcccc3d4374561ec/pages/4_Synergy_Counter_Analysis.py
import streamlit as st
from utils import data_processing, analysis_functions, plotting
import pandas as pd

st.set_page_config(layout="wide", page_title="Synergy & Counter Analysis")

if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.info("Please select and load tournament data from the '🏠 Home' page first.")
    st.stop()

pooled_matches = st.session_state['pooled_matches']
tournaments_shown = st.session_state.get('tournaments_shown', [])

st.title("🤝 Synergy & Counter Analysis")
st.info(f"**Tournaments loaded:** {', '.join(tournaments_shown)}")

# --- Data Preparation ---
team_norm2disp, all_teams_norm = data_processing.get_all_teams_from_matches(pooled_matches)
all_heroes = data_processing.get_all_heroes_from_matches(pooled_matches)
team_options = [("All Teams", "all")] + [(team_norm2disp.get(n, n), n) for n in sorted(all_teams_norm)]

# --- UI Controls ---
mode = st.selectbox("Select Analysis Mode:", ["Synergy Combos", "Anti-Synergy Combos", "Counter Combos"])

cols = st.columns([1, 1, 2])
with cols[0]:
    min_games = st.slider("Minimum Games Played:", 1, 20, 5)
with cols[1]:
    top_n = st.slider("Top N Results:", 3, 30, 10)
with cols[2]:
    selected_team_norm = st.selectbox(
        "Filter by Team:", 
        options=team_options, 
        format_func=lambda x: x[0]
    )[1]

# --- Analysis Logic ---
df = pd.DataFrame()

if mode == "Synergy Combos":
    st.subheader("Best Performing Hero Duos (Highest Win Rate)")
    df = analysis_functions.analyze_synergy(pooled_matches, selected_team_norm, min_games, top_n, anti=False, team_norm_to_display_map=team_norm2disp)
    fig = plotting.plot_synergy_bar(df, "Win Rate of Top Hero Duos")

elif mode == "Anti-Synergy Combos":
    st.subheader("Worst Performing Hero Duos (Lowest Win Rate)")
    df = analysis_functions.analyze_synergy(pooled_matches, selected_team_norm, min_games, top_n, anti=True, team_norm_to_display_map=team_norm2disp)
    fig = plotting.plot_synergy_bar(df, "Win Rate of Bottom Hero Duos")

elif mode == "Counter Combos":
    st.subheader("Hero vs. Hero Matchups (Ally vs. Enemy)")
    df = analysis_functions.analyze_counter(pooled_matches, min_games, top_n)
    fig = plotting.plot_counter_heatmap(df, "Win Rate: Ally Hero vs Enemy Hero")

# --- Display Results ---
if df.empty:
    st.warning("No hero pairs found that meet the selected criteria. Try adjusting the filters.")
else:
    st.dataframe(df, use_container_width=True)
    plotting.offer_csv_download(df, f"{mode.replace(' ', '_').lower()}.csv")
    
    if fig:
        st.pyplot(fig)
