import pandas as pd
import random
import json
import os
from collections import defaultdict

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
    match_counts={t:0 for t in teams}
    match_wins={t:0 for t in teams}
    gwins={t:0 for t in teams}
    gloss={t:0 for t in teams}
    for m in played_matches:
        a,b,wa,wb=m["teamA"],m["teamB"],m["scoreA"],m["scoreB"]
        if a in teams and b in teams:
            match_counts[a]+=1; match_counts[b]+=1
            gwins[a]+=wa; gloss[a]+=wb
            gwins[b]+=wb; gloss[b]+=wa
            if m["winner"]=="1": match_wins[a]+=1
            elif m["winner"]=="2": match_wins[b]+=1
            
    standings=[]
    for t in teams:
        mw=match_wins[t]; ml=match_counts[t]-mw
        gw,gl=gwins[t],gloss[t]
        diff=gw-gl
        row = {"Team":t,"Match W-L":f"{mw}-{ml}","Game W-L":f"{gw}-{gl}","Diff":diff}
        standings.append(row)
        
    df=pd.DataFrame(standings)
    if not df.empty:
        df[['MW','ML']] = df['Match W-L'].str.split('-',expand=True).astype(int)
        df=df.sort_values(by=["MW","Diff"],ascending=[False,False]).reset_index(drop=True)
        df = df.drop(columns=["MW","ML"])
        df.index += 1
    return df

# --- UPGRADED MONTE CARLO SIMULATION ---
def run_monte_carlo_simulation(teams, current_wins, current_diff, unplayed_matches, forced_outcomes, brackets, n_sim=5000):
    """
    Upgraded simulation that uses custom, named brackets for probability calculation.
    """
    finish_counter = {t: {b["name"]: 0 for b in brackets} for t in teams}

    for _ in range(n_sim):
        # BUG FIX: .copy() is a method and needs parentheses to be called.
        sim_wins = current_wins.copy()
        sim_diff = current_diff.copy()

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
