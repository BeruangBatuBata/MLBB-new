import pandas as pd
from collections import defaultdict

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
