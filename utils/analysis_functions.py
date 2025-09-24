import pandas as pd
from collections import defaultdict, Counter

def calculate_hero_stats_for_team(pooled_matches, team_filter="All Teams"):
    """
    Calculates hero statistics for a specific team or all teams from a pool of matches.
    This is a pure function that returns a DataFrame.
    """
    stats_data = defaultdict(lambda: {
        "games": 0, "wins": 0, "bans": 0, "blue_picks": 0, "blue_wins": 0,
        "red_picks": 0, "red_wins": 0
    })

    # First pass to calculate total games for the selected team filter
    total_games = 0
    for match in pooled_matches:
        match_teams = [opp.get('name','').strip() for opp in match.get("match2opponents", [])]
        is_relevant_match = (team_filter == "All Teams" or team_filter in match_teams)

        if is_relevant_match:
            for game in match.get("match2games", []):
                # Ensure game has valid winner and opponents
                if game.get("winner") and game.get("opponents") and len(game.get("opponents")) >= 2:
                    total_games += 1

    if total_games == 0:
        return pd.DataFrame() # Return empty if no games found

    # Second pass to aggregate stats
    for match in pooled_matches:
        match_teams = [opp.get('name','').strip() for opp in match.get("match2opponents", [])]

        for game in match.get("match2games", []):
            winner = game.get("winner")
            if not winner: continue

            opponents = game.get("opponents")
            if not opponents or len(opponents) < 2: continue

            extradata = game.get("extradata", {})
            sides = [extradata.get("team1side", "").lower(), extradata.get("team2side", "").lower()]

            for idx, opp_game_data in enumerate(opponents):
                team_name = match_teams[idx] if idx < len(match_teams) else ""

                if team_filter != "All Teams" and team_name != team_filter:
                    continue

                # Picks
                for p in opp_game_data.get("players", []):
                    if isinstance(p, dict) and "champion" in p:
                        hero = p["champion"]
                        stats_data[hero]["games"] += 1
                        is_win = str(idx + 1) == str(winner)
                        if is_win:
                            stats_data[hero]["wins"] += 1

                        side = sides[idx] if idx < len(sides) else ""
                        if side == "blue":
                            stats_data[hero]["blue_picks"] += 1
                            if is_win: stats_data[hero]["blue_wins"] += 1
                        elif side == "red":
                            stats_data[hero]["red_picks"] += 1
                            if is_win: stats_data[hero]["red_wins"] += 1

                # Bans
                for i in range(1, 6):
                    banned_hero = extradata.get(f'team{idx+1}ban{i}')
                    if banned_hero:
                        stats_data[banned_hero]["bans"] += 1

    # Create the final DataFrame
    df_rows = []
    for hero, stats in stats_data.items():
        games = stats["games"]
        bans = stats["bans"]
        wins = stats["wins"]
        blue_picks = stats["blue_picks"]
        red_picks = stats["red_picks"]
        blue_wins = stats["blue_wins"]
        red_wins = stats["red_wins"]

        row = {
            "Hero": hero,
            "Picks": games,
            "Bans": bans,
            "Wins": wins,
            "Pick Rate (%)": round((games / total_games) * 100, 2) if total_games > 0 else 0,
            "Ban Rate (%)": round((bans / total_games) * 100, 2) if total_games > 0 else 0,
            "Presence (%)": round(((games + bans) / total_games) * 100, 2) if total_games > 0 else 0,
            "Win Rate (%)": round((wins / games) * 100, 2) if games > 0 else 0,
            "Blue Picks": blue_picks,
            "Blue Wins": blue_wins,
            "Blue Win Rate (%)": round((blue_wins / blue_picks) * 100, 2) if blue_picks > 0 else 0,
            "Red Picks": red_picks,
            "Red Wins": red_wins,
            "Red Win Rate (%)": round((red_wins / red_picks) * 100, 2) if red_picks > 0 else 0,
        }
        df_rows.append(row)

    return pd.DataFrame(df_rows)


def process_hero_drilldown_data(pooled_matches):
    """
    Processes all matches to create a cache of hero-specific stats.
    Returns a dictionary mapping each hero to their detailed statistics.
    """
    hero_stats_map = {}
    all_heroes = set()
    hero_pick_rows = []

    for match in pooled_matches:
        t1 = t2 = ""
        opps = match.get('match2opponents', [])
        if len(opps) >= 2:
            t1 = opps[0].get('name','').strip()
            t2 = opps[1].get('name','').strip()

        for game in match.get("match2games", []):
            opps_game = game.get("opponents", [])
            if len(opps_game) < 2: continue

            winner_raw = str(game.get("winner",""))
            for idx, opp in enumerate(opps_game[:2]):
                team_name = [t1, t2][idx]
                for p in opp.get("players", []):
                    if isinstance(p, dict) and "champion" in p:
                        hero = p["champion"]
                        win = (str(idx+1) == winner_raw)

                        enemy_heroes = [
                            ep["champion"]
                            for ep in opps_game[1-idx].get("players", [])
                            if isinstance(ep, dict) and "champion" in ep
                        ]

                        hero_pick_rows.append({
                            "hero": hero, "team": team_name, "win": win,
                            "enemy_heroes": enemy_heroes
                        })
                        all_heroes.add(hero)

    sorted_heroes = sorted(list(all_heroes))

    for hero in sorted_heroes:
        rows = [r for r in hero_pick_rows if r['hero'] == hero]

        # Per-team stats
        team_stats = defaultdict(lambda: {'games': 0, 'wins': 0})
        for r in rows:
            team_stats[r['team']]['games'] += 1
            if r['win']:
                team_stats[r['team']]['wins'] += 1

        team_stats_rows = []
        for team, stats in team_stats.items():
            g, w = stats['games'], stats['wins']
            winrate = (w / g * 100) if g > 0 else 0
            team_stats_rows.append({
                "Team": team, "Games": g, "Wins": w, "Win Rate (%)": f"{winrate:.2f}%"
            })

        # Matchup stats
        all_enemy_heroes = [eh for r in rows for eh in r.get("enemy_heroes", [])]
        matchups = Counter(all_enemy_heroes)
        win_counter = defaultdict(int)
        for r in rows:
            if r['win']:
                for eh in r['enemy_heroes']:
                    win_counter[eh] += 1

        matchup_rows = []
        for enemy_hero, faced_count in matchups.most_common():
            win_count = win_counter[enemy_hero]
            wr_vs = (win_count / faced_count * 100) if faced_count > 0 else 0
            matchup_rows.append({
                "Opposing Hero": enemy_hero,
                "Times Faced": faced_count,
                f"Win Rate vs Them (%)": f"{wr_vs:.2f}%"
            })

        hero_stats_map[hero] = {
            "per_team_df": pd.DataFrame(team_stats_rows).sort_values("Games", ascending=False),
            "matchups_df": pd.DataFrame(matchup_rows)
        }

    return sorted_heroes, hero_stats_map


def process_head_to_head_teams(t1_norm, t2_norm, pooled_matches):
    """
    Analyzes the head-to-head record between two specific teams.
    """
    win_counts = {t1_norm: 0, t2_norm: 0}
    t1_heroes = Counter()
    t2_heroes = Counter()
    t1_bans = Counter()
    t2_bans = Counter()
    total_games = 0

    for match in pooled_matches:
        opps = [x.get("name", "").strip() for x in match.get("match2opponents", [])]
        if {t1_norm, t2_norm}.issubset(set(opps)):
            try:
                idx1 = opps.index(t1_norm)
            except ValueError:
                continue

            for game in match.get("match2games", []):
                winner = str(game.get("winner", ""))
                if winner.isdigit():
                    total_games += 1
                    winner_team = opps[int(winner) - 1]
                    if winner_team in win_counts:
                        win_counts[winner_team] += 1

                # Picks and bans
                extrad = game.get("extradata", {})
                for i, opp_game in enumerate(game.get("opponents", [])):
                    hero_set = {p["champion"] for p in opp_game.get("players", []) if isinstance(p, dict) and "champion" in p}
                    is_t1 = (i == idx1)

                    if is_t1:
                        t1_heroes.update(hero_set)
                    else:
                        t2_heroes.update(hero_set)

                    for ban_n in range(1, 6):
                        ban_hero = extrad.get(f"team{i+1}ban{ban_n}")
                        if ban_hero:
                            if is_t1:
                                t1_bans[ban_hero] += 1
                            else:
                                t2_bans[ban_hero] += 1

    return {
        "win_counts": win_counts,
        "total_games": total_games,
        "t1_picks_df": pd.DataFrame(t1_heroes.most_common(8), columns=['Hero', 'Picks']),
        "t2_picks_df": pd.DataFrame(t2_heroes.most_common(8), columns=['Hero', 'Picks']),
        "t1_bans_df": pd.DataFrame(t1_bans.most_common(8), columns=['Hero', 'Bans']),
        "t2_bans_df": pd.DataFrame(t2_bans.most_common(8), columns=['Hero', 'Bans']),
    }
