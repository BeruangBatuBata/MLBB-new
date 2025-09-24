import streamlit as st
import pandas as pd
from collections import defaultdict
from utils.simulation import (
    get_series_outcome_options,
    build_standings_table,
    run_monte_carlo_simulation,
    load_bracket_config,
    save_bracket_config
)

st.set_page_config(layout="wide", page_title="Playoff Qualification Odds")

st.title("🏆 Playoff Qualification Odds")

# --- Check for loaded data ---
if 'parsed_matches' not in st.session_state or not st.session_state['parsed_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()
    
# Use the first selected tournament as the context for this page
tournament_name = st.session_state.selected_tournaments[0]
st.info(f"Analyzing simulation odds for: **{tournament_name}**")

# --- Initialize Session State ---
if 'sim_results' not in st.session_state:
    st.session_state.sim_results = None
if 'forced_outcomes' not in st.session_state:
    st.session_state.forced_outcomes = {}
if 'current_brackets' not in st.session_state:
    st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']

# --- BUG FIX: Filter for REGULAR SEASON matches only ---
all_parsed_matches = st.session_state.parsed_matches
regular_season_matches = [m for m in all_parsed_matches if m.get("is_regular_season", False)]
if not regular_season_matches:
    st.error("No regular season matches found in the selected data. This feature requires regular season data to simulate.")
    st.stop()

teams = sorted(list(set([m["teamA"] for m in regular_season_matches] + [m["teamB"] for m in regular_season_matches])))
all_dates = sorted(list(set(m["date"] for m in regular_season_matches)))

# Group dates into "weeks"
week_blocks = []
if all_dates:
    current_block = [all_dates[0]]
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i-1]).days <= 2:
            current_block.append(all_dates[i])
        else:
            week_blocks.append(current_block)
            current_block = [all_dates[i]]
    week_blocks.append(current_block)

# --- Sidebar Controls ---
st.sidebar.header("Simulation Controls")
week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}
week_options["Pre-Season (Week 0)"] = -1
sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[opt[0] for opt in sorted_week_options], value=sorted_week_options[-1][0])
cutoff_week_idx = week_options[cutoff_week_label]
n_simulations = st.sidebar.number_input("Number of Simulations:", 1000, 100000, 10000, 1000)
run_simulation_button = st.sidebar.button("Run Monte Carlo Simulation", type="primary")

# --- Data Processing based on Cutoff Week ---
played_matches, unplayed_matches = [], []
current_wins, current_diff = defaultdict(int), defaultdict(int)
cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()

for m in regular_season_matches:
    (played_matches if m["date"] in cutoff_dates else unplayed_matches).append(m)

for m in played_matches:
    if m["winner"] in ("1", "2"):
        winner_idx = int(m["winner"]) - 1
        teams_in_match = [m["teamA"], m["teamB"]]
        winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
        current_wins[winner] += 1
        score_winner = m["scoreA"] if winner_idx == 0 else m["scoreB"]
        score_loser = m["scoreB"] if winner_idx == 0 else m["scoreA"]
        current_diff[winner] += score_winner - score_loser
        current_diff[loser] += score_loser - score_winner

# --- UI FOR BRACKET CONFIGURATION (Restored Feature) ---
st.sidebar.subheader("Tournament Format")
with st.sidebar.expander("Configure Playoff Brackets"):
    for i, bracket in enumerate(st.session_state.current_brackets):
        cols = st.columns([3, 1, 1])
        bracket['name'] = cols[0].text_input("Bracket Name", value=bracket['name'], key=f"name_{i}")
        bracket['start'] = cols[1].number_input("Start Rank", min_value=1, value=bracket['start'], key=f"start_{i}")
        end_val = bracket['end'] if bracket['end'] is not None else len(teams)
        bracket['end'] = cols[2].number_input("End Rank", min_value=bracket['start'], value=end_val, key=f"end_{i}")
        if bracket['end'] >= len(teams): bracket['end'] = None
    
    if st.button("Save Brackets"):
        save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
        st.success("Bracket configuration saved!")

# --- "What-If" Scenarios UI ---
st.subheader("Upcoming Matches (What-If Scenarios)")
with st.expander("Set specific outcomes for upcoming matches", expanded=True):
    if not unplayed_matches:
        st.write("No upcoming matches to simulate.")
    else:
        unplayed_tuples = sorted([(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed_matches], key=lambda x: x[2])
        for teamA, teamB, date, bo in unplayed_tuples:
            match_key = (teamA, teamB, date)
            options = get_series_outcome_options(teamA, teamB, bo)
            outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"match_{date}_{teamA}")
            st.session_state.forced_outcomes[match_key] = outcome[1]

# --- Main Logic & Display ---
if run_simulation_button:
    unplayed_tuples = [(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed_matches]
    with st.spinner(f"Running {n_simulations} simulations..."):
        df_probs = run_monte_carlo_simulation(teams, current_wins, current_diff, unplayed_tuples, st.session_state.forced_outcomes, st.session_state.current_brackets, n_simulations)
        st.session_state.sim_results = df_probs

st.markdown("---")
st.subheader("Results")
col1, col2 = st.columns(2)
with col1:
    st.write("**Current Standings**")
    standings_df = build_standings_table(teams, played_matches)
    st.dataframe(standings_df, use_container_width=True)
with col2:
    st.write("**Playoff Qualification Probabilities**")
    if st.session_state.sim_results is not None:
        sorted_probs_df = st.session_state.sim_results.set_index('Team').loc[standings_df['Team']].reset_index()
        sorted_probs_df.index += 1
        st.dataframe(sorted_probs_df, use_container_width=True)
    else:
        st.info("Click 'Run Monte Carlo Simulation' to see probabilities.")
