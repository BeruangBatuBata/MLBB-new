import streamlit as st
import pandas as pd
from collections import defaultdict
from utils.simulation import get_series_outcome_options, build_standings_table, run_monte_carlo_simulation

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

# --- Prepare Data ---
parsed_matches = st.session_state.parsed_matches
teams = sorted(list(set([m["teamA"] for m in parsed_matches] + [m["teamB"] for m in parsed_matches])))
all_dates = sorted(list(set(m["date"] for m in parsed_matches)))

# Group dates into "weeks" (blocks of consecutive play days)
week_blocks = []
if all_dates:
    current_block = [all_dates[0]]
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i-1]).days <= 2: # Group days within 2 days of each other
            current_block.append(all_dates[i])
        else:
            week_blocks.append(current_block)
            current_block = [all_dates[i]]
    week_blocks.append(current_block)

# --- Sidebar Controls ---
st.sidebar.header("Simulation Controls")
week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}
week_options["Pre-Season (Week 0)"] = -1

# Sort options to have Pre-Season first, then Week 1, etc.
sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
cutoff_week_label = st.sidebar.select_slider(
    "Select Cutoff Week:",
    options=[opt[0] for opt in sorted_week_options],
    value=sorted_week_options[-1][0] if sorted_week_options else "Pre-Season (Week 0)"
)
cutoff_week_idx = week_options[cutoff_week_label]

n_simulations = st.sidebar.number_input("Number of Simulations:", min_value=1000, max_value=100000, value=10000, step=1000)

run_simulation_button = st.sidebar.button("Run Monte Carlo Simulation", type="primary")

# --- Data Processing based on Cutoff Week ---
played_matches = []
unplayed_matches = []
current_wins = defaultdict(int)
current_diff = defaultdict(int)

cutoff_dates = set()
if cutoff_week_idx >= 0:
    for i in range(cutoff_week_idx + 1):
        cutoff_dates.update(week_blocks[i])

for m in parsed_matches:
    if m["date"] in cutoff_dates:
        played_matches.append(m)
        if m["winner"] in ("1", "2"):
            winner_idx = int(m["winner"]) - 1
            loser_idx = 1 - winner_idx
            teams_in_match = [m["teamA"], m["teamB"]]
            winner_team = teams_in_match[winner_idx]
            loser_team = teams_in_match[loser_idx]
            
            current_wins[winner_team] += 1
            
            score_winner = m["scoreA"] if winner_idx == 0 else m["scoreB"]
            score_loser = m["scoreB"] if winner_idx == 0 else m["scoreA"]
            
            current_diff[winner_team] += score_winner - score_loser
            current_diff[loser_team] += score_loser - score_winner
    else:
        unplayed_matches.append((m["teamA"], m["teamB"], m["date"], m["bestof"]))

# --- "What-If" Scenarios UI ---
st.subheader("Upcoming Matches (What-If Scenarios)")
with st.expander("Set specific outcomes for upcoming matches", expanded=False):
    if not unplayed_matches:
        st.write("No upcoming matches to simulate.")
    else:
        for teamA, teamB, date, bo in sorted(unplayed_matches, key=lambda x: x[2]):
            match_key = (teamA, teamB, date)
            options = get_series_outcome_options(teamA, teamB, bo)
            
            # Use st.selectbox for a cleaner UI
            outcome = st.selectbox(
                f"{teamA} vs {teamB} ({date})",
                options=options,
                format_func=lambda x: x[0], # Display the readable name
                key=f"match_{date}_{teamA}" # Unique key for widget state
            )
            # Store the outcome code ('A20', 'B21', etc.)
            st.session_state.forced_outcomes[match_key] = outcome[1]

# --- Main Logic ---
if run_simulation_button:
    with st.spinner(f"Running {n_simulations} simulations... This may take a moment."):
        df_probs = run_monte_carlo_simulation(
            teams, current_wins, current_diff, unplayed_matches, 
            st.session_state.forced_outcomes, n_simulations
        )
        st.session_state.sim_results = df_probs

# --- Display Area ---
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
        # Sort probability table based on current standings for consistency
        sorted_probs_df = st.session_state.sim_results.set_index('Team').loc[standings_df['Team']].reset_index()
        sorted_probs_df.index += 1
        st.dataframe(sorted_probs_df, use_container_width=True)
    else:
        st.info("Click 'Run Monte Carlo Simulation' in the sidebar to see the probabilities.")
