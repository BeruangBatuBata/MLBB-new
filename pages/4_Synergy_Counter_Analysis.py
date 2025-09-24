import streamlit as st
import pandas as pd
from utils.analysis_functions import analyze_synergy_combos, analyze_counter_combos
from utils.plotting import plot_synergy_bar_chart, plot_counter_heatmap

st.set_page_config(layout="wide", page_title="Synergy & Counter Analysis")

st.title("🤝 Synergy & Counter Analysis")

if 'pooled_matches' not in st.session_state or not st.session_state['pooled_matches']:
    st.warning("Please select and load tournament data on the homepage first.")
    st.stop()

pooled_matches = st.session_state['pooled_matches']

# --- Sidebar Controls ---
st.sidebar.header("Analysis Controls")

# Get unique lists of teams and heroes
all_teams = sorted(list(set(opp.get('name','').strip() for m in pooled_matches for opp in m.get("match2opponents", []) if opp.get('name'))))
all_heroes = sorted(list(set(p["champion"] for m in pooled_matches for g in m.get("match2games", []) for o in g.get("opponents", []) for p in o.get("players", []) if isinstance(p, dict) and "champion" in p)))

analysis_mode = st.sidebar.radio(
    "Select Analysis Mode:",
    ["Synergy (Best Pairs)", "Anti-Synergy (Worst Pairs)", "Counters"]
)

team_filter = st.sidebar.selectbox("Filter by Team:", ["All Teams"] + all_teams)
min_games = st.sidebar.slider("Minimum Games Played Together:", 1, 20, 5)
top_n = st.sidebar.slider("Number of Results to Show:", 5, 50, 15)

# --- Main Page Logic & Display ---
if analysis_mode in ["Synergy (Best Pairs)", "Anti-Synergy (Worst Pairs)"]:
    find_anti = (analysis_mode == "Anti-Synergy (Worst Pairs)")
    
    focus_hero = st.sidebar.selectbox("Focus on a specific Hero (optional):", ["All Heroes"] + all_heroes)
    focus_hero = None if focus_hero == "All Heroes" else focus_hero
    
    with st.spinner("Analyzing hero synergies..."):
        df_results = analyze_synergy_combos(pooled_matches, team_filter, min_games, top_n, find_anti, focus_hero)

    st.header(f"Top {top_n} {analysis_mode}")
    df_display = df_results.reset_index(drop=True)
    df_display.index += 1 # Add this
    st.dataframe(df_display, use_container_width=True)
    
    title = f"Win Rate of {'Worst' if find_anti else 'Best'} Hero Duos"
    if focus_hero:
        title += f" with {focus_hero}"
        
    plot_synergy_bar_chart(df_results.sort_values("Win Rate (%)", ascending=find_anti), title, focus_hero=focus_hero)

elif analysis_mode == "Counters":
    focus_on_team_picks = True
    if team_filter != "All Teams":
        focus_on_team_picks = st.sidebar.radio(
            f"Focus on matchups where:",
            [f"{team_filter} picks the 'Ally Hero'", f"{team_filter} plays against the 'Ally Hero'"],
            index=0
        ) == f"{team_filter} picks the 'Ally Hero'"

    with st.spinner("Analyzing hero counters..."):
        df_results = analyze_counter_combos(pooled_matches, min_games, top_n, team_filter, focus_on_team_picks)

    st.header(f"Top {top_n} Counter Matchups")
    df_display = df_results.reset_index(drop=True)
    df_display.index += 1 # Add this
    st.dataframe(df_display, use_container_width=True)
    
    title = f"Win Rate: Ally Hero vs. Enemy Hero"
    if team_filter != "All Teams":
        title += f" (Perspective: {team_filter})"
        
    plot_counter_heatmap(df_results, title)
