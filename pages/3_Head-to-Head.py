# beruangbatubata/mlbb-new/MLBB-new-44d3b1513eb1b302f1f96286fcccc3d4374561ec/pages/3_Head-to-Head.py
import streamlit as st
from utils import data_processing, analysis_functions
import pandas as pd
from collections import Counter

st.set_page_config(layout="wide", page_title="Head-to-Head")

if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.info("Please select and load tournament data from the '🏠 Home' page first.")
    st.stop()

pooled_matches = st.session_state['pooled_matches']
tournaments_shown = st.session_state.get('tournaments_shown', [])

st.title("⚔️ Head-to-Head Comparison")
st.info(f"**Tournaments loaded:** {', '.join(tournaments_shown)}")

# --- Data Preparation ---
team_norm2disp, all_teams_norm = data_processing.get_all_teams_from_matches(pooled_matches)
all_heroes = data_processing.get_all_heroes_from_matches(pooled_matches)
team_options = [team_norm2disp.get(n, n) for n in sorted(all_teams_norm)]

# --- UI Controls ---
mode = st.radio("Select Comparison Mode:", ['Team vs. Team', 'Hero vs. Hero'], horizontal=True)

if mode == 'Team vs. Team':
    col1, col2 = st.columns(2)
    with col1:
        team1_disp = st.selectbox("Select Team 1:", team_options, index=0)
    with col2:
        team2_disp = st.selectbox("Select Team 2:", team_options, index=1 if len(team_options) > 1 else 0)

    if st.button("Compare Teams", use_container_width=True, type="primary"):
        if team1_disp == team2_disp:
            st.error("Please select two different teams.")
        else:
            # Find normalized names
            team1_norm = next((norm for norm, disp in team_norm2disp.items() if disp == team1_disp), None)
            team2_norm = next((norm for norm, disp in team_norm2disp.items() if disp == team2_disp), None)

            if team1_norm and team2_norm:
                results = analysis_functions.do_team_h2h(pooled_matches, team1_norm, team2_norm, team_norm2disp)
                
                if not results['h2h_matches']:
                    st.warning(f"No direct matches found between {team1_disp} and {team2_disp}.")
                else:
                    st.subheader(f"{team1_disp} vs {team2_disp} Head-to-Head")
                    st.markdown(f"**Total Games:** {results['total_games']}")
                    st.markdown(f"**{team1_disp} Wins:** **<span style='color:green;'>{results['win_counts'][team1_norm']}</span>**", unsafe_allow_html=True)
                    st.markdown(f"**{team2_disp} Wins:** **<span style='color:green;'>{results['win_counts'][team2_norm']}</span>**", unsafe_allow_html=True)
                    st.markdown("---")

                    # Display paired tables using columns
                    st.subheader("Head-to-Head Statistics")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Top picks by {team1_disp} (vs {team2_disp})**")
                        st.dataframe(results['t1_heroes'], use_container_width=True)
                        st.write(f"**Target bans by {team1_disp} (vs {team2_disp})**")
                        st.dataframe(results['t1_bans'], use_container_width=True)
                    with col_b:
                        st.write(f"**Top picks by {team2_disp} (vs {team1_disp})**")
                        st.dataframe(results['t2_heroes'], use_container_width=True)
                        st.write(f"**Target bans by {team2_disp} (vs {team1_disp})**")
                        st.dataframe(results['t2_bans'], use_container_width=True)

else: # Hero vs. Hero
    col1, col2 = st.columns(2)
    with col1:
        hero1 = st.selectbox("Select Hero 1:", all_heroes, index=0)
    with col2:
        hero2 = st.selectbox("Select Hero 2:", all_heroes, index=1 if len(all_heroes) > 1 else 0)

    if st.button("Compare Heroes", use_container_width=True, type="primary"):
        if hero1 == hero2:
            st.error("Please select two different heroes.")
        else:
            results = analysis_functions.do_hero_h2h(pooled_matches, hero1, hero2)

            if results['games_with_both'] == 0:
                st.warning(f"No games found where {hero1} and {hero2} were on opposing teams.")
            else:
                st.subheader(f"{hero1} vs {hero2} Head-to-Head")
                st.markdown(f"**Games on Opposite Teams:** {results['games_with_both']}")
                win_rate_h1 = (results['win_h1'] / results['games_with_both'] * 100)
                win_rate_h2 = (results['win_h2'] / results['games_with_both'] * 100)
                st.markdown(f"**{hero1} Wins:** **<span style='color:green;'>{results['win_h1']} ({win_rate_h1:.2f}%)</span>**", unsafe_allow_html=True)
                st.markdown(f"**{hero2} Wins:** **<span style='color:green;'>{results['win_h2']} ({win_rate_h2:.2f}%)</span>**", unsafe_allow_html=True)
