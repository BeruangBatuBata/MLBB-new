import streamlit as st
import pandas as pd
from collections import defaultdict
from utils.simulation import (
    get_series_outcome_options,
    build_standings_table,
    run_monte_carlo_simulation,
    load_bracket_config,
    save_bracket_config,
    build_week_blocks
)

st.set_page_config(layout="wide", page_title="Playoff Qualification Odds")

st.title("🏆 Playoff Qualification Odds")

# --- Check for loaded data ---
if 'parsed_matches' not in st.session_state or not st.session_state['parsed_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()

# --- Initialize Session State ---
if 'forced_outcomes' not in st.session_state:
    st.session_state.forced_outcomes = {}

tournament_name = st.session_state.selected_tournaments[0]
if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
    st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']
    st.session_state.bracket_tournament = tournament_name

# --- Data Preparation ---
regular_season_matches = [m for m in st.session_state.parsed_matches if m.get("is_regular_season", False)]
if not regular_season_matches:
    st.error("No regular season matches found. This feature requires regular season data.")
    st.stop()

teams = sorted(list(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches)))
all_dates = sorted(list(set(m["date"] for m in regular_season_matches)))
week_blocks = build_week_blocks(all_dates)

# --- NEW CACHED SIMULATION FUNCTION ---
@st.cache_data(show_spinner="Running Monte Carlo simulations...")
def get_simulation_results(_teams, _played, _unplayed, _forced_outcomes, _brackets, _n_sim):
    """
    This cached function performs the heavy calculation.
    It reruns automatically if any of its inputs (like the cutoff week) change.
    """
    current_wins, current_diff = defaultdict(int), defaultdict(int)
    for m in _played:
        if m["winner"] in ("1", "2"):
            winner_idx = int(m["winner"]) - 1
            teams_in_match = [m["teamA"], m["teamB"]]
            winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
            current_wins[winner] += 1
            score_winner = m["scoreA"] if winner_idx == 0 else m["scoreB"]
            score_loser = m["scoreB"] if winner_idx == 0 else m["scoreA"]
            current_diff[winner] += score_winner - score_loser
            current_diff[loser] += score_loser - score_winner

    unplayed_tuples = [(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in _unplayed]
    
    df_probs = run_monte_carlo_simulation(
        _teams, current_wins, current_diff, unplayed_tuples, 
        _forced_outcomes, _brackets, _n_sim
    )
    return df_probs

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
cutoff_week_idx = week_options[cutoff_week_label]
n_simulations = st.sidebar.number_input("Number of Simulations:", 1000, 100000, 10000, 1000)

# --- Bracket Configuration UI ---
st.sidebar.subheader("Tournament Format")
with st.sidebar.expander("Configure Playoff Brackets"):
    for i, bracket in enumerate(st.session_state.current_brackets):
        cols = st.columns([3, 1, 1])
        bracket['name'] = cols[0].text_input("Bracket Name", value=bracket['name'], key=f"name_{i}")
        bracket['start'] = cols[1].number_input("Start Rank", value=bracket['start'], min_value=1, key=f"start_{i}")
        end_val = bracket['end'] if bracket['end'] is not None else len(teams)
        bracket['end'] = cols[2].number_input("End Rank", value=end_val, min_value=bracket['start'], key=f"end_{i}")
    
    if st.button("Save Brackets"):
        save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
        st.success("Brackets saved!")
        st.cache_data.clear() # Clear cache to reflect new brackets

# --- Data processing based on CURRENT slider value ---
cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
played = [m for m in regular_season_matches if m["date"] in cutoff_dates]
unplayed = [m for m in regular_season_matches if m["date"] not in cutoff_dates]

# --- "What-If" Scenarios UI ---
st.subheader("Upcoming Matches (What-If Scenarios)")
with st.expander("Set specific outcomes for upcoming matches", expanded=True):
    if not unplayed:
        st.write("No upcoming matches to simulate for the selected cutoff week.")
    else:
        unplayed_tuples = sorted([(m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed], key=lambda x: x[2])
        for teamA, teamB, date, bo in unplayed_tuples:
            match_key = (teamA, teamB, date)
            options = get_series_outcome_options(teamA, teamB, bo)
            default_index = next((i for i, opt in enumerate(options) if opt[1] == st.session_state.forced_outcomes.get(match_key)), 0)
            outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, index=default_index, format_func=lambda x: x[0], key=f"match_{date}_{teamA}")
            st.session_state.forced_outcomes[match_key] = outcome[1]

# --- Main Logic: Call the cached function on EVERY rerun ---
# We convert the forced_outcomes dict to a tuple of items to make it hashable for the cache
forced_outcomes_tuple = tuple(sorted(st.session_state.forced_outcomes.items()))
sim_results = get_simulation_results(
    tuple(teams), tuple(map(str, played)), tuple(map(str, unplayed)), 
    forced_outcomes_tuple, tuple(map(str, st.session_state.current_brackets)), n_simulations
)

# --- Display Results ---
st.markdown("---")
st.subheader("Results")
col1, col2 = st.columns(2)

with col1:
    st.write("**Current Standings** (as of selected cutoff week)")
    standings_df = build_standings_table(teams, played)
    st.dataframe(standings_df, use_container_width=True)

with col2:
    st.write("**Playoff Qualification Probabilities**")
    if sim_results is not None and not sim_results.empty:
        try:
            sorted_probs_df = sim_results.set_index('Team').loc[standings_df['Team']].reset_index()
            sorted_probs_df.index += 1
            st.dataframe(sorted_probs_df, use_container_width=True)
        except (KeyError, ValueError):
            st.warning("Standings and simulation results are out of sync. This can happen if team lists differ.")
            st.dataframe(sim_results)
    else:
        st.info("Simulation results will appear here.")
