import streamlit as st
from utils.drafting_ai import (
    predict_draft_outcome,
    generate_prediction_explanation,
    calculate_series_score_probs,
    calculate_ban_suggestions_ML,
    calculate_pick_suggestions_ML
)
import joblib

st.set_page_config(layout="wide")

st.title("🎯 Professional Drafting Assistant")

# --- This is the corrected guard clause, identical to other working pages ---
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please select one or more tournaments from the main page and click 'Load Data'.")
    st.stop()
# --- End of fix ---


def initialize_draft_state():
    """Initializes the session state for the draft."""
    if 'draft_initialized' not in st.session_state:
        st.session_state.blue_bans = [None] * 5
        st.session_state.red_bans = [None] * 5
        st.session_state.blue_picks = {role: None for role in st.session_state.position_labels}
        st.session_state.red_picks = {role: None for role in st.session_state.position_labels}
        st.session_state.blue_team = None
        st.session_state.red_team = None
        st.session_state.draft_initialized = True

def get_draft_phase():
    """Determines the current phase and turn of the draft."""
    b_bans = sum(1 for b in st.session_state.blue_bans if b)
    r_bans = sum(1 for b in st.session_state.red_bans if b)
    b_picks = sum(1 for p in st.session_state.blue_picks.values() if p)
    r_picks = sum(1 for p in st.session_state.red_picks.values() if p)

    total_bans = b_bans + r_bans
    total_picks = b_picks + r_picks

    if total_bans < 6: return "BAN", ['B', 'R', 'B', 'R', 'B', 'R'][total_bans]
    if total_picks < 6: return "PICK", ['B', 'R', 'R', 'B', 'B', 'R'][total_picks]
    if total_bans < 10: return "BAN", ['R', 'B', 'R', 'B'][total_bans - 6]
    if total_picks < 10: return "PICK", ['R', 'B', 'B', 'R'][total_picks - 6]

    return "DRAFT COMPLETE", None


def render_suggestion_box(team_color, phase, turn):
    """Renders the AI suggestion box for the active team."""
    if (team_color == 'blue' and turn != 'B') or (team_color == 'red' and turn != 'R'):
        return

    st.markdown(f"**AI Suggestions for {'Blue' if team_color == 'blue' else 'Red'} Team**")
    
    # Prepare data for AI functions
    available_heroes = [h for h in st.session_state.all_heroes if h not in st.session_state.taken_heroes]
    your_picks = st.session_state.blue_picks if team_color == 'blue' else st.session_state.red_picks
    enemy_picks = st.session_state.red_picks if team_color == 'blue' else st.session_state.blue_picks
    your_team = st.session_state.blue_team
    enemy_team = st.session_state.red_team
    is_blue = (team_color == 'blue')

    if phase == "BAN":
        with st.spinner("Calculating ban threats..."):
            suggestions = calculate_ban_suggestions_ML(available_heroes, your_picks, enemy_picks, your_team, enemy_team, st.session_state.model_assets, is_blue)
        for i, (hero, threat) in enumerate(suggestions[:5]):
            st.button(f"Ban {hero} ({threat:.1%} Threat)", key=f"{team_color}_ban_{i}", on_click=handle_suggestion_click, args=(hero, "ban", team_color))

    elif phase == "PICK":
        pick_order = ['B', 'R', 'R', 'B', 'B', 'R', 'R', 'B', 'B', 'R']
        total_picks = sum(1 for p in your_picks.values() if p) + sum(1 for p in enemy_picks.values() if p)
        is_double_pick = (total_picks < len(pick_order) - 1 and pick_order[total_picks] == pick_order[total_picks+1])
        num_picks = 2 if is_double_pick else 1

        with st.spinner(f"Simulating {num_picks} pick(s)..."):
            suggestions = calculate_pick_suggestions_ML(available_heroes, your_picks, enemy_picks, your_team, enemy_team, st.session_state.model_assets, is_blue, num_picks)

        if num_picks == 1:
            for i, (hero, prob) in enumerate(suggestions[:5]):
                st.button(f"Pick {hero} (→ {prob:.1%} Win)", key=f"{team_color}_pick_{i}", on_click=handle_suggestion_click, args=(hero, "pick", team_color))
        else:
            st.markdown("_Suggestion for double pick:_")
            for i, (hero_pair, prob) in enumerate(suggestions[:3]):
                 st.button(f"Pick {hero_pair[0]} & {hero_pair[1]} (→ {prob:.1%} Win)", key=f"{team_color}_pick_pair_{i}", on_click=handle_suggestion_click, args=(hero_pair[0], "pick", team_color))


def handle_suggestion_click(hero, action, team_color):
    """Callback to apply a suggestion to the draft state."""
    if action == "ban":
        ban_list = st.session_state.blue_bans if team_color == 'blue' else st.session_state.red_bans
        if None in ban_list:
            ban_list[ban_list.index(None)] = hero
    elif action == "pick":
        pick_dict = st.session_state.blue_picks if team_color == 'blue' else st.session_state.red_picks
        open_role = next((role for role, hero in pick_dict.items() if hero is None), None)
        if open_role:
            pick_dict[open_role] = hero

# --- Main App UI ---

# Initialization
initialize_draft_state()
try:
    if 'model_assets' not in st.session_state:
        st.session_state.model_assets = joblib.load('draft_predictor.joblib')
except FileNotFoundError:
    st.error("Fatal: `draft_predictor.joblib` not found. Please ensure the model is trained and available in the root directory.")
    st.stop()


# --- Header and Controls ---
phase, turn = get_draft_phase()
color = "blue" if turn == 'B' else "red" if turn == 'R' else "green"
st.markdown(f"### <span style='color:{color};'>{'Blue' if turn == 'B' else 'Red' if turn == 'R' else ''} Turn ({phase})</span>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.session_state.blue_team = st.selectbox("Blue Team", options=[None] + st.session_state.all_teams, key='sb_blue_team')
with col2:
    st.session_state.red_team = st.selectbox("Red Team", options=[None] + st.session_state.all_teams, key='sb_red_team')
with col3:
    st.selectbox("Series Format", options=[1, 2, 3, 5, 7], format_func=lambda x: f"Best-of-{x}", key='sb_series_format')


# --- Win Probability and Analysis ---
st.session_state.taken_heroes = set(st.session_state.blue_bans + st.session_state.red_bans + list(st.session_state.blue_picks.values()) + list(st.session_state.red_picks.values())) - {None}
available_heroes = [h for h in st.session_state.all_heroes if h not in st.session_state.taken_heroes]

win_prob_overall, win_prob_draft = predict_draft_outcome(st.session_state.blue_picks, st.session_state.red_picks, st.session_state.blue_team, st.session_state.red_team, st.session_state.model_assets)

st.progress(win_prob_overall, text=f"Overall Win Prediction: Blue {win_prob_overall:.1%} vs Red {1-win_prob_overall:.1%}")
st.progress(win_prob_draft, text=f"Draft-Only Prediction: Blue {win_prob_draft:.1%} vs Red {1-win_prob_draft:.1%}")

explanation = generate_prediction_explanation(list(st.session_state.blue_picks.values()), list(st.session_state.red_picks.values()))

with st.expander("Show/Hide Detailed Draft Analysis"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Blue Team Analysis")
        for point in explanation['blue']:
            st.markdown(f"- {point}")
    with col2:
        st.markdown("##### Red Team Analysis")
        for point in explanation['red']:
            st.markdown(f"- {point}")

st.markdown("---")


# --- Drafting Area ---
blue_col, red_col = st.columns(2)

with blue_col:
    st.markdown("<h4 style='color:blue;'>Blue Team Draft</h4>", unsafe_allow_html=True)
    st.markdown("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        st.session_state.blue_bans[i] = ban_cols[i].selectbox(f"B{i+1}", [None] + available_heroes, key=f"blue_ban_{i}", index=([None] + available_heroes).index(st.session_state.blue_bans[i]) if st.session_state.blue_bans[i] in available_heroes else 0, label_visibility="collapsed")

    st.markdown("**Picks**")
    for i, role in enumerate(st.session_state.position_labels):
        st.session_state.blue_picks[role] = st.selectbox(role, [None] + available_heroes, key=f"blue_pick_{i}", index=([None] + available_heroes).index(st.session_state.blue_picks[role]) if st.session_state.blue_picks[role] in available_heroes else 0)

    render_suggestion_box('blue', phase, turn)


with red_col:
    st.markdown("<h4 style='color:red;'>Red Team Draft</h4>", unsafe_allow_html=True)
    st.markdown("**Bans**")
    ban_cols = st.columns(5)
    for i in range(5):
        st.session_state.red_bans[i] = ban_cols[i].selectbox(f"B{i+1}", [None] + available_heroes, key=f"red_ban_{i}", index=([None] + available_heroes).index(st.session_state.red_bans[i]) if st.session_state.red_bans[i] in available_heroes else 0, label_visibility="collapsed")
        
    st.markdown("**Picks**")
    for i, role in enumerate(st.session_state.position_labels):
        st.session_state.red_picks[role] = st.selectbox(role, [None] + available_heroes, key=f"red_pick_{i}", index=([None] + available_heroes).index(st.session_state.red_picks[role]) if st.session_state.red_picks[role] in available_heroes else 0)

    render_suggestion_box('red', phase, turn)
