import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from utils.simulation import (
    get_series_outcome_options, build_standings_table, run_monte_carlo_simulation,
    load_bracket_config, save_bracket_config, build_week_blocks,
    load_group_config, save_group_config, run_monte_carlo_simulation_groups
)

st.set_page_config(layout="wide", page_title="Playoff Qualification Odds")

# --- Page State Initialization ---
if 'page_view' not in st.session_state:
    st.session_state.page_view = 'format_selection'

# --- Check for loaded data ---
if 'parsed_matches' not in st.session_state or not st.session_state['parsed_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()

# --- Global Data Prep ---
tournament_name = st.session_state.selected_tournaments[0]
regular_season_matches = [m for m in st.session_state.parsed_matches if m.get("is_regular_season", False)]
if not regular_season_matches:
    st.error("No regular season matches found for this feature. This feature requires regular season data.")
    st.stop()
teams = sorted(list(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches)))

# --- Cached Simulation Functions ---
@st.cache_data(show_spinner="Running single-table simulation...")
def cached_single_table_sim(teams, played_matches_tuple, unplayed_tuples, forced_outcomes_tuple, brackets_tuple, n_sim):
    played_matches = [eval(m_str) for m_str in played_matches_tuple]
    wins, diffs = defaultdict(int), defaultdict(int)
    for m in played_matches:
        winner_idx = int(m["winner"]) - 1
        teams_in_match = [m["teamA"], m["teamB"]]
        winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
        wins[winner] += 1
        s_w, s_l = (m["scoreA"], m["scoreB"]) if winner_idx == 0 else (m["scoreB"], m["scoreA"])
        diffs[winner] += s_w - s_l
        diffs[loser] += s_l - s_w
    return run_monte_carlo_simulation(list(teams), dict(wins), dict(diffs), list(unplayed_tuples), dict(forced_outcomes_tuple), [dict(b) for b in brackets_tuple], n_sim)

@st.cache_data(show_spinner="Running group stage simulation...")
def cached_group_sim(groups, played_matches_tuple, unplayed_tuples, forced_outcomes_tuple, brackets_tuple, n_sim):
    played_matches = [eval(m_str) for m_str in played_matches_tuple]
    wins, diffs = defaultdict(int), defaultdict(int)
    for m in played_matches:
        winner_idx = int(m["winner"]) - 1
        teams_in_match = [m["teamA"], m["teamB"]]
        winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
        wins[winner] += 1
        s_w, s_l = (m["scoreA"], m["scoreB"]) if winner_idx == 0 else (m["scoreB"], m["scoreA"])
        diffs[winner] += s_w - s_l
        diffs[loser] += s_l - s_w
    return run_monte_carlo_simulation_groups(groups, dict(wins), dict(diffs), list(unplayed_tuples), dict(forced_outcomes_tuple), [dict(b) for b in brackets_tuple], n_sim)

# --- UI Functions ---
def group_setup_ui():
    st.header(f"Group Configuration for {tournament_name}")
    st.write("Assign the teams into their respective groups for the tournament.")
    if 'group_config' not in st.session_state or not isinstance(st.session_state.group_config, dict):
        st.session_state.group_config = {'groups': {'Group A': [], 'Group B': []}}
    num_groups = st.number_input("Number of Groups", min_value=1, max_value=8, value=len(st.session_state.group_config.get('groups', {})))
    current_groups = st.session_state.group_config.get('groups', {})
    if len(current_groups) != num_groups:
        new_groups = {}
        sorted_keys = sorted(current_groups.keys())
        for i in range(num_groups):
            group_name = sorted_keys[i] if i < len(sorted_keys) else f"Group {chr(65+i)}"
            new_groups[group_name] = current_groups.get(group_name, [])
        st.session_state.group_config['groups'] = new_groups
        st.rerun()
    st.markdown("---")
    assigned_teams = {team for group in current_groups.values() for team in group}
    unassigned_teams = [team for team in teams if team not in assigned_teams]
    if unassigned_teams: st.warning(f"Unassigned Teams: {', '.join(unassigned_teams)}")
    cols = st.columns(num_groups)
    for i, (group_name, group_teams) in enumerate(current_groups.items()):
        with cols[i]:
            st.subheader(group_name); new_teams = st.multiselect(f"Teams in {group_name}", options=teams, default=group_teams, key=f"group_{group_name}")
            current_groups[group_name] = new_teams
    if st.button("Save & Continue", type="primary"):
        save_group_config(tournament_name, st.session_state.group_config); st.success("Group configuration saved!")
        st.session_state.page_view = 'group_sim'; st.rerun()

def single_table_dashboard():
    st.header(f"Simulation for {tournament_name} (Single Table)"); st.button("← Change Tournament Format", on_click=lambda: st.session_state.update(page_view='format_selection'))
    week_blocks = build_week_blocks(sorted(list(set(m["date"] for m in regular_season_matches))))
    st.sidebar.header("Simulation Controls")
    week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}; week_options["Pre-Season (Week 0)"] = -1
    sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
    cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[opt[0] for opt in sorted_week_options], value=sorted_week_options[-1][0])
    cutoff_week_idx = week_options[cutoff_week_label]
    n_sim = st.sidebar.number_input("Simulations:", 1000, 100000, 10000, 1000, key="single_sim_count")
    if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
        st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']; st.session_state.bracket_tournament = tournament_name
    with st.sidebar.expander("Configure Playoff Brackets"):
        editable_brackets = [b.copy() for b in st.session_state.current_brackets]
        for i, bracket in enumerate(editable_brackets):
            cols = st.columns([4, 2, 2, 1]); bracket['name'] = cols[0].text_input("Name", bracket['name'], key=f"s_name_{i}"); bracket['start'] = cols[1].number_input("Start", bracket['start'], min_value=1, key=f"s_start_{i}"); end_val = bracket['end'] or len(teams); bracket['end'] = cols[2].number_input("End", end_val, min_value=bracket['start'], key=f"s_end_{i}")
            if cols[3].button("🗑️", key=f"s_del_{i}"): st.session_state.current_brackets.pop(i); st.rerun()
        st.session_state.current_brackets = editable_brackets
        if st.button("Save Brackets", type="primary"): save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets}); st.success("Brackets saved!"); st.cache_data.clear()
    cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
    played = [m for m in regular_season_matches if m["date"] in cutoff_dates and m.get("winner") in ("1", "2")]; unplayed = [m for m in regular_season_matches if m not in played]
    st.subheader("Upcoming Matches (What-If Scenarios)"); forced_outcomes = {}
    with st.expander("Set outcomes for upcoming matches", expanded=True):
        if not unplayed: st.info("No matches left to simulate.")
        else:
            for m in sorted(unplayed, key=lambda x: x['date']):
                teamA, teamB, date, bo = m["teamA"], m["teamB"], m["date"], m["bestof"]
                match_key, options = (teamA, teamB, date), get_series_outcome_options(teamA, teamB, bo)
                outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"s_match_{date}_{teamA}")
                forced_outcomes[match_key] = outcome[1]
    sim_results = cached_single_table_sim(tuple(teams), tuple(str(m) for m in played), tuple((m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed), tuple(sorted(forced_outcomes.items())), tuple(frozenset(b.items()) for b in st.session_state.current_brackets), n_sim)
    st.markdown("---"); st.subheader("Results"); col1, col2 = st.columns(2)
    with col1:
        st.write("**Current Standings**"); standings_df = build_standings_table(teams, played)
        st.dataframe(standings_df, use_container_width=True)
    with col2:
        st.write("**Playoff Probabilities**")
        if sim_results is not None and not sim_results.empty:
            if 'Team' in standings_df.columns and not standings_df.empty: st.dataframe(sim_results.set_index('Team').loc[standings_df['Team']].reset_index(), use_container_width=True, hide_index=True)
            else: st.dataframe(sim_results, use_container_width=True, hide_index=True)

def group_dashboard():
    st.header(f"Simulation for {tournament_name} (Group Stage)"); st.button("← Change Tournament Format", on_click=lambda: st.session_state.update(page_view='format_selection'))
    group_config = st.session_state.group_config; groups = group_config.get('groups', {})
    week_blocks = build_week_blocks(sorted(list(set(m["date"] for m in regular_season_matches))))
    st.sidebar.header("Simulation Controls")
    cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[f"Week {i+1}" for i in range(len(week_blocks))], value=f"Week {len(week_blocks)}")
    cutoff_week_idx = int(cutoff_week_label.split(" ")[1]) - 1
    n_sim = st.sidebar.number_input("Simulations:", 1000, 100000, 10000, 1000, key="group_sim_count")
    brackets = load_bracket_config(tournament_name)['brackets']
    cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
    played = [m for m in regular_season_matches if m["date"] in cutoff_dates and m.get("winner") in ("1", "2")]; unplayed = [m for m in regular_season_matches if m not in played]
    st.subheader("Upcoming Matches (What-If Scenarios)"); forced_outcomes = {}
    with st.expander("Set outcomes for upcoming matches", expanded=True):
        if not unplayed: st.info("No matches left to simulate.")
        else:
            for m in sorted(unplayed, key=lambda x: x['date']):
                teamA, teamB, date, bo = m["teamA"], m["teamB"], m["date"], m["bestof"]
                match_key, options = (teamA, teamB, date), get_series_outcome_options(teamA, teamB, bo)
                outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"g_match_{date}_{teamA}")
                forced_outcomes[match_key] = outcome[1]
    sim_results = cached_group_sim(groups, tuple(str(m) for m in played), tuple((m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed), tuple(sorted(forced_outcomes.items())), tuple(frozenset(b.items()) for b in brackets), n_sim)
    st.markdown("---"); st.subheader("Results")
    tab1, tab2 = st.tabs(["Current Standings", "Playoff Probabilities"])
    with tab1:
        group_teams = [team for g in groups.values() for team in g]
        standings_tabs = st.tabs(["Overall"] + sorted(groups.keys()))
        with standings_tabs[0]: st.dataframe(build_standings_table(group_teams, played), use_container_width=True)
        for i, group_name in enumerate(sorted(groups.keys())):
            with standings_tabs[i+1]: st.dataframe(build_standings_table(groups[group_name], played), use_container_width=True)
    with tab2:
        if sim_results is not None and not sim_results.empty:
            prob_tabs = st.tabs(["Overall"] + sorted(groups.keys()))
            with prob_tabs[0]: st.dataframe(sim_results, use_container_width=True, hide_index=True)
            for i, group_name in enumerate(sorted(groups.keys())):
                with prob_tabs[i+1]: st.dataframe(sim_results[sim_results['Group'] == group_name].drop(columns=['Group']), use_container_width=True, hide_index=True)

# --- Page Router ---
if st.session_state.page_view == 'format_selection':
    st.title("🏆 Playoff Odds: Tournament Format")
    st.write(f"How is **{tournament_name}** structured?")
    col1, col2 = st.columns(2)
    if col1.button("Single Table League (e.g., MPL Regular Season)", use_container_width=True): st.session_state.page_view = 'single_table_sim'; st.rerun()
    if col2.button("Group Stage (e.g., MSC, M-Series)", use_container_width=True):
        saved_config = load_group_config(tournament_name)
        if saved_config: st.session_state.group_config = saved_config; st.session_state.page_view = 'group_sim'
        else: st.session_state.page_view = 'group_setup'
        st.rerun()
elif st.session_state.page_view == 'group_setup':
    group_setup_ui()
    if st.button("← Back to Format Selection"): st.session_state.page_view = 'format_selection'; st.rerun()
elif st.session_state.page_view == 'single_table_sim':
    single_table_dashboard()
elif st.session_state.page_view == 'group_sim':
    group_dashboard()
