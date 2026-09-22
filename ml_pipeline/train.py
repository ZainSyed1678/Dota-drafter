import pandas as pd
import numpy as np
import requests
import ast
import argparse
import pickle
import sys
from pathlib import Path
from collections import Counter
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import log_loss

def clean_team(x):
    try:
        x = str(x)
        while isinstance(x, str):
            try:
                x = ast.literal_eval(x)
            except:
                break
        if isinstance(x, str):
            x = x.replace('[','').replace(']','')
            x = [int(i.strip()) for i in x.split(',') if i.strip().isdigit()]
        return list(x)
    except:
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", type=str, required=True, help="Path to the versioned matches CSV")
    parser.add_argument("--output_dir", type=str, default="../backend/model", help="Directory to save the trained pkl files")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    df['radiant_team'] = df['radiant_team'].apply(clean_team)
    df['dire_team'] = df['dire_team'].apply(clean_team)

    df = df[
        (df['radiant_team'].apply(lambda x: len(x) == 5 and all(h != 0 for h in x))) &
        (df['dire_team'].apply(lambda x: len(x) == 5 and all(h != 0 for h in x)))
    ]

    print(f"Valid 5v5 matches: {len(df)}")
    
    if len(df) == 0:
        print("Dataset is empty after cleaning!")
        sys.exit(1)

    hero_counts = Counter()
    for _, row in df.iterrows():
        hero_counts.update(row['radiant_team'])
        hero_counts.update(row['dire_team'])

    MIN_GAMES = 1
    # Note: MIN_GAMES set to 1 for small testing datasets so training doesn't crash on 100 matches
    # In production, this can be increased if match count > 1000.
    if len(df) > 1000:
        MIN_GAMES = 10

    valid_heroes = {h for h, count in hero_counts.items() if count >= MIN_GAMES}

    df = df[
        df['radiant_team'].apply(lambda team: all(h in valid_heroes for h in team)) &
        df['dire_team'].apply(lambda team: all(h in valid_heroes for h in team))
    ]

    heroes = sorted(list(valid_heroes))
    hero_to_idx = {h: i for i, h in enumerate(heroes)}
    NUM_HEROES = len(heroes)

    print(f"Total valid heroes after MIN_GAMES ({MIN_GAMES}) filter: {NUM_HEROES}")
    
    if NUM_HEROES == 0 or len(df) < 5:
        print("Not enough data to train. Exiting gracefully.")
        sys.exit(0)

    # 1. Hero Map and Roles
    try:
        hero_data = requests.get("https://api.opendota.com/api/heroes").json()
        hero_map = {h['id']: h['localized_name'] for h in hero_data}
        api_roles = {h['id']: h.get('roles', []) for h in hero_data}
    except Exception as e:
        print(f"Error fetching hero API: {e}")
        hero_map = {}
        api_roles = {}

    hero_roles = {}
    for hid in hero_to_idx.keys():
        roles = api_roles.get(hid, [])
        clean = []
        if "Carry" in roles: clean.append("carry")
        if "Nuker" in roles: clean.append("mid")
        if "Initiator" in roles or "Durable" in roles: clean.append("offlane")
        if "Support" in roles: clean.append("support")
        if not clean: clean = ["offlane"]
        hero_roles[hid] = list(set(clean))

    # 2. Matchup Matrix
    matchups = []
    for _, row in df.iterrows():
        r = row['radiant_team']
        d = row['dire_team']
        win = row['radiant_win']
        for a in r:
            for b in d:
                matchups.append((a, b, win))
                matchups.append((b, a, 1 - win))
    matchups_df = pd.DataFrame(matchups, columns=['hero_1', 'hero_2', 'win'])
    winrates = matchups_df.groupby(['hero_1', 'hero_2'])['win'].mean().reset_index()
    
    matchup_matrix = {}
    for _, row in winrates.iterrows():
        matchup_matrix[(row['hero_1'], row['hero_2'])] = row['win']

    # 3. Synergy Matrix
    synergy_matrix = {}
    pair_counts = {}
    for _, row in df.iterrows():
        team = row['radiant_team']
        win = row['radiant_win']
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                pair = (team[i], team[j])
                pair_counts[pair] = pair_counts.get(pair, [0, 0])
                pair_counts[pair][0] += win
                pair_counts[pair][1] += 1
                
        team = row['dire_team']
        win = 1 - row['radiant_win']
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                pair = (team[i], team[j])
                pair_counts[pair] = pair_counts.get(pair, [0, 0])
                pair_counts[pair][0] += win
                pair_counts[pair][1] += 1

    for pair, (wins, games) in pair_counts.items():
        synergy_matrix[pair] = wins / games

    # 4. Hero Winrates
    hero_games = {}
    hero_wins = {}
    for _, row in df.iterrows():
        for h in row['radiant_team']:
            hero_games[h] = hero_games.get(h, 0) + 1
            hero_wins[h] = hero_wins.get(h, 0) + row['radiant_win']
        for h in row['dire_team']:
            hero_games[h] = hero_games.get(h, 0) + 1
            hero_wins[h] = hero_wins.get(h, 0) + (1 - row['radiant_win'])
            
    hero_winrate = {}
    for h in hero_to_idx.keys():
        if hero_games.get(h, 0) > 0:
            hero_winrate[h] = hero_wins[h] / hero_games[h]
        else:
            hero_winrate[h] = 0.5

    # 5. Build Training Vectors
    X, y = [], []
    for _, row in df.iterrows():
        vec = []
        hero_vec = np.zeros(NUM_HEROES)
        for h in row['radiant_team']:
            hero_vec[hero_to_idx[h]] = 1
        for h in row['dire_team']:
            hero_vec[hero_to_idx[h]] = -1
        vec.extend(hero_vec)
        
        radiant_wr = np.mean([hero_winrate.get(h, 0.5) for h in row['radiant_team']])
        dire_wr = np.mean([hero_winrate.get(h, 0.5) for h in row['dire_team']])
        vec.append(2 * radiant_wr)
        vec.append(2 * dire_wr)
        vec.append(3 * (radiant_wr - dire_wr))
        
        matchup_score = 0
        for r in row['radiant_team']:
            for d in row['dire_team']:
                matchup_score += matchup_matrix.get((r, d), 0.5) - 0.5
        vec.append(4 * matchup_score)
        
        synergy_score = 0
        team = row['radiant_team']
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                pair = (team[i], team[j])
                rev_pair = (team[j], team[i])
                val = synergy_matrix.get(pair, synergy_matrix.get(rev_pair, 0.5))
                synergy_score += (val - 0.5)
        vec.append(2 * synergy_score)
        
        X.append(vec)
        y.append(row['radiant_win'])

    X = np.array(X)
    y = np.array(y)

    print(f"X shape: {X.shape}, y shape: {y.shape}")

    # 6. Train XGBoost Model
    if X.shape[0] < 5:
        print("Not enough samples for train_test_split. Need more data to train the model.")
        sys.exit(0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBClassifier(
        n_estimators=800, max_depth=7, learning_rate=0.025,
        subsample=0.9, colsample_bytree=0.9, reg_lambda=2,
        reg_alpha=0.5, eval_metric='logloss'
    )
    
    print("Training XGBoost...")
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)
    loss = log_loss(y_test, model.predict_proba(X_test))
    print(f"Accuracy: {acc:.4f}")
    print(f"LogLoss: {loss:.4f}")

    # 7. Save outputs
    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(out_path / "hero_map.pkl", "wb") as f:
        pickle.dump(hero_map, f)
    with open(out_path / "matchup.pkl", "wb") as f:
        pickle.dump(matchup_matrix, f)
    with open(out_path / "synergy.pkl", "wb") as f:
        pickle.dump(synergy_matrix, f)
    with open(out_path / "roles.pkl", "wb") as f:
        pickle.dump(hero_roles, f)
    with open(out_path / "hero_winrate.pkl", "wb") as f:
        pickle.dump(hero_winrate, f)
        
    print(f"Successfully saved all .pkl artifacts to {out_path}!")

if __name__ == "__main__":
    main()
