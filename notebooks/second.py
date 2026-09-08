#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Module Imports
import pandas as pd
import numpy as np
import requests
import ast

from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


# In[2]:


#Creating the dataframes and data cleaning
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

df = pd.read_csv("matches.csv")

df['radiant_team'] = df['radiant_team'].apply(clean_team)
df['dire_team'] = df['dire_team'].apply(clean_team)

df = df[
    (df['radiant_team'].apply(lambda x: len(x) == 5 and all(h != 0 for h in x))) &
    (df['dire_team'].apply(lambda x: len(x) == 5 and all(h != 0 for h in x)))
]


# In[3]:


#Counter Logic
from collections import Counter

hero_counts = Counter()

for _, row in df.iterrows():
    hero_counts.update(row['radiant_team'])
    hero_counts.update(row['dire_team'])

MIN_GAMES = 10

valid_heroes = {
    h for h, count in hero_counts.items()
    if count >= MIN_GAMES
}

df = df[
    df['radiant_team'].apply(lambda team: all(h in valid_heroes for h in team)) &
    df['dire_team'].apply(lambda team: all(h in valid_heroes for h in team))
]


# In[4]:


heroes = sorted(list(valid_heroes))
hero_to_idx = {h: i for i, h in enumerate(heroes)}
NUM_HEROES = len(heroes)


# In[5]:


#Fetching Hero data from OpenDota API

hero_data = requests.get("https://api.opendota.com/api/heroes").json()
api_roles = {h['id']: h.get('roles', []) for h in hero_data}

hero_roles = {}

for hid in hero_to_idx.keys():
    roles = api_roles.get(hid, [])

hero_data = requests.get("https://api.opendota.com/api/heroes").json()
api_roles = {h['id']: h.get('roles', []) for h in hero_data}

hero_roles = {}

for hid in hero_to_idx.keys():
    roles = api_roles.get(hid, [])

    mapped_roles = []

    if "Carry" in roles:
        mapped_roles.append("carry")

    if "Nuker" in roles:
        mapped_roles.append("mid")

    if "Initiator" in roles or "Durable" in roles:
        mapped_roles.append("offlane")

    if "Support" in roles:
        mapped_roles.append("support")

    if not mapped_roles:
        mapped_roles = ["offlane"]

    hero_roles[hid] = mapped_roles

    if "Support" in roles and "Carry" not in roles:
     hero_roles[hid] = "support"

    elif "Nuker" in roles:
     hero_roles[hid] = "mid"

    elif "Initiator" in roles or "Durable" in roles:
     hero_roles[hid] = "offlane"

    elif "Carry" in roles:
     hero_roles[hid] = "carry"

    else:

        hero_roles[hid] = "offlane"


# In[6]:


#Assigning Roles to Heroes
def get_dynamic_role(hero, team):
    roles = hero_roles.get(hero, ["offlane"])


    if isinstance(roles, str):
        roles = [roles]

    team_roles = [hero_roles.get(h, ["offlane"])[0] if isinstance(hero_roles.get(h, ["offlane"]), list) else hero_roles.get(h, "offlane") for h in team]
    role_count = Counter(team_roles)

    needed_roles = {
        "carry": 1 - role_count.get("carry", 0),
        "mid": 1 - role_count.get("mid", 0),
        "offlane": 1 - role_count.get("offlane", 0),
        "support": 2 - role_count.get("support", 0),
    }

    best_role = None
    best_score = -999

    for r in roles:
        if r not in needed_roles:
            continue  # skip broken roles

        score = needed_roles.get(r, 0)

        if score > best_score:
            best_score = score
            best_role = r

    return best_role if best_role else "offlane"


# In[7]:


from collections import Counter

def get_team_roles(team):
    roles = [hero_roles.get(h, ["offlane"])[0] if isinstance(hero_roles.get(h, ["offlane"]), list) else hero_roles.get(h, "offlane") for h in team]
    return Counter(roles)


# In[8]:


#Obtaining Role Score
def role_score(team):
    roles = get_team_roles(team)

    score = 0
    if roles["carry"] == 0:
        score -= 0.4
    elif roles["carry"] > 1:
        score -= 0.3 * (roles["carry"] - 1)

    if roles["mid"] == 0:
        score -= 0.3
    elif roles["mid"] > 1:
        score -= 0.2 * (roles["mid"] - 1)


    if roles["offlane"] == 0:
        score -= 0.25

    if roles["support"] < 2:
        score -= 0.3
    elif roles["support"] > 3:
        score -= 0.15 * (roles["support"] - 3)

    return score


# In[9]:


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


# In[10]:


synergy_matrix = {}

pair_counts = {}

for _, row in df.iterrows():
    team = row['radiant_team']
    win = row['radiant_win']

    # radiant pairs
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


# In[11]:


winrates = matchups_df.groupby(['hero_1', 'hero_2'])['win'].mean().reset_index()

strong_counters = winrates[
    (winrates['win'] < 0.35) | (winrates['win'] > 0.65)
]


# In[12]:


counter_pairs = list(zip(strong_counters['hero_1'], strong_counters['hero_2']))
pair_to_idx = {pair: i for i, pair in enumerate(counter_pairs)}

NUM_COUNTERS = len(counter_pairs)


# In[13]:


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


# In[14]:


matchup_matrix = {}

for _, row in winrates.iterrows():
    matchup_matrix[(row['hero_1'], row['hero_2'])] = row['win']


# In[15]:


X = []
y = []

for _, row in df.iterrows():
    vec = []

    hero_vec = np.zeros(NUM_HEROES)

    for h in row['radiant_team']:
        hero_vec[hero_to_idx[h]] = 1
    for h in row['dire_team']:
        hero_vec[hero_to_idx[h]] = -1

    vec.extend(hero_vec)

    # team strength
    radiant_wr = np.mean([hero_winrate[h] for h in row['radiant_team']])
    dire_wr = np.mean([hero_winrate[h] for h in row['dire_team']])

    vec.append(2 * radiant_wr)
    vec.append(2 * dire_wr)
    vec.append(3 * (radiant_wr - dire_wr))

    # matchup
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


# In[16]:


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# In[17]:


model = XGBClassifier(
    n_estimators=800,
    max_depth=7,
    learning_rate=0.025,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_lambda=2,
    reg_alpha=0.5,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

print("Accuracy:", model.score(X_test, y_test))


# In[18]:


from sklearn.metrics import log_loss

print("LogLoss:", log_loss(y_test, model.predict_proba(X_test)))


# In[19]:


def predict(hero, enemy_team, my_team):
    team = my_team + [hero]

    vec = []


    hero_vec = np.zeros(NUM_HEROES)

    for h in team:
        hero_vec[hero_to_idx[h]] = 1
    for h in enemy_team:
        hero_vec[hero_to_idx[h]] = -1

    vec.extend(hero_vec)


    radiant_wr = np.mean([hero_winrate[h] for h in team])
    dire_wr = np.mean([hero_winrate[h] for h in enemy_team])

    vec.append(2 * radiant_wr)
    vec.append(2 * dire_wr)
    vec.append(3 * (radiant_wr - dire_wr))


    matchup_score = 0
    for r in team:
        for d in enemy_team:
            matchup_score += matchup_matrix.get((r, d), 0.5) - 0.5

    vec.append(4 * matchup_score)


    synergy_score = 0
    for i in range(len(team)):
        for j in range(i+1, len(team)):
            pair = (team[i], team[j])
            rev_pair = (team[j], team[i])

            val = synergy_matrix.get(pair, synergy_matrix.get(rev_pair, 0.5))
            synergy_score += (val - 0.5)

    vec.append(2 * synergy_score)

    prob = model.predict_proba([vec])[0][1]

    # calibration
    prob = 0.5 + (prob - 0.5) * 0.7

    return prob


# In[20]:


def suggest(enemy_team, my_team=[]):
    taken = set(enemy_team + my_team)
    candidates = [h for h in hero_to_idx.keys() if h not in taken]

    results = []

    for hero in candidates:
        prob = predict(hero, enemy_team, my_team)

        new_team = my_team + [hero]


        r_score = role_score(new_team)
        matchup_score = 0
        for e in enemy_team:
            matchup_score += matchup_matrix.get((hero, e), 0.5) - 0.5


        synergy_score = 0
        for ally in my_team:
            pair = (hero, ally)
            rev_pair = (ally, hero)

            val = synergy_matrix.get(pair, synergy_matrix.get(rev_pair, 0.5))
            synergy_score += (val - 0.5)


        base_wr = hero_winrate.get(hero, 0.5)

        final_score = (
            prob
            + 0.25 * r_score
            + 0.4 * matchup_score
            + 0.3 * synergy_score
            + 0.1 * (base_wr - 0.5)
        )


        if abs(matchup_score) < 0.05:
            final_score -= 0.05 

        results.append((hero, final_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]


# In[21]:


def group_by_role(results, my_team):
    role_groups = {
        "carry": [],
        "mid": [],
        "offlane": [],
        "support": []
    }

    for hero, score in results:
        role = get_dynamic_role(hero, my_team)
        role_groups[role].append((hero, score))

    return role_groups


# In[22]:


def explain_pick(hero, enemy_team, my_team):
    reasons = []

    # --- MATCHUP ---
    matchup_score = 0
    strong_vs = []

    for e in enemy_team:
        val = matchup_matrix.get((hero, e), 0.5)
        diff = val - 0.5
        matchup_score += diff

        if diff > 0.1:
            strong_vs.append(hero_map.get(e, e))

    if strong_vs:
        reasons.append(f"Strong vs: {', '.join(strong_vs[:2])}")

    synergy_score = 0
    good_with = []

    for ally in my_team:
        val = synergy_matrix.get((hero, ally), synergy_matrix.get((ally, hero), 0.5))
        diff = val - 0.5
        synergy_score += diff

        if diff > 0.1:
            good_with.append(hero_map.get(ally, ally))

    if good_with:
        reasons.append(f"Good with: {', '.join(good_with[:2])}")

    roles = hero_roles.get(hero, ["unknown"])


    if isinstance(roles, str):
     roles = [roles]

    reasons.append(f"Roles: {', '.join(roles)}")


    wr = hero_winrate.get(hero, 0.5)
    if wr > 0.52:
        reasons.append("Meta strong")

    return reasons


# In[23]:


def suggest_top3_by_role(enemy_team, my_team=[]):
    results = suggest(enemy_team, my_team)

    grouped = group_by_role(results, my_team)

    print("Enemy:", [hero_map.get(h, h) for h in enemy_team])
    print("Your Team:", [hero_map.get(h, h) for h in my_team])
    print("\n--- TOP PICKS BY ROLE ---\n")

    for role, heroes in grouped.items():
        print(f"{role.upper()}:\n")

        top3 = sorted(heroes, key=lambda x: x[1], reverse=True)[:3]

        for i, (h, score) in enumerate(top3, 1):
            name = hero_map.get(h, h)
            print(f"{i}. {name} â†’ {round(score, 3)}")

            reasons = explain_pick(h, enemy_team, my_team)
            for r in reasons:
                print(f"   - {r}")

            print()

        print("-" * 40)


# In[24]:


hero_map = {
    h['id']: h['localized_name']
    for h in requests.get("https://api.opendota.com/api/heroes").json()
}


# In[25]:


def suggest_named(enemy_team, my_team=[]):
    print("Enemy:", [hero_map.get(h, h) for h in enemy_team])
    print("Your Team:", [hero_map.get(h, h) for h in my_team])
    print("\nSuggestions:\n")

    results = suggest(enemy_team, my_team)

    for i, (h, prob) in enumerate(results, 1):
        print(f"{i}. {hero_map.get(h, h)} â†’ {round(prob, 3)}")


# In[26]:


fixed_roles = {}

for h, roles in hero_roles.items():
    if isinstance(roles, str):
        roles = [roles]

    clean = []

    for r in roles:
        if r in ["c", "carry"]:
            clean.append("carry")
        elif r in ["m", "mid"]:
            clean.append("mid")
        elif r in ["o", "offlane"]:
            clean.append("offlane")
        elif r in ["s", "support"]:
            clean.append("support")


    if not clean:
        clean = ["offlane"]

    fixed_roles[h] = list(set(clean)) 

hero_roles = fixed_roles


# In[27]:


suggest_named([81,82], [6,7])  


# In[28]:


suggest_named([17, 59, 6, 74],[35,1])


# In[29]:


suggest_top3_by_role([6,36],[50,59])


# In[30]:


suggest_top3_by_role([81,82], [59,50])


# In[31]:


for h in [1, 2, 6, 17, 59]:
    print(hero_map[h], "â†’", hero_roles.get(h))


# In[32]:


from collections import Counter
pass


# In[33]:


for h, r in hero_roles.items():
    if isinstance(r, str) and len(r) == 1:
        print(h, r)


# In[34]:


import pickle

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("hero_map.pkl", "wb") as f:
    pickle.dump(hero_map, f)

with open("matchup.pkl", "wb") as f:
    pickle.dump(matchup_matrix, f)

with open("synergy.pkl", "wb") as f:
    pickle.dump(synergy_matrix, f)

with open("roles.pkl", "wb") as f:
    pickle.dump(hero_roles, f)


# In[ ]:




