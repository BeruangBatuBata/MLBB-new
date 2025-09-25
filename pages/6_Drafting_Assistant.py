import streamlit as st
import pandas as pd
import joblib
from collections import defaultdict
from utils.drafting_ai import predict_draft_outcome, get_all_hero_names, calculate_series_score_probs
from utils.data_processing import HERO_PROFILES, HERO_DAMAGE_TYPE

st.set_page_config(layout="wide", page_title="Drafting Assistant")

def generate_prediction_explanation(blue_picks, red_picks, HERO_PROFILES, HERO_DAMAGE_TYPE):
    """Generates a detailed, dual-sided analysis for the draft."""
    def analyze_single_team_draft(team_picks, enemy_picks):
        results = {'warnings': [], 'strengths': [], 'strategy': [], 'pacing': []}
        if not team_picks: return results
        tags_to_heroes = defaultdict(list); all_tags = []
        for hero in team_picks:
            profiles = HERO_PROFILES.get(hero)
            if profiles:
                for tag in profiles[0]['tags']: all_tags.append(tag); tags_to_heroes[tag].append(hero)
        if 'Front-line' not in all_tags and 'Initiator' not in all_tags: results['warnings'].append("⚠️ **Lacks a durable front-line.**")
        damage_dealers = [h for h in team_picks if HERO_PROFILES.get(h, [{}])[0].get('primary_role', '') in ['Mid', 'Gold', 'Jungle']]
        if len(damage_dealers) >= 2:
            magic_count = sum(1 for h in damage_dealers if 'Magic' in HERO_DAMAGE_TYPE.get(h, []))
            phys_count = sum(1 for h in damage_dealers if 'Physical' in HERO_DAMAGE_TYPE.get(h, []))
            if magic_count == 0 and phys_count > 1: results['warnings'].append("⚠️ **Lacks magic damage.**")
            elif phys_count == 0 and magic_count > 1: results['warnings'].append("⚠️ **Lacks physical damage.**")
            else: results['strengths'].append("✅ **Balanced damage profile.**")
        if len(tags_to_heroes.get('Early Game', [])) >= 2: results['pacing'].append(f"🕒 **Pacing:** Strong Early Game.")
        if len(tags_to_heroes.get('Late Game', [])) >= 2: results['pacing'].append(f"🕒 **Pacing:** Strong Late Game Scaling.")
        if len(tags_to_heroes.get('Initiator',[])) >= 1 and len(tags_to_heroes.get('AoE Damage',[])) >= 2: results['strategy'].append(f"📈 **Strategy:** Strong Team Fighting.")
        if len(tags_to_heroes.get('High Mobility',[])) >= 2 and len(tags_to_heroes.get('Burst',[])) >= 2: results['strategy'].append(f"📈 **Strategy:** Excellent Pick-off.")
        if len(tags_to_heroes.get('Poke',[])) >= 2 and len(tags_to_heroes.get('Long Range',[])) >= 1: results['strategy'].append(f"📈 **Strategy:** Strong Poke & Siege.")
        return results

    blue_analysis = analyze_single_team_draft(blue_picks, red_picks)
    red_analysis = analyze_single_team_draft(red_picks, blue_picks)
    return {
        'blue': (blue_analysis['warnings'] + blue_analysis['pacing'] + blue_analysis['strategy'] + blue_analysis['strengths']),
        'red': (red_analysis['warnings'] + red_analysis['pacing'] + red_analysis['strategy'] + red_analysis['strengths'])
    }

st.title("🎯 Professional Drafting Assistant")

try:
    model_assets = joblib.load('draft_predictor.joblib')
except FileNotFoundError:
    st.error("Fatal Error: 'draft_predictor.joblib' not found. Please train the model on the homepage first.")
    st.stop()

# --- DYNAMIC UI DATA ---
ALL_HERO_NAMES = get_all_hero_names(HERO_PROFILES)
if 'pooled_matches' in st.session_state and st.session_state['pooled_matches']:
    all_teams_set = {opp.get("name", "").strip() for match in st.session_state['pooled_matches'] for opp in match.get("match2opponents", []) if opp.get("name", "").strip()}
    ALL_TEAMS = sorted(list(all_teams_set))
else:
    st.warning("Please load tournament data on the homepage to populate the team lists.", icon="👈")
    ALL_TEAMS = model_assets['all_teams'] # Fallback to model's team list

hero_options = ["(None)"] + ALL_HERO_NAMES
team_options = ["(None)"] + ALL_TEAMS

# --- DRAFT STATE ---
roles = model_assets['roles']
st.session_state.setdefault('blue_picks', {role: "(None)" for role in roles})
st.session_state.setdefault('red_picks', {role: "(None)" for role in roles})
st.session_state.setdefault('blue_bans', ["(None)"] * 5)
st.session_state.setdefault('red_bans', ["(None)"] * 5)

# --- HEADER ---
st.markdown("Select teams, then fill in the picks and bans as they happen to see a real-time win probability prediction.")
st.markdown("---")
prediction_placeholder = st.empty()
explanation_placeholder = st.empty()

# --- DRAFTING UI ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Blue Side")
    st.selectbox("Blue Team", options=team_options, key="blue_team")
    st.write("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        ban_cols[i].selectbox(f"B{i+1}", options=hero_options, key=f"blue_ban_{i}")
    st.write("**Picks**")
    for role in roles:
        st.selectbox(role, options=hero_options, key=f"blue_pick_{role}")

with col2:
    st.subheader("Red Side")
    st.selectbox("Red Team", options=team_options, key="red_team")
    st.write("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        ban_cols[i].selectbox(f"B{i+1}", options=hero_options, key=f"red_ban_{i}")
    st.write("**Picks**")
    for role in roles:
        st.selectbox(role, options=hero_options, key=f"red_pick_{role}")

# --- PREDICTION LOGIC (RUNS ON EVERY INTERACTION) ---
s = st.session_state
blue_team, red_team = s.blue_team, s.red_team
blue_picks = {role: s[f"blue_pick_{role}"] for role in roles if s[f"blue_pick_{role}"] != "(None)"}
red_picks = {role: s[f"red_pick_{role}"] for role in roles if s[f"red_pick_{role}"] != "(None)"}

if blue_team != "(None)" and red_team != "(None)" and blue_picks and red_picks:
    win_prob_blue = predict_draft_outcome(blue_picks, red_picks, blue_team, red_team, model_assets, HERO_PROFILES)
    win_prob_red = 1 - win_prob_blue
    
    with prediction_placeholder.container():
        st.subheader("Live Win Probability (Single Game)")
        blue_pct, red_pct = int(win_prob_blue * 100), int(win_prob_red * 100)
        st.markdown(f"""
        <div style="display: flex; width: 100%; height: 32px; font-weight: bold; font-size: 16px; border-radius: 5px; overflow: hidden;">
            <div style="width: {blue_pct}%; background-color: #4299e1; color: white; display: flex; align-items: center; justify-content: center;">{blue_pct}%</div>
            <div style="width: {red_pct}%; background-color: #f56565; color: white; display: flex; align-items: center; justify-content: center;">{red_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

        series_probs = calculate_series_score_probs(win_prob_blue, series_format=3)
        if series_probs:
            st.write("**Best-of-3 Series Score Probability**")
            series_text = ""
            for score, prob in series_probs.items():
                s1, s2 = map(int, score.split('-'))
                winner = f"<span style='color:#4299e1;'>{blue_team}</span>" if s1 > s2 else f"<span style='color:#f56565;'>{red_team}</span>"
                series_text += f"&nbsp;&nbsp;&nbsp;•&nbsp; {winner} wins {score}: **{prob:.1%}**"
            st.markdown(series_text, unsafe_allow_html=True)
    
    with explanation_placeholder.container():
        st.markdown("---")
        st.subheader("Draft Analysis")
        explanation = generate_prediction_explanation(list(blue_picks.values()), list(red_picks.values()), HERO_PROFILES, HERO_DAMAGE_TYPE)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Blue Side Analysis**")
            for point in explanation['blue']: st.markdown(f"- {point}")
        with col2:
            st.write("**Red Side Analysis**")
            for point in explanation['red']: st.markdown(f"- {point}")
else:
    prediction_placeholder.info("Prediction will appear here once both teams and at least one pick for each side are selected.")
