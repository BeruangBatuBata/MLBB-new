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

# --- Cached Simulation Engine (Correctly Designed) ---
@st.cache_data(show_spinner="Running Monte Carlo simulations...")
def cached_run_simulation(teams, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim):
    """
    This is a pure calculation engine. It takes simple, prepared data and
    returns the simulation results. It no longer uses unsafe str/eval.
    """
    df_probs = run_monte_carlo_simulation(
        list(teams), dict(current_wins), dict(current_diff),
        list(unplayed_matches), dict(forced_outcomes),
        [dict(b) for b in brackets], n_sim
    )
    return df_probs

# --- UI AND DATA PREP (This is the main, interactive part of the script) ---

# 1. Prepare base data
tournament_name = st.session_state.selected_tournaments[0]
regular_season_matches = [m for m in st.session_state.parsed_matches if m.get("is_regular_season", False)]

if not regular_season_matches:
    st.error("No regular season matches found for this feature.")
    st.stop()

teams = tuple(sorted(list(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches))))
all_dates = sorted(list(set(m["date"] for m in regular_season_matches)))
week_blocks = build_week_blocks(all_dates)

# 2. Render Sidebar UI
st.sidebar.header("Simulation Controls")
week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}
week_options["Pre-Season (Week 0)"] = -1
sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[opt[0] for opt in sorted_week_options], value=sorted_week_options[-1][0])
cutoff_week_idx = week_options[cutoff_week_label]
n_simulations = st.sidebar.number_input("Number of Simulations:", 1000, 100000, 10000, 1000)

# Load/manage brackets
if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
    st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']
    st.session_state.bracket_tournament = tournament_name

with st.sidebar.expander("Configure Playoff Brackets"):
    # ... (Bracket configuration UI - this code is correct and remains the same)
    editable_brackets = [b.copy() for b in st.session_state.current_brackets]
    for i, bracket in enumerate(editable_brackets):
        cols = st.columns([4, 2, 2, 1])
        bracket['name'] = cols[0].text_input("Name", value=bracket['name'], key=f"name_{i}")
        bracket['start'] = cols[1].number_input("Start", value=bracket['start'], min_value=1, key=f"start_{i}")
        end_val = bracket['end'] if bracket['end'] is not None else len(teams)
        bracket['end'] = cols[2].number_input("End", value=end_val, min_value=bracket['start'], key=f"end_{i}")
        if cols[3].button("🗑️", key=f"del_{i}"):
            st.session_state.current_brackets.pop(i)
            st.rerun()
    st.session_state.current_brackets = editable_brackets
    if st.button("Save Brackets", type="primary"):
        save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
        st.success("Brackets saved!")
        st.cache_data.clear()

# 3. Determine played vs. unplayed matches
cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
played_matches = []
unplayed_matches = []
for m in regular_season_matches:
    if m["date"] in cutoff_dates and m.get("winner") in ("1", "2"):
        played_matches.append(m)
    else:
        unplayed_matches.append(m)

# 4. Render "What-If" UI
st.subheader("Upcoming Matches (What-If Scenarios)")
forced_outcomes = {}
matches_by_week = defaultdict(list)
for match in unplayed_matches:
    for week_idx, week_dates in enumerate(week_blocks):
        if match['date'] in week_dates:
            matches_by_week[week_idx].append(match)
            break
if not matches_by_week:
    st.info("No upcoming matches to simulate.")
else:
    for i, week_idx in enumerate(sorted(matches_by_week.keys())):
        week_label = f"Week {week_idx + 1} ({week_blocks[week_idx][0]} to {week_blocks[week_idx][-1]})"
        with st.expander(week_label, expanded=(i == 0)):
            for m in sorted(matches_by_week[week_idx], key=lambda x: x['date']):
                teamA, teamB, date, bo = m["teamA"], m["teamB"], m["date"], m["bestof"]
                match_key = (teamA, teamB, date)
                options = get_series_outcome_options(teamA, teamB, bo)
                outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"match_{date}_{teamA}")
                forced_outcomes[match_key] = outcome[1]

# 5. Prepare data inputs for the cached function
current_wins, current_diff = defaultdict(int), defaultdict(int)
for m in played_matches:
    winner_idx = int(m["winner"]) - 1
    teams_in_match = [m["teamA"], m["teamB"]]
    winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
    current_wins[winner] += 1
    score_winner = m["scoreA"] if winner_idx == 0 else m["scoreB"]
    score_loser = m["scoreB"] if winner_idx == 0 else m["scoreA"]
    current_diff[winner] += score_winner - score_loser
    current_diff[loser] += score_loser - score_winner

# Use cache-friendly tuples of simple types
unplayed_tuples = tuple((m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed_matches)
forced_outcomes_tuple = tuple(sorted(forced_outcomes.items()))
brackets_tuple = tuple(frozenset(b.items()) for b in st.session_state.current_brackets)
current_wins_tuple = tuple(sorted(current_wins.items()))
current_diff_tuple = tuple(sorted(current_diff.items()))

# 6. Call the cached simulation
sim_results = cached_run_simulation(
    teams, current_wins_tuple, current_diff_tuple,
    unplayed_tuples, forced_outcomes_tuple, brackets_tuple, n_simulations
)

# 7. Display results
st.markdown("---")
st.subheader("Results")
col1, col2 = st.columns(2)
with col1:
    st.write("**Current Standings**")
    standings_df = build_standings_table(list(teams), played_matches)
    st.dataframe(standings_df, use_container_width=True)
with col2:
    st.write("**Playoff Qualification Probabilities**")
    if sim_results is not None and not sim_results.empty:
        if 'Team' in standings_df.columns and not standings_df.empty:
            sorted_probs_df = sim_results.set_index('Team').loc[standings_df['Team']].reset_index()
            sorted_probs_df.index += 1
            st.dataframe(sorted_probs_df, use_container_width=True)
        else:
            st.dataframe(sim_results)
