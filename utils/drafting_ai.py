# In utils/drafting_ai.py

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from collections import defaultdict
import itertools

# --- Helper function to get all hero names ---
def get_all_hero_names(HERO_PROFILES):
    return sorted(list(HERO_PROFILES.keys()))

def train_and_save_prediction_model(matches, HERO_PROFILES, HERO_DAMAGE_TYPE, model_filename='draft_predictor.joblib'):
    """
    Trains an advanced XGBoost model using Hero+Role, Ban, and Compositional features.
    Saves the trained model and necessary assets.
    """
    all_heroes = sorted(list(set(p['champion'] for m in matches for g in m.get('match2games', []) for o in g.get('opponents', []) for p in o.get('players', []) if 'champion' in p)))
    all_teams = sorted(list(set(o['name'] for m in matches for o in m.get('match2opponents', []) if 'name' in o)))
    roles = ["EXP", "Jungle", "Mid", "Gold", "Roam"]
    all_tags = sorted(list(set(tag for hero_profiles in HERO_PROFILES.values() for profile in hero_profiles for tag in profile['tags'])))
    
    feature_list = []
    for hero in all_heroes:
        for role in roles: feature_list.append(f"{hero}_{role}")
    for hero in all_heroes: feature_list.append(f"{hero}_Ban")
    feature_list.extend(all_teams)
    for tag in all_tags: feature_list.append(f"blue_{tag}_count")
    for tag in all_tags: feature_list.append(f"red_{tag}_count")
    
    feature_to_idx = {feature: i for i, feature in enumerate(feature_list)}
    
    X, y = [], []
    for match in matches:
        match_teams = [o.get('name') for o in match.get('match2opponents', [])]
        if len(match_teams) != 2 or not all(t in feature_to_idx for t in match_teams): continue
        for game in match.get('match2games', []):
            extradata = game.get('extradata', {})
            if len(game.get('opponents', [])) != 2 or game.get('winner') not in ['1', '2'] or not extradata: continue
            vector = np.zeros(len(feature_list))
            blue_picks_list, red_picks_list = [], []
            for i, role in enumerate(roles, 1):
                blue_hero, red_hero = extradata.get(f'team1champion{i}'), extradata.get(f'team2champion{i}')
                if blue_hero in all_heroes:
                    vector[feature_to_idx[f"{blue_hero}_{role}"]] = 1
                    blue_picks_list.append(blue_hero)
                if red_hero in all_heroes:
                    vector[feature_to_idx[f"{red_hero}_{role}"]] = -1
                    red_picks_list.append(red_hero)
            for i in range(1, 6):
                blue_ban, red_ban = extradata.get(f'team1ban{i}'), extradata.get(f'team2ban{i}')
                if blue_ban in all_heroes: vector[feature_to_idx[f"{blue_ban}_Ban"]] = 1
                if red_ban in all_heroes: vector[feature_to_idx[f"{red_ban}_Ban"]] = -1
            
            def get_tags_for_team(team_picks):
                team_tags = defaultdict(int)
                team_has_frontline = any('Front-line' in p['tags'] for h in team_picks if h in HERO_PROFILES for p in HERO_PROFILES[h])
                for hero in team_picks:
                    profiles = HERO_PROFILES.get(hero)
                    if profiles:
                        chosen_build = profiles[0]
                        if len(profiles) > 1 and not team_has_frontline and any('Tank' in p['build_name'] for p in profiles):
                            chosen_build = next((p for p in profiles if 'Tank' in p['build_name']), profiles[0])
                        for tag in chosen_build['tags']: team_tags[tag] += 1
                return team_tags
            
            blue_tags = get_tags_for_team(blue_picks_list)
            red_tags = get_tags_for_team(red_picks_list)
            for tag, count in blue_tags.items():
                if f"blue_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"blue_{tag}_count"]] = count
            for tag, count in red_tags.items():
                if f"red_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"red_{tag}_count"]] = count
            
            vector[feature_to_idx[match_teams[0]]] = 1
            vector[feature_to_idx[match_teams[1]]] = -1
            X.append(vector)
            y.append(1 if game['winner'] == '1' else 0)
    
    if not X:
        raise ValueError("Could not generate any training samples from the provided match data.")
    
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=200, max_depth=6, learning_rate=0.05, colsample_bytree=0.8)
    model.fit(np.array(X), np.array(y))
    
    model_assets = {'model': model, 'feature_list': feature_list, 'feature_to_idx': feature_to_idx, 'roles': roles, 'all_heroes': all_heroes, 'all_tags': all_tags, 'all_teams': all_teams}
    joblib.dump(model_assets, model_filename)
    return f"✅ Advanced model training complete. Saved to '{model_filename}'"

def predict_draft_outcome(blue_picks, red_picks, blue_team, red_team, model_assets, HERO_PROFILES):
    """Predicts the win probability for a given draft."""
    model = model_assets['model']
    feature_to_idx = model_assets['feature_to_idx']
    all_heroes = model_assets['all_heroes']
    all_teams = model_assets['all_teams']
    all_tags = model_assets['all_tags']
    roles = model_assets['roles']
    
    vector = np.zeros(len(feature_to_idx))

    for role, hero in blue_picks.items():
        if hero in all_heroes and f"{hero}_{role}" in feature_to_idx:
            vector[feature_to_idx[f"{hero}_{role}"]] = 1
    for role, hero in red_picks.items():
        if hero in all_heroes and f"{hero}_{role}" in feature_to_idx:
            vector[feature_to_idx[f"{hero}_{role}"]] = -1
    
    def get_tags_for_team(team_picks_dict):
        team_tags = defaultdict(int)
        team_picks_list = list(team_picks_dict.values())
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
        if f"blue_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"blue_{tag}_count"]] = count
    for tag, count in red_tags.items():
        if f"red_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"red_{tag}_count"]] = count
            
    if blue_team in all_teams and blue_team in feature_to_idx:
        vector[feature_to_idx[blue_team]] = 1
    if red_team in all_teams and red_team in feature_to_idx:
        vector[feature_to_idx[red_team]] = -1

    win_prob_blue = model.predict_proba(vector.reshape(1, -1))[0][1]
    return win_prob_blue
