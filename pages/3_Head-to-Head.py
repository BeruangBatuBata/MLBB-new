import streamlit as st
import pandas as pd
from utils.analysis_functions import process_head_to_head_teams

st.set_page_config(layout="wide", page_title="Head-to-Head")

st.title("⚔️ Head-to-Head Comparison")

if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()

pooled_matches = st.session_state['pooled_matches']

# Get a unique, sorted list of all teams
all_teams = sorted(list(set(
    opp.get('name','').strip()
    for match in pooled_matches
    for opp in match.get("match2opponents", [])
    if opp.get('name')
)))

# --- Sidebar Controls ---
st.sidebar.header("Comparison Setup")
st.sidebar.info("This page currently supports Team vs. Team comparison.")

team1 = st.sidebar.selectbox("Select Team 1:", options=all_teams, index=0)
team2 = st.sidebar.selectbox("Select Team 2:", options=all_teams, index=1 if len(all_teams) > 1 else 0)


# --- Main Page Display ---
if team1 == team2:
    st.error("Please select two different teams for comparison.")
else:
    st.header(f"{team1} vs {team2}")
    
    with st.spinner(f"Analyzing matches between {team1} and {team2}..."):
        h2h_data = process_head_to_head_teams(team1, team2, pooled_matches)

    if h2h_data["total_games"] == 0:
        st.warning(f"No direct matches found between {team1} and {team2} in the selected tournaments.")
    else:
        # --- Display Results ---
        st.subheader("Overall Match Results")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label=f"{team1} Wins", value=h2h_data["win_counts"][team1])
        col2.metric(label=f"{team2} Wins", value=h2h_data["win_counts"][team2])
        col3.metric(label="Total Games Played", value=h2h_data["total_games"])
        
        st.markdown("---")
        
        # --- Picks and Bans in Columns ---
        st.subheader("Top Picks & Bans (in Head-to-Head Matches)")
        
        col_picks, col_bans = st.columns(2)
        
        with col_picks:
            st.write(f"**Most Picked by {team1}**")
            t1_picks_df = h2h_data["t1_picks_df"]
            # --- ADD THIS LINE ---
            t1_picks_df.index += 1
            st.dataframe(t1_picks_df, use_container_width=True)
            
            st.write(f"**Most Picked by {team2}**")
            t2_picks_df = h2h_data["t2_picks_df"]
            # --- ADD THIS LINE ---
            t2_picks_df.index += 1
            st.dataframe(t2_picks_df, use_container_width=True)
            
        with col_bans:
            st.write(f"**Most Banned by {team1}**")
            t1_bans_df = h2h_data["t1_bans_df"]
            # --- ADD THIS LINE ---
            t1_bans_df.index += 1
            st.dataframe(t1_bans_df, use_container_width=True)
            
            st.write(f"**Most Banned by {team2}**")
            t2_bans_df = h2h_data["t2_bans_df"]
            # --- ADD THIS LINE ---
            t2_bans_df.index += 1
            st.dataframe(t2_bans_df, use_container_width=True)
