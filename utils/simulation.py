import pandas as pd
import random
import json
import os
from collections import defaultdict


def build_week_blocks(dates):
    """(Copied from the original notebook)
    Groups sorted dates into blocks of consecutive or near-consecutive days.
    """
    if not dates: return []
    blocks=[ [dates[0]] ]
    for prev,curr in zip(dates,dates[1:]):
        # Original logic: group days that are 1 day apart
        if (curr-prev).days<=1: 
            blocks[-1].append(curr)
        else: 
            blocks.append([curr])
    return blocks
    
# --- BRACKET CONFIGURATION FUNCTIONS (Restored from Notebook) ---
def get_bracket_cache_key(tournament_name):
    """Generate a unique filename for a tournament's bracket config."""
    return f".playoff_config_{tournament_name.replace(' ', '_')}.json"

def load_bracket_config(tournament_name):
    """Load a saved bracket configuration from a local JSON file."""
    cache_file = get_bracket_cache_key(tournament_name)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # Return a default configuration if none is found
    return {
        "brackets": [
            {"start": 1, "end": 2, "name": "Top 2 Seed", "color": "#4CAF50"},
            {"start": 3, "end": 6, "name": "Playoff (3-6)", "color": "#2196F3"},
            {"start": 7, "end": None, "name": "Unqualified", "color": "#f44336"}
        ]
    }

def save_bracket_config(tournament_name, config):
    """Save a bracket configuration to a local JSON file."""
    cache_file = get_bracket_cache_key(tournament_name)
    try:
        with open(cache_file, 'w') as f:
            json.dump(config, f)
        return True
    except Exception:
        return False

# --- SERIES OUTCOME HELPER (Unchanged) ---
def get_series_outcome_options(teamA, teamB, bo:int):
    opts=[("Random","random")]
    if bo==1:
        opts+=[(f"{teamA} 1–0","A10"), (f"{teamB} 1–0","B10")]
    elif bo==2:
        opts+=[(f"{teamA} 2–0","A20"),("Draw 1–1","DRAW"),(f"{teamB} 2–0","B20")]
    elif bo==3:
        opts+=[(f"{teamA} 2–0","A20"),(f"{teamA} 2–1","A21"),
               (f"{teamB} 2–1","B21"),(f"{teamB} 2–0","B20")]
    elif bo==5:
        opts+=[(f"{teamA} 3–0","A30"),(f"{teamA} 3–1","A31"),(f"{teamA} 3–2","A32"),
               (f"{teamB} 3–2","B32"),(f"{teamB} 3–1","B31"),(f"{teamB} 3–0","B30")]
    else:
        opts+=[(f"{teamA} Win","A1"), (f"{teamB} Win","B1")]
    return opts

# --- STANDINGS TABLE BUILDER (Unchanged) ---
def build_standings_table(teams, played_matches):
    """
    Calculates the current standings based on a list of completed matches.
    This version is more robust and correctly handles teams with no matches played.
    """
    # Initialize stats for all teams in the tournament
    stats = {
        team: {'match_wins': 0, 'match_count': 0, 'game_wins': 0, 'game_losses': 0}
        for team in teams
    }

    # Iterate through only the matches that have been played up to the cutoff
    for m in played_matches:
        team_a, team_b = m["teamA"], m["teamB"]
        score_a, score_b = m["scoreA"], m["scoreB"]

        # Ensure both teams are part of the stats dictionary before proceeding
        if team_a in stats and team_b in stats:
            # Update match counts
            stats[team_a]['match_count'] += 1
            stats[team_b]['match_count'] += 1

            # Update game scores
            stats[team_a]['game_wins'] += score_a
            stats[team_a]['game_losses'] += score_b
            stats[team_b]['game_wins'] += score_b
            stats[team_b]['game_losses'] += score_a

            # Update match wins
            if m["winner"] == "1":
                stats[team_a]['match_wins'] += 1
            elif m["winner"] == "2":
                stats[team_b]['match_wins'] += 1

    # Create the final DataFrame from the calculated stats
    standings_rows = []
    for team, team_stats in stats.items():
        match_wins = team_stats['match_wins']
        match_losses = team_stats['match_count'] - match_wins
        game_wins = team_stats['game_wins']
        game_losses = team_stats['game_losses']
        game_diff = game_wins - game_losses
        
        row = {
            "Team": team,
            "Match W-L": f"{match_wins}-{match_losses}",
            "Game W-L": f"{game_wins}-{game_losses}",
            "Diff": game_diff,
            # Store raw numbers for sorting
            "_MW": match_wins,
            "_Diff": game_diff
        }
        standings_rows.append(row)

    if not standings_rows:
        return pd.DataFrame()

    df = pd.DataFrame(standings_rows)
    # Sort by Match Wins, then by Game Difference
    df = df.sort_values(by=["_MW", "_Diff"], ascending=[False, False]).reset_index(drop=True)
    # Drop the temporary sorting columns
    df = df.drop(columns=["_MW", "_Diff"])
    df.index += 1  # Make it 1-indexed for display
    return df

# --- UPGRADED MONTE CARLO SIMULATION ---
def run_monte_carlo_simulation(teams, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim=5000):
    """
    Upgraded simulation that uses custom, named brackets for probability calculation.
    """
    finish_counter = {t: {b["name"]: 0 for b in brackets} for t in teams}

    for _ in range(n_sim):
        # --- THIS IS THE ONLY LINE THAT HAS CHANGED ---
        # We now initialize a defaultdict to correctly handle teams with zero initial wins.
        sim_wins = defaultdict(int, current_wins)
        sim_diff = defaultdict(int, current_diff)
        # --- END OF CHANGE ---

        for (a, b, dt, bo) in unplayed_matches:
            code = forced_outcomes.get((a, b, dt), "random")
            if code == "random":
                options = [c for (_, c) in get_series_outcome_options(a, b, bo) if c != "random"]
                if not options: continue
                outcome = random.choice(options)
            else:
                outcome = code

            if outcome == "DRAW": continue
            
            if outcome.startswith("A"):
                winner, loser = a, b
            else:
                winner, loser = b, a
                
            num = outcome[1:]
            w, l = (int(num[0]), int(num[1])) if len(num) == 2 else (int(num), 0)

            sim_wins[winner] += 1
            sim_diff[winner] += w - l
            sim_diff[loser] += l - w

        ranked = sorted(teams, key=lambda t: (sim_wins[t], sim_diff[t], random.random()), reverse=True)
        
        for pos, t in enumerate(ranked):
            rank = pos + 1
            for bracket in brackets:
                start = bracket["start"]
                end = bracket["end"] if bracket["end"] is not None else len(teams)
                if start <= rank <= end:
                    finish_counter[t][bracket["name"]] += 1
                    break

    prob_data = []
    for t in teams:
        row = {"Team": t}
        for bracket in brackets:
            row[f"{bracket['name']} (%)"] = (finish_counter[t][bracket["name"]] / n_sim) * 100
        prob_data.append(row)
    
    df_probs = pd.DataFrame(prob_data).round(2)
    return df_probs

def get_group_cache_key(tournament_name):
    """Generate a unique filename for a tournament's group config."""
    return f".group_config_{tournament_name.replace(' ', '_')}.json"

def load_group_config(tournament_name):
    """Load a saved group configuration from a local JSON file."""
    cache_file = get_group_cache_key(tournament_name)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None # Return None if no config exists

def save_group_config(tournament_name, config):
    """Save a group configuration to a local JSON file."""
    cache_file = get_group_cache_key(tournament_name)
    try:
        with open(cache_file, 'w') as f:
            json.dump(config, f)
        return True
    except Exception:
        return False

def run_monte_carlo_simulation_groups(groups, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim=5000):
    """
    Monte Carlo simulation specifically for group stage tournaments.
    """
    teams = [t for g_teams in groups.values() for t in g_teams]
    finish_counter = {t: {b["name"]: 0 for b in brackets} for t in teams}

    for _ in range(n_sim):
        sim_wins = defaultdict(int, current_wins)
        sim_diff = defaultdict(int, current_diff)

        for (a, b, dt, bo) in unplayed_matches:
            code = forced_outcomes.get((a, b, dt), "random")
            if code == "random":
                options = [c for (_, c) in get_series_outcome_options(a, b, bo) if c != "random"]
                if not options: continue
                outcome = random.choice(options)
            else:
                outcome = code

            if outcome == "DRAW": continue
            
            winner, loser = (a, b) if outcome.startswith("A") else (b, a)
            num = outcome[1:]
            w, l = (int(num[0]), int(num[1])) if len(num) == 2 else (int(num), 0)

            sim_wins[winner] += 1
            sim_diff[winner] += w - l
            sim_diff[loser] += l - w
        
        # Rank teams within each group
        group_rankings = {}
        for g_name, g_teams in groups.items():
            ranked = sorted(g_teams, key=lambda t: (sim_wins[t], sim_diff[t], random.random()), reverse=True)
            group_rankings[g_name] = ranked
        
        # Combine all teams for an overall ranking to apply brackets
        # This assumes brackets are based on overall performance, not just group placement.
        # This logic can be customized if qualification rules are more complex.
        overall_ranked_teams = sorted(teams, key=lambda t: (sim_wins[t], sim_diff[t], random.random()), reverse=True)

        for pos, team in enumerate(overall_ranked_teams):
            rank = pos + 1
            for bracket in brackets:
                start = bracket["start"]
                end = bracket["end"] if bracket["end"] is not None else len(teams)
                if start <= rank <= end:
                    finish_counter[team][bracket["name"]] += 1
                    break
    
    prob_data = []
    for t in teams:
        row = {"Team": t}
        for g_name, g_teams in groups.items():
            if t in g_teams:
                row["Group"] = g_name
                break
        for bracket in brackets:
            row[f"{bracket['name']} (%)"] = (finish_counter[t][bracket["name"]] / n_sim) * 100
        prob_data.append(row)
    
    df_probs = pd.DataFrame(prob_data).round(2)
    return df_probs
