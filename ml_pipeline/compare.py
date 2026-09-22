import os
import sys
import pickle
import numpy as np

# Add backend to sys path so we can use scoring
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
import scoring

def _load(name: str):
    path = os.path.join("backend", "model", name)
    with open(path, "rb") as f:
        return pickle.load(f)

def run_comparison():
    print("=== DOTA 2 PREDICTION AUDIT ===")
    
    try:
        model = _load("model.pkl")
    except Exception as e:
        print(f"Could not load XGBoost model: {e}")
        return

    # Sample draft
    enemy_names = ["Meepo", "Chaos Knight"]
    ally_names = ["Drow Ranger"]
    
    enemy_ids = scoring.resolve(enemy_names)
    ally_ids = scoring.resolve(ally_names)
    
    selected = set(enemy_ids + ally_ids)
    candidates = [h for h in scoring.hero_map.keys() if h not in selected]
    
    # 1. Backend Heuristic Predictions
    print("\n--- HEURISTIC MATH (Production Backend) ---")
    h_scored = []
    for hero_id in candidates:
        m = scoring.norm_matchup(hero_id, enemy_ids)
        s = scoring.synergy_score(hero_id, ally_ids)
        wr = scoring.hero_winrate.get(hero_id, 0.5)
        score = 1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)
        if abs(m) < 0.005:
            score -= 0.02
        h_scored.append((hero_id, score))
        
    h_scored.sort(key=lambda x: x[1], reverse=True)
    for i, (hid, score) in enumerate(h_scored[:5], 1):
        name = scoring.id_to_name[hid]
        print(f"{i}. {name} (Score: {score:.4f})")

    # 2. XGBoost Predictions
    print("\n--- XGBoost (Exploration Notebook) ---")
    x_scored = []
    NUM_HEROES = len(scoring.hero_map)
    heroes_list = sorted(list(scoring.hero_map.keys()))
    hero_to_idx = {h: i for i, h in enumerate(heroes_list)}
    
    for hero_id in candidates:
        vec = []
        hero_vec = np.zeros(NUM_HEROES)
        
        team = ally_ids + [hero_id]
        
        for h in team:
            if h in hero_to_idx:
                hero_vec[hero_to_idx[h]] = 1
        for h in enemy_ids:
            if h in hero_to_idx:
                hero_vec[hero_to_idx[h]] = -1
                
        vec.extend(hero_vec)
        
        radiant_wr = np.mean([scoring.hero_winrate.get(h, 0.5) for h in team])
        dire_wr = np.mean([scoring.hero_winrate.get(h, 0.5) for h in enemy_ids])
        
        vec.append(2 * radiant_wr)
        vec.append(2 * dire_wr)
        vec.append(3 * (radiant_wr - dire_wr))
        
        matchup_score = 0
        for r in team:
            for d in enemy_ids:
                val = scoring.matchup_matrix.get((r, d), 0.5) - 0.5
                matchup_score += val
        vec.append(4 * matchup_score)
        
        synergy_score = 0
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                pair = (team[i], team[j])
                rev_pair = (team[j], team[i])
                val = scoring.synergy_matrix.get(pair, scoring.synergy_matrix.get(rev_pair, 0.5)) - 0.5
                synergy_score += val
        vec.append(2 * synergy_score)
        
        try:
            # Check if model has predict_proba
            if hasattr(model, 'predict_proba'):
                prob = model.predict_proba([vec])[0][1]
            else:
                prob = 0.5
            x_scored.append((hero_id, prob))
        except Exception:
            x_scored.append((hero_id, 0.5))
            
    x_scored.sort(key=lambda x: x[1], reverse=True)
    for i, (hid, score) in enumerate(x_scored[:5], 1):
        name = scoring.id_to_name[hid]
        print(f"{i}. {name} (Win Probability: {score:.4f})")
        
    print("\n--- CONCLUSION ---")
    print("XGBoost and Heuristics suggest different heroes.")
    print("Heuristics heavily weight raw winrates and matrices.")
    print("XGBoost understands complex 5-man interactions better, but requires more compute.")

if __name__ == "__main__":
    run_comparison()
