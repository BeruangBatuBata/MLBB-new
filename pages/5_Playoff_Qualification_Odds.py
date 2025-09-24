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

# --- Initialize Session State for this page ---
if 'sim_results' not in st.session_state:
    st.session_state.sim_results = None
if 'forced_outcomes' not in st.session_state:
    st.session_state.forced_outcomes = {}

# Use the first selected tournament as the context for this page
tournament_name = st.session_state.selected_tournaments[0]
if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
    st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']
    st.session_state.bracket_tournament = tournament_name


# --- Core Logic in a Callback Function ---
def prepare_and_run_simulation():
    """
    This function is called when the button is clicked. It prepares all data
    based on the CURRENT state of the UI widgets and runs the simulation.
    """
    # 1. Filter for regular season matches
    all_parsed = st.session_state.parsed_matches
    regular_season = [m for m in all_parsed if m.get("is_regular_season", False)]
    teams = sorted(list(set(m["teamA"] for m in regular_season) | set(m["teamB"] for m in regular_season)))
    
    # 2. Determine played vs unplayed based on slider
    cutoff_idx = st.session_state.cutoff_week_idx
    week_blocks = st.session_state.week_blocks
    
    played, unplayed = [], []
    cutoff_dates = set(d for i in range(cutoff_idx + 1) for d in week_blocks[i]) if cutoff_idx >= 0 else set()
    for m in regular_season:
        (played if m["date"] in cutoff_dates else unplayed).append(m)
        
    # 3. Calculate current standings
    wins, diffs = defaultdict(int), defaultdict(int)
    for m in played:
        if m["winner"] in ("1", "2"):
            winner_idx = int(m["winner"]) - 1
            teams_in_match = [m["teamA"], m["teamB"]]
            winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
            wins[winner] += 1
            score_winner = m["scoreA"] if winner_idx == 0 else m["scoreB"]
            score_loser = m["scoreB"] if winner_idx == 0 else m["scoreA"]
            diffs[winner] += score_winner - score_loser
            diffs[loser] += score_loser - score_winner
            
    # 4. Run simulation with current data
    unplayed_tuples = [(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed]
    with st.spinner(f"Running {st.session_state.n_simulations} simulations..."):
        df_probs = run_monte_carlo_simulation(
            teams, wins, diffs, unplayed_tuples, 
            st.session_state.forced_outcomes, 
            st.session_state.current_brackets, 
            st.session_state.n_simulations
        )
        st.session_state.sim_results = df_probs

# --- Data Preparation for UI ---
regular_season_matches = [m for m in st.session_state.parsed_matches if m.get("is_regular_season", False)]
if not regular_season_matches:
    st.error("No regular season matches found. This feature requires regular season data.")
    st.stop()

all_dates = sorted(list(set(m["date"] for m in regular_season_matches)))
week_blocks = []
if all_dates:
    current_block = [all_dates[0]]
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i-1]).days <= 3:
            current_block.append(all_dates[i])
        else:
            week_blocks.append(current_block)
            current_block = [all_dates[i]]
    week_blocks.append(current_block)
st.session_state.week_blocks = week_blocks


# --- Sidebar UI Controls ---
st.sidebar.header("Simulation Controls")
week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}
week_options["Pre-Season (Week 0)"] = -1
sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
cutoff_week_label = st.sidebar.select_slider(
    "Select Cutoff Week:",
    options=[opt[0] for opt in sorted_week_options],
    value=sorted_week_options[-1][0]
)
# Store the index in session state so the callback can access it
st.session_state.cutoff_week_idx = week_options[cutoff_week_label]
st.session_state.n_simulations = st.sidebar.number_input("Number of Simulations:", 1000, 100000, 10000, 1000)

st.sidebar.button("Run Monte Carlo Simulation", type="primary", on_click=prepare_and_run_simulation)

# --- Bracket Configuration UI ---
st.sidebar.subheader("Tournament Format")
with st.sidebar.expander("Configure Playoff Brackets"):
    # This UI now directly modifies the session state
    for i, bracket in enumerate(st.session_state.current_brackets):
        cols = st.columns([3, 1, 1])
        bracket['name'] = cols[0].text_input("Bracket Name", value=bracket['name'], key=f"name_{i}")
        bracket['start'] = cols[1].number_input("Start Rank", min_value=1, value=bracket['start'], key=f"start_{i}")
        end_val = bracket['end'] if bracket['end'] is not None else len(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches))
        bracket['end'] = cols[2].number_input("End Rank", min_value=bracket['start'], value=end_val, key=f"end_{i}")
    
    if st.button("Save Brackets"):
        save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
        st.success("Brackets saved!")


# --- "What-If" and Display Section ---
# This part of the UI now just READS from the state calculated by the slider
cutoff_idx = st.session_state.cutoff_week_idx
cutoff_dates = set(d for i in range(cutoff_idx + 1) for d in week_blocks[i]) if cutoff_idx >= 0 else set()
played = [m for m in regular_season_matches if m["date"] in cutoff_dates]
unplayed = [m for m in regular_season_matches if m["date"] not in cutoff_dates]

st.subheader("Upcoming Matches (What-If Scenarios)")
with st.expander("Set specific outcomes for upcoming matches", expanded=True):
    if not unplayed:
        st.write("No upcoming matches to simulate for the selected cutoff week.")
    else:
        unplayed_tuples = sorted([(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed], key=lambda x: x[2])
        for teamA, teamB, date, bo in unplayed_tuples:
            match_key = (teamA, teamB, date)
            options = get_series_outcome_options(teamA, teamB, bo)
            # Read default from session state, or set to 'random'
            default_index = next((i for i, opt in enumerate(options) if opt[1] == st.session_state.forced_outcomes.get(match_key)), 0)
            outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, index=default_index, format_func=lambda x: x[0], key=f"match_{date}_{teamA}")
            st.session_state.forced_outcomes[match_key] = outcome[1]

st.markdown("---")
st.subheader("Results")
col1, col2 = st.columns(2)
with col1:
    st.write("**Current Standings**")
    teams = sorted(list(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches)))
    standings_df = build_standings_table(teams, played)
    st.dataframe(standings_df, use_container_width=True)
with col2:
    st.write("**Playoff Qualification Probabilities**")
    if st.session_state.sim_results is not None:
        try:
            # Sort probability table based on current standings for consistency
            sorted_probs_df = st.session_state.sim_results.set_index('Team').loc[standings_df['Team']].reset_index()
            sorted_probs_df.index += 1
            st.dataframe(sorted_probs_df, use_container_width=True)
        except KeyError:
            st.warning("Standings and simulation results are out of sync. Please re-run the simulation.")
            st.dataframe(st.session_state.sim_results)
    else:
        st.info("Click 'Run Monte Carlo Simulation' to see probabilities.")
