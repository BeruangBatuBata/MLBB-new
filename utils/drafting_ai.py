import streamlit as st
import pandas as pd
import numpy as np
import joblib
from collections import defaultdict
import itertools
import math

# Load hero profiles and damage types from the main app's session state
# This is a placeholder; we will connect it to the main app's data later
HERO_PROFILES = {}
HERO_DAMAGE_TYPE = {}

def load_data_from_session():
    """Loads necessary data from Streamlit's session state."""
    global HERO_PROFILES, HERO_DAMAGE_TYPE
    HERO_PROFILES = st.session_state.get('hero_profiles', {})
    HERO_DAMAGE_TYPE = st.session_state.get('hero_damage_types', {})


def predict_draft_outcome(blue_picks, red_picks, blue_team, red_team, model_assets):
    """
    Predicts the win probability for a given draft, returning both the overall
    and a team-neutral (draft-only) prediction.
    """
    model = model_assets['model']
    feature_to_idx = model_assets['feature_to_idx']
    roles = model_assets['roles']
    all_heroes = model_assets['all_heroes']
    all_tags = model_assets['all_tags']

    vector_with_teams = np.zeros(len(model_assets['feature_list']))

    # Process Picks (Hero + Role)
    for role, hero in blue_picks.items():
        if hero in all_heroes and f"{hero}_{role}" in feature_to_idx:
            vector_with_teams[feature_to_idx[f"{hero}_{role}"]] = 1
    for role, hero in red_picks.items():
        if hero in all_heroes and f"{hero}_{role}" in feature_to_idx:
            vector_with_teams[feature_to_idx[f"{hero}_{role}"]] = -1

    def get_tags_for_team(team_picks_dict):
        team_tags, team_picks_list = defaultdict(int), list(team_picks_dict.values())
        team_has_frontline = any('Front-line' in p['tags'] for h in team_picks_list if h in HERO_PROFILES for p in HERO_PROFILES[h])
        for hero in team_picks_list:
            profiles = HERO_PROFILES.get(hero)
            if profiles:
                chosen_build = profiles[0]
                if len(profiles) > 1 and not team_has_frontline and any('Tank' in p['build_name'] for p in profiles):
                    chosen_build = next((p for p in profiles if 'Tank' in p['build_name']), profiles[0])
                for tag in chosen_build['tags']:
                    if tag in all_tags: team_tags[tag] += 1
        return team_tags

    blue_tags, red_tags = get_tags_for_team(blue_picks), get_tags_for_team(red_picks)
    for tag, count in blue_tags.items():
        if f"blue_{tag}_count" in feature_to_idx: vector_with_teams[feature_to_idx[f"blue_{tag}_count"]] = count
    for tag, count in red_tags.items():
        if f"red_{tag}_count" in feature_to_idx: vector_with_teams[feature_to_idx[f"red_{tag}_count"]] = count

    # Process Team Identities for the first vector
    if blue_team and blue_team in feature_to_idx: vector_with_teams[feature_to_idx[blue_team]] = 1
    if red_team and red_team in feature_to_idx: vector_with_teams[feature_to_idx[red_team]] = -1

    # --- Calculate first prediction (Overall) ---
    win_prob_overall = model.predict_proba(vector_with_teams.reshape(1, -1))[0][1]

    # --- Calculate second prediction (Draft-Only) ---
    vector_draft_only = vector_with_teams.copy()
    if blue_team and blue_team in feature_to_idx: vector_draft_only[feature_to_idx[blue_team]] = 0
    if red_team and red_team in feature_to_idx: vector_draft_only[feature_to_idx[red_team]] = 0

    win_prob_draft_only = model.predict_proba(vector_draft_only.reshape(1, -1))[0][1]

    return win_prob_overall, win_prob_draft_only


def generate_prediction_explanation(blue_picks, red_picks):
    """
    Generates a detailed, dual-sided analysis for the draft.
    """
    load_data_from_session()

    def analyze_single_team_draft(team_picks):
        results = {'warnings': [], 'strengths': [], 'strategy': [], 'pacing': []}
        if not team_picks: return results

        tags_to_heroes = defaultdict(list)
        all_tags = []
        team_has_frontline = any('Front-line' in p['tags'] for h in team_picks if h in HERO_PROFILES for p in HERO_PROFILES[h])
        for hero in team_picks:
            profiles = HERO_PROFILES.get(hero)
            if profiles:
                chosen_build = profiles[0]
                if len(profiles) > 1 and not team_has_frontline and any('Tank' in p['build_name'] for p in profiles):
                    chosen_build = next((p for p in profiles if 'Tank' in p['build_name']), profiles[0])
                for tag in chosen_build['tags']:
                    all_tags.append(tag)
                    tags_to_heroes[tag].append(hero)

        # Composition Analysis
        if 'Front-line' not in all_tags and 'Initiator' not in all_tags: results['warnings'].append("⚠️ **Lacks Front-line:** Vulnerable to engages.")
        damage_dealers = [h for h in team_picks if HERO_PROFILES.get(h, [{}])[0].get('primary_role', '') in ['Mid', 'Gold', 'Jungle']]
        if len(damage_dealers) >= 2:
            magic_count = sum(1 for h in damage_dealers if 'Magic' in HERO_DAMAGE_TYPE.get(h, []))
            phys_count = sum(1 for h in damage_dealers if 'Physical' in HERO_DAMAGE_TYPE.get(h, []))
            if magic_count == 0 and phys_count > 1: results['warnings'].append("⚠️ **One-dimensional:** Lacks magic damage.")
            elif phys_count == 0 and magic_count > 1: results['warnings'].append("⚠️ **One-dimensional:** Lacks physical damage.")
            elif magic_count > 0 and phys_count > 0: results['strengths'].append("✅ **Balanced Damage:** Good mix of physical and magic damage.")

        # Pacing Analysis
        if len(tags_to_heroes.get('Early Game', [])) >= 2: results['pacing'].append(f"🕒 **Early Game:** Strong early presence with {', '.join(tags_to_heroes['Early Game'])}.")
        if len(tags_to_heroes.get('Late Game', [])) >= 2: results['pacing'].append(f"🕒 **Late Game:** Excellent scaling with {', '.join(tags_to_heroes['Late Game'])}.")

        # Strategy Analysis
        if len(tags_to_heroes.get('Initiator',[])) >= 1 and len(tags_to_heroes.get('AoE Damage',[])) >= 2: results['strategy'].append("📈 **Team Fight:** Strong area damage.")
        if len(tags_to_heroes.get('High Mobility',[])) >= 2 and len(tags_to_heroes.get('Burst',[])) >= 2: results['strategy'].append("📈 **Pick-off:** High mobility and burst.")
        if len(tags_to_heroes.get('Poke',[])) >= 2 and len(tags_to_heroes.get('Long Range',[])) >= 1: results['strategy'].append("📈 **Siege:** Strong poke and zone control.")

        return results

    if len(blue_picks) < 3 and len(red_picks) < 3:
        return {'blue': ["Waiting for more picks..."], 'red': ["Waiting for more picks..."]}

    blue_analysis = analyze_single_team_draft(blue_picks)
    red_analysis = analyze_single_team_draft(red_picks)

    return {
        'blue': (blue_analysis['strengths'] + blue_analysis['pacing'] + blue_analysis['strategy'] + blue_analysis['warnings'])[:5],
        'red': (red_analysis['strengths'] + red_analysis['pacing'] + red_analysis['strategy'] + red_analysis['warnings'])[:5]
    }


def calculate_series_score_probs(p_win_game, series_format=3):
    """
    Calculates the probability of each specific score in a Best-of-X series.
    """
    if p_win_game is None or not (0 <= p_win_game <= 1):
        return {}

    p = p_win_game
    q = 1 - p

    if series_format == 2:
        return {"2-0": p**2, "1-1": 2 * p * q, "0-2": q**2}

    wins_needed = math.ceil((series_format + 1) / 2)
    results = {}

    for losses in range(wins_needed):
        games_played = wins_needed + losses
        if games_played > series_format: continue
        combinations = math.comb(games_played - 1, wins_needed - 1)
        prob_a = combinations * (p ** wins_needed) * (q ** losses)
        results[f"{wins_needed}-{losses}"] = prob_a
        prob_b = combinations * (q ** wins_needed) * (p ** losses)
        results[f"{losses}-{wins_needed}"] = prob_b

    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))

def calculate_ban_suggestions_ML(available_heroes, your_picks_dict, enemy_picks_dict, your_team_name, enemy_team_name, model_assets, is_you_blue):
    threat_scores = []
    position_labels = ["EXP", "Jungle", "Mid", "Gold", "Roam"]
    next_enemy_role = next((role for role in position_labels if role not in enemy_picks_dict), None)
    if not next_enemy_role: return []

    for hero in available_heroes:
        hypothetical_enemy_picks = enemy_picks_dict.copy()
        hypothetical_enemy_picks[next_enemy_role] = hero

        if is_you_blue:
            win_prob_overall, _ = predict_draft_outcome(your_picks_dict, hypothetical_enemy_picks, your_team_name, enemy_team_name, model_assets)
            enemy_win_prob = 1 - win_prob_overall
        else:
            win_prob_overall, _ = predict_draft_outcome(hypothetical_enemy_picks, your_picks_dict, enemy_team_name, your_team_name, model_assets)
            enemy_win_prob = win_prob_overall

        threat_scores.append((hero, enemy_win_prob))

    return sorted(threat_scores, key=lambda x: x[1], reverse=True)


def calculate_pick_suggestions_ML(available_heroes, your_picks_dict, enemy_picks_dict, your_team_name, enemy_team_name, model_assets, is_you_blue, num_picks=1):
    position_labels = ["EXP", "Jungle", "Mid", "Gold", "Roam"]
    open_roles = [role for role in position_labels if role not in your_picks_dict]
    if not open_roles: return []

    single_pick_candidates = []
    for hero in available_heroes:
        hypothetical_your_picks = your_picks_dict.copy()
        hypothetical_your_picks[open_roles[0]] = hero

        if is_you_blue:
            win_prob, _ = predict_draft_outcome(hypothetical_your_picks, enemy_picks_dict, your_team_name, enemy_team_name, model_assets)
        else:
            win_prob_blue, _ = predict_draft_outcome(enemy_picks_dict, hypothetical_your_picks, enemy_team_name, your_team_name, model_assets)
            win_prob = 1 - win_prob_blue
        single_pick_candidates.append((hero, win_prob))

    sorted_candidates = sorted(single_pick_candidates, key=lambda x: x[1], reverse=True)

    if num_picks == 1:
        return sorted_candidates

    if num_picks == 2 and len(open_roles) >= 2:
        top_candidates = [hero for hero, prob in sorted_candidates[:12]]
        if len(top_candidates) < 2: return []

        pair_suggestions = []
        for hero_pair in itertools.combinations(top_candidates, 2):
            hypothetical_your_picks = your_picks_dict.copy()
            hypothetical_your_picks[open_roles[0]] = hero_pair[0]
            hypothetical_your_picks[open_roles[1]] = hero_pair[1]

            if is_you_blue:
                win_prob, _ = predict_draft_outcome(hypothetical_your_picks, enemy_picks_dict, your_team_name, enemy_team_name, model_assets)
            else:
                win_prob_blue, _ = predict_draft_outcome(enemy_picks_dict, hypothetical_your_picks, enemy_team_name, your_team_name, model_assets)
                win_prob = 1 - win_prob_blue

            pair_suggestions.append((hero_pair, win_prob))

        return sorted(pair_suggestions, key=lambda x: x[1], reverse=True)

    return []
