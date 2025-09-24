import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from utils.simulation import (
    get_series_outcome_options, build_standings_table, run_monte_carlo_simulation,
    load_bracket_config, save_bracket_config, build_week_blocks,
    load_group_config, save_group_config, run_monte_carlo_simulation_groups,
    load_tournament_format, save_tournament_format
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
    st.error("No regular season matches found for this feature.")
    st.stop()
teams = sorted(list(set(m["teamA"] for m in regular_season_matches) | set(m["teamB"] for m in regular_season_matches)))

# --- Cached Simulation Functions ---
@st.cache_data(show_spinner="Running single-table simulation...")
def cached_single_table_sim(teams, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim):
    return run_monte_carlo_simulation(list(teams), dict(current_wins), dict(current_diff), list(unplayed_matches), dict(forced_outcomes), [dict(b) for b in brackets], n_sim)

@st.cache_data(show_spinner="Running group stage simulation...")
def cached_group_sim(groups, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim):
    return run_monte_carlo_simulation_groups(groups, dict(current_wins), dict(current_diff), list(unplayed_matches), dict(forced_outcomes), [dict(b) for b in brackets], n_sim)

# --- UI Functions ---
def group_setup_ui():
    st.header(f"Group Configuration for {tournament_name}"); st.write("Assign the teams into their respective groups.")
    if 'group_config' not in st.session_state or not isinstance(st.session_state.group_config, dict):
        st.session_state.group_config = {'groups': {'Group A': [], 'Group B': []}}
    num_groups = st.number_input("Number of Groups", 1, 8, len(st.session_state.group_config.get('groups', {})))
    current_groups = st.session_state.group_config.get('groups', {})
    if len(current_groups) != num_groups:
        new_groups = {}; sorted_keys = sorted(current_groups.keys())
        for i in range(num_groups):
            group_name = sorted_keys[i] if i < len(sorted_keys) else f"Group {chr(65+i)}"; new_groups[group_name] = current_groups.get(group_name, [])
        st.session_state.group_config['groups'] = new_groups; st.rerun()
    st.markdown("---")
    assigned_teams = {team for group in current_groups.values() for team in group}
    unassigned_teams = [team for team in teams if team not in assigned_teams]
    if unassigned_teams: st.warning(f"Unassigned Teams: {', '.join(unassigned_teams)}")
    cols = st.columns(num_groups)
    for i, (group_name, group_teams) in enumerate(current_groups.items()):
        with cols[i]:
            st.subheader(group_name); new_teams = st.multiselect(f"Teams in {group_name}", teams, default=group_teams, key=f"group_{group_name}")
            current_groups[group_name] = new_teams
    if st.button("Save & Continue", type="primary"):
        save_group_config(tournament_name, st.session_state.group_config); st.success("Group configuration saved!")
        st.session_state.page_view = 'group_sim'; st.rerun()

def single_table_dashboard():
    st.header(f"Simulation for {tournament_name} (Single Table)")
    st.button("← Change Tournament Format", on_click=lambda: st.session_state.update(page_view='format_selection'))
    
    # --- Data Prep ---
    week_blocks = build_week_blocks(sorted(list(set(m["date"] for m in regular_season_matches))))
    
    # --- Sidebar UI ---
    st.sidebar.header("Simulation Controls")
    week_options = {f"Week {i+1} ({wk[0]} to {wk[-1]})": i for i, wk in enumerate(week_blocks)}
    week_options["Pre-Season (Week 0)"] = -1
    sorted_week_options = sorted(week_options.items(), key=lambda item: item[1])
    cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[opt[0] for opt in sorted_week_options], value=sorted_week_options[-1][0])
    cutoff_week_idx = week_options[cutoff_week_label]
    n_sim = st.sidebar.number_input("Simulations:", 1000, 100000, 10000, 1000, key="single_sim_count")
    
    if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
        st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']
        st.session_state.bracket_tournament = tournament_name
        
    with st.sidebar.expander("Configure Playoff Brackets"):
        editable_brackets = [b.copy() for b in st.session_state.current_brackets]
        for i, bracket in enumerate(editable_brackets):
            cols = st.columns([4, 2, 2, 1])
            bracket['name'] = cols[0].text_input("Name", value=bracket.get('name', ''), key=f"s_name_{i}")
            bracket['start'] = cols[1].number_input("Start", value=bracket.get('start', 1), min_value=1, key=f"s_start_{i}")
            end_val = bracket.get('end') or len(teams)
            bracket['end'] = cols[2].number_input("End", value=end_val, min_value=bracket.get('start', 1), key=f"s_end_{i}")
            if cols[3].button("🗑️", key=f"s_del_{i}"):
                st.session_state.current_brackets.pop(i)
                st.rerun()
        st.session_state.current_brackets = editable_brackets
        if st.button("Save Brackets", type="primary"):
            save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
            st.success("Brackets saved!")
            st.cache_data.clear()
            
    # --- Data Processing ---
    cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
    played = [m for m in regular_season_matches if m["date"] in cutoff_dates and m.get("winner") in ("1", "2")]
    unplayed = [m for m in regular_season_matches if m not in played]

    # --- "What-If" Scenarios UI (with Weekly Grouping Restored) ---
    st.subheader("Upcoming Matches (What-If Scenarios)")
    forced_outcomes = {}
    
    matches_by_week = defaultdict(list)
    for match in unplayed:
        for week_idx, week_dates in enumerate(week_blocks):
            if match['date'] in week_dates:
                matches_by_week[week_idx].append(match)
                break

    if not matches_by_week:
        st.info("No upcoming matches to simulate for the selected cutoff week.")
    else:
        sorted_weeks = sorted(matches_by_week.keys())
        for i, week_idx in enumerate(sorted_weeks):
            week_label = f"Week {week_idx + 1} ({week_blocks[week_idx][0]} to {week_blocks[week_idx][-1]})"
            with st.expander(week_label, expanded=False):
                for m in sorted(matches_by_week[week_idx], key=lambda x: x['date']):
                    teamA, teamB, date, bo = m["teamA"], m["teamB"], m["date"], m["bestof"]
                    match_key, options = (teamA, teamB, date), get_series_outcome_options(teamA, teamB, bo)
                    outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"s_match_{date}_{teamA}_{teamB}")
                    forced_outcomes[match_key] = outcome[1]

    # --- Simulation Call ---
    current_wins, current_diff = defaultdict(int), defaultdict(int)
    for m in played:
        winner_idx = int(m["winner"]) - 1
        teams_in_match = [m["teamA"], m["teamB"]]
        winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
        current_wins[winner] += 1
        s_w, s_l = (m["scoreA"], m["scoreB"]) if winner_idx == 0 else (m["scoreB"], m["scoreA"])
        current_diff[winner] += s_w - s_l
        current_diff[loser] += s_l - s_w
        
    sim_results = cached_single_table_sim(tuple(teams), tuple(sorted(current_wins.items())), tuple(sorted(current_diff.items())), tuple((m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed), tuple(sorted(forced_outcomes.items())), tuple(frozenset(b.items()) for b in st.session_state.current_brackets), n_sim)
    
    # --- Display Results ---
    st.markdown("---")
    st.subheader("Results")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Current Standings**")
        standings_df = build_standings_table(teams, played)
        st.dataframe(standings_df, use_container_width=True)
    with col2:
        st.write("**Playoff Probabilities**")
        if sim_results is not None and not sim_results.empty:
            if 'Team' in standings_df.columns and not standings_df.empty:
                st.dataframe(sim_results.set_index('Team').loc[standings_df['Team']].reset_index(), use_container_width=True, hide_index=True)
            else:
                st.dataframe(sim_results, use_container_width=True, hide_index=True)

def group_dashboard():
    st.header(f"Simulation for {tournament_name} (Group Stage)")
    st.button("← Change Tournament Format", on_click=lambda: st.session_state.update(page_view='format_selection'))
    
    # --- Data Prep ---
    group_config = st.session_state.group_config
    groups = group_config.get('groups', {})
    week_blocks = build_week_blocks(sorted(list(set(m["date"] for m in regular_season_matches))))
    
    # --- Sidebar ---
    st.sidebar.header("Simulation Controls")
    cutoff_week_label = st.sidebar.select_slider("Select Cutoff Week:", options=[f"Week {i+1}" for i in range(len(week_blocks))], value=f"Week {len(week_blocks)}")
    cutoff_week_idx = int(cutoff_week_label.split(" ")[1]) - 1
    n_sim = st.sidebar.number_input("Simulations:", 1000, 100000, 10000, 1000, key="group_sim_count")
    
    # --- ADD THIS ENTIRE BLOCK TO ADD THE MISSING FEATURE ---
    if 'current_brackets' not in st.session_state or st.session_state.get('bracket_tournament') != tournament_name:
        st.session_state.current_brackets = load_bracket_config(tournament_name)['brackets']
        st.session_state.bracket_tournament = tournament_name
    
    with st.sidebar.expander("Configure Playoff Brackets"):
        editable_brackets = [b.copy() for b in st.session_state.current_brackets]
        for i, bracket in enumerate(editable_brackets):
            cols = st.columns([4, 2, 2, 1])
            bracket['name'] = cols[0].text_input("Name", bracket.get('name', ''), key=f"g_name_{i}")
            bracket['start'] = cols[1].number_input("Start", value=bracket.get('start', 1), min_value=1, key=f"g_start_{i}")
            end_val = bracket.get('end') or len(teams)
            bracket['end'] = cols[2].number_input("End", value=end_val, min_value=bracket.get('start', 1), key=f"g_end_{i}")
            if cols[3].button("🗑️", key=f"g_del_{i}"):
                st.session_state.current_brackets.pop(i)
                st.rerun()
        st.session_state.current_brackets = editable_brackets
        if st.button("Save Brackets", type="primary", key="g_save_brackets"):
            save_bracket_config(tournament_name, {"brackets": st.session_state.current_brackets})
            st.success("Brackets saved!")
            st.cache_data.clear()
    # --- END OF ADDITION ---

    with st.sidebar.expander("Configure Groups"):
        st.write("Edit team assignments for each group.")
        editable_groups = st.session_state.group_config.get('groups', {})
        for group_name, group_teams in editable_groups.items():
            new_teams = st.multiselect(f"Teams in {group_name}", options=teams, default=group_teams, key=f"edit_group_{group_name}")
            editable_groups[group_name] = new_teams
        if st.button("Save Group Changes"):
            st.session_state.group_config['groups'] = editable_groups
            save_group_config(tournament_name, st.session_state.group_config)
            st.success("Group configuration updated!")
            st.cache_data.clear()
            st.rerun()

    # --- Data Processing & "What-If" (The rest of the function remains the same) ---
    brackets = st.session_state.current_brackets # Use the potentially edited brackets
    cutoff_dates = set(d for i in range(cutoff_week_idx + 1) for d in week_blocks[i]) if cutoff_week_idx >= 0 else set()
    played = [m for m in regular_season_matches if m["date"] in cutoff_dates and m.get("winner") in ("1", "2")]
    unplayed = [m for m in regular_season_matches if m not in played]
    
    st.subheader("Upcoming Matches (What-If Scenarios)")
    forced_outcomes = {}
    with st.expander("Set outcomes for upcoming matches", expanded=True):
        if not unplayed: st.info("No matches left to simulate.")
        else:
            for m in sorted(unplayed, key=lambda x: x['date']):
                teamA, teamB, date, bo = m["teamA"], m["teamB"], m["date"], m["bestof"]
                match_key, options = (teamA, teamB, date), get_series_outcome_options(teamA, teamB, bo)
                outcome = st.selectbox(f"{teamA} vs {teamB} ({date})", options, format_func=lambda x: x[0], key=f"g_match_{date}_{teamA}_{teamB}")
                forced_outcomes[match_key] = outcome[1]
    
    current_wins, current_diff = defaultdict(int), defaultdict(int)
    for m in played:
        winner_idx = int(m["winner"]) - 1
        teams_in_match = [m["teamA"], m["teamB"]]
        winner, loser = teams_in_match[winner_idx], teams_in_match[1 - winner_idx]
        current_wins[winner] += 1
        s_w, s_l = (m["scoreA"], m["scoreB"]) if winner_idx == 0 else (m["scoreB"], m["scoreA"])
        current_diff[winner] += s_w - s_l
        current_diff[loser] += s_l - s_w
    sim_results = cached_group_sim(groups, tuple(sorted(current_wins.items())), tuple(sorted(current_diff.items())), tuple((m["teamA"], m["teamB"], m["date"], m["bestof"]) for m in unplayed), tuple(sorted(forced_outcomes.items())), tuple(frozenset(b.items()) for b in brackets), n_sim)
    
    st.markdown("---"); st.subheader("Results")
    result_tabs = st.tabs(["Overall"] + sorted(groups.keys()))
    with result_tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Current Standings by Group**")
            for group_name in sorted(groups.keys()):
                st.write(f"**{group_name}**"); standings_df = build_standings_table(groups[group_name], played)
                st.dataframe(standings_df, use_container_width=True)
        with col2:
            st.write("**Playoff Probabilities by Group**")
            if sim_results is not None and not sim_results.empty:
                for group_name in sorted(groups.keys()):
                    st.write(f"**{group_name}**"); group_probs = sim_results[sim_results['Group'] == group_name].drop(columns=['Group'])
                    st.dataframe(group_probs, use_container_width=True, hide_index=True)
    for i, group_name in enumerate(sorted(groups.keys())):
        with result_tabs[i+1]:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Current Standings ({group_name})**"); standings_df = build_standings_table(groups[group_name], played)
                st.dataframe(standings_df, use_container_width=True)
            with col2:
                st.write(f"**Playoff Probabilities ({group_name})**")
                if sim_results is not None and not sim_results.empty:
                    group_probs = sim_results[sim_results['Group'] == group_name].drop(columns=['Group'])
                    st.dataframe(group_probs, use_container_width=True, hide_index=True)

# --- Page Router ---
# On first load for a tournament, try to load the saved format
if 'page_view' not in st.session_state or st.session_state.get('active_tournament') != tournament_name:
    st.session_state.active_tournament = tournament_name
    saved_format = load_tournament_format(tournament_name)
    if saved_format == 'single_table':
        st.session_state.page_view = 'single_table_sim'
    elif saved_format == 'group':
        st.session_state.page_view = 'group_sim'
        # Also pre-load group config if it exists
        saved_group_config = load_group_config(tournament_name)
        if saved_group_config:
            st.session_state.group_config = saved_group_config
    else:
        st.session_state.page_view = 'format_selection'

# Now, display the correct view based on the state
if st.session_state.page_view == 'format_selection':
    st.title("🏆 Playoff Odds: Tournament Format")
    st.write(f"How is **{tournament_name}** structured?")
    col1, col2 = st.columns(2)
    if col1.button("Single Table League", use_container_width=True):
        save_tournament_format(tournament_name, 'single_table') # Save the choice
        st.session_state.page_view = 'single_table_sim'; st.rerun()
    if col2.button("Group Stage", use_container_width=True):
        save_tournament_format(tournament_name, 'group') # Save the choice
        # Go to setup if no config exists, otherwise go straight to the sim
        saved_config = load_group_config(tournament_name)
        if saved_config: st.session_state.group_config = saved_config; st.session_state.page_view = 'group_sim'
        else: st.session_state.page_view = 'group_setup'
        st.rerun()

elif st.session_state.page_view == 'group_setup':
    group_setup_ui()
    if st.button("← Back to Format Selection"):
        st.session_state.page_view = 'format_selection'; st.rerun()

elif st.session_state.page_view == 'single_table_sim':
    single_table_dashboard()

elif st.session_state.page_view == 'group_sim':
    group_dashboard()
