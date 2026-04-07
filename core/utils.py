import numpy as np
from collections import Counter

# these will be loaded from app.py
model = None
hero_map = None
matchup_matrix = None
synergy_matrix = None
hero_roles = None
hero_winrate = None
hero_to_idx = None
NUM_HEROES = None


def get_primary_role(hero):
    roles = hero_roles.get(hero, ["offlane"])
    if isinstance(roles, list):
        return roles[0]
    return roles


def get_team_roles(team):
    roles = [get_primary_role(h) for h in team]
    return Counter(roles)


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
    prob = 0.5 + (prob - 0.5) * 0.7

    return prob


def suggest(enemy_team, my_team=[]):
    taken = set(enemy_team + my_team)
    candidates = [h for h in hero_to_idx.keys() if h not in taken]

    results = []

    for hero in candidates:
        prob = predict(hero, enemy_team, my_team)
        new_team = my_team + [hero]

        r_score = role_score(new_team)

        matchup_score = sum(
            matchup_matrix.get((hero, e), 0.5) - 0.5 for e in enemy_team
        )

        synergy_score = sum(
            synergy_matrix.get((hero, ally), synergy_matrix.get((ally, hero), 0.5)) - 0.5
            for ally in my_team
        )

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


def explain_pick(hero, enemy_team, my_team):
    reasons = []

    strong_vs = [
        hero_map.get(e, e)
        for e in enemy_team
        if matchup_matrix.get((hero, e), 0.5) - 0.5 > 0.1
    ]

    if strong_vs:
        reasons.append(f"Strong vs: {', '.join(strong_vs[:2])}")

    good_with = [
        hero_map.get(a, a)
        for a in my_team
        if synergy_matrix.get((hero, a), 0.5) - 0.5 > 0.1
    ]

    if good_with:
        reasons.append(f"Good with: {', '.join(good_with[:2])}")

    roles = hero_roles.get(hero, ["unknown"])
    if isinstance(roles, str):
        roles = [roles]

    reasons.append(f"Roles: {', '.join(roles)}")

    if hero_winrate.get(hero, 0.5) > 0.52:
        reasons.append("Meta strong")

    return reasons