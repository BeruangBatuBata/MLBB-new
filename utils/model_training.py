import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from collections import defaultdict
from utils.data_processing import HERO_PROFILES

def train_and_save_prediction_model(matches, model_filename='draft_predictor.joblib'):
    """
    Trains an advanced XGBoost model using Hero+Role, Ban, and Compositional features.
    """
    print("Starting advanced model training process...")

    # --- 1. Define the full feature space ---
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
    print(f"Created a feature space with {len(feature_list)} unique features.")

    # --- 2. Prepare data with temporal weighting ---
    X, y, weights = [], [], []
    valid_dates = [pd.to_datetime(m['date']) for m in matches if pd.notna(pd.to_datetime(m.get('date')))]
    if not valid_dates:
        print("No valid dates found in matches. Cannot perform temporal weighting.")
        return
        
    max_date = max(valid_dates)

    for match in matches:
        match_date = pd.to_datetime(match.get('date'))
        if pd.isna(match_date): continue

        match_teams = [o.get('name') for o in match.get('match2opponents', [])]
        if len(match_teams) != 2 or not all(t in feature_to_idx for t in match_teams): continue

        for game in match.get('match2games', []):
            extradata = game.get('extradata', {})
            if len(game.get('opponents', [])) != 2 or game.get('winner') not in ['1', '2'] or not extradata:
                continue
            
            vector = np.zeros(len(feature_list))
            
            # a) Process Picks (Hero + Role) and build list for tag counting
            blue_picks_list, red_picks_list = [], []
            for i, role in enumerate(roles, 1):
                blue_hero = extradata.get(f'team1champion{i}')
                red_hero = extradata.get(f'team2champion{i}')
                if blue_hero in all_heroes:
                    if f"{blue_hero}_{role}" in feature_to_idx:
                        vector[feature_to_idx[f"{blue_hero}_{role}"]] = 1
                    blue_picks_list.append(blue_hero)
                if red_hero in all_heroes:
                    if f"{red_hero}_{role}" in feature_to_idx:
                        vector[feature_to_idx[f"{red_hero}_{role}"]] = -1
                    red_picks_list.append(red_hero)

            # b) Process Bans
            for i in range(1, 6):
                blue_ban, red_ban = extradata.get(f'team1ban{i}'), extradata.get(f'team2ban{i}')
                if blue_ban in all_heroes and f"{blue_ban}_Ban" in feature_to_idx: vector[feature_to_idx[f"{blue_ban}_Ban"]] = 1
                if red_ban in all_heroes and f"{red_ban}_Ban" in feature_to_idx: vector[feature_to_idx[f"{red_ban}_Ban"]] = -1
                
            # c) Process Compositional Tags using Contextual Build Inference
            def get_tags_for_team(team_picks):
                team_tags = defaultdict(int)
                team_has_frontline = any('Front-line' in p['tags'] for h in team_picks if h in HERO_PROFILES for p in HERO_PROFILES[h])
                for hero in team_picks:
                    profiles = HERO_PROFILES.get(hero)
                    if profiles:
                        chosen_build = profiles[0]
                        if len(profiles) > 1 and not team_has_frontline and any('Tank' in p['build_name'] for p in profiles):
                            chosen_build = next((p for p in profiles if 'Tank' in p['build_name']), profiles[0])
                        for tag in chosen_build['tags']:
                            team_tags[tag] += 1
                return team_tags
            
            blue_tags = get_tags_for_team(blue_picks_list)
            red_tags = get_tags_for_team(red_picks_list)
            for tag, count in blue_tags.items():
                if f"blue_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"blue_{tag}_count"]] = count
            for tag, count in red_tags.items():
                if f"red_{tag}_count" in feature_to_idx: vector[feature_to_idx[f"red_{tag}_count"]] = count
                
            # d) Process Team Identities
            vector[feature_to_idx[match_teams[0]]] = 1
            vector[feature_to_idx[match_teams[1]]] = -1

            X.append(vector)
            y.append(1 if game['winner'] == '1' else 0)

            days_old = (max_date - match_date).days
            weights.append(0.99 ** (days_old / 30))

    if not X:
        print("Could not generate any training samples."); return

    print(f"Training model on {len(X)} games...")
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=200, max_depth=6, learning_rate=0.05, colsample_bytree=0.8)
    model.fit(np.array(X), np.array(y), sample_weight=np.array(weights))

    model_assets = {'model': model, 'feature_list': feature_list, 'feature_to_idx': feature_to_idx, 'roles': roles, 'all_heroes': all_heroes, 'all_tags': all_tags}
    joblib.dump(model_assets, model_filename)
    print(f"✅ Advanced model training complete. Saved to '{model_filename}'")
