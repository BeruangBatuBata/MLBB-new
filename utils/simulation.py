import pandas as pd
import random
from collections import defaultdict

def get_series_outcome_options(teamA, teamB, bo:int):
    """Generates the possible outcomes for a best-of series."""
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

def build_standings_table(teams, played_matches):
    """Calculates the current standings based on a list of completed matches."""
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
        # Sort by Match Wins, then by Game Difference
        df[['MW','ML']] = df['Match W-L'].str.split('-',expand=True).astype(int)
        df=df.sort_values(by=["MW","Diff"],ascending=[False,False]).reset_index(drop=True)
        df = df.drop(columns=["MW","ML"])
        df.index += 1 # Make it 1-indexed for display
    return df

def run_monte_carlo_simulation(teams, current_wins, current_diff, unplayed_matches, forced_outcomes, n_sim=5000):
    """
    Runs a Monte Carlo simulation for a single-table tournament.
    This is a pure, heavy-lifting function.
    """
    position_counts = {team: defaultdict(int) for team in teams}

    for _ in range(n_sim):
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

            if outcome == "DRAW":
                continue

            if outcome.startswith("A"):
                winner, loser = a, b
                num = outcome[1:]
            elif outcome.startswith("B"):
                winner, loser = b, a
                num = outcome[1:]
            else:
                continue

            w, l = (int(num[0]), int(num[1])) if len(num) == 2 else (int(num), 0)

            sim_wins[winner] += 1
            sim_diff[winner] += w - l
            sim_diff[loser] += l - w

        ranked_teams = sorted(teams, key=lambda t: (sim_wins[t], sim_diff[t], random.random()), reverse=True)
        
        for pos, team in enumerate(ranked_teams):
            position_counts[team][pos + 1] += 1
    
    # Calculate probabilities
    prob_data = []
    for t in teams:
        row = {"Team": t}
        for i in range(1, len(teams) + 1):
            row[f"Rank {i} (%)"] = (position_counts[t][i] / n_sim) * 100
        prob_data.append(row)

    df_probs = pd.DataFrame(prob_data).round(2)
    return df_probs
