import streamlit as st
import pickle

st.set_page_config(page_title="Dota 2 Drafter", layout="wide")

# --- LOAD DATA ---
hero_map = pickle.load(open("model/hero_map.pkl", "rb"))
matchup_matrix = pickle.load(open("model/matchup.pkl", "rb"))
synergy_matrix = pickle.load(open("model/synergy.pkl", "rb"))
hero_roles = pickle.load(open("model/roles.pkl", "rb"))

name_to_id = {v: k for k, v in hero_map.items()}
id_to_name = hero_map

# --- SESSION STATE ---
if "enemy" not in st.session_state:
    st.session_state.enemy = []

if "team" not in st.session_state:
    st.session_state.team = []

if "mode" not in st.session_state:
    st.session_state.mode = "enemy"

# --- HELPERS ---
def get_img(name):
    return f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/{name.lower().replace(' ', '_')}_full.png"

def get_primary_role(hero):
    roles = hero_roles.get(hero, ["offlane"])
    if isinstance(roles, str):
        roles = [roles]

    priority = ["carry", "mid", "offlane", "support"]
    for p in priority:
        if p in roles:
            return p
    return roles[0]

def explain(hero, enemy, team):
    reasons = []

    for e in enemy:
        val = matchup_matrix.get((hero, e), 0)
        if val > 0.05:
            reasons.append(f"Strong vs {id_to_name[e]}")

    for t in team:
        val = synergy_matrix.get((hero, t), 0)
        if val > 0.05:
            reasons.append(f"Good with {id_to_name[t]}")

    roles = hero_roles.get(hero, ["offlane"])
    if isinstance(roles, str):
        roles = [roles]

    reasons.append(f"Roles: {', '.join(roles)}")
    return reasons

# --- STYLE ---
st.markdown("""
<style>
.hero-img {
    border-radius: 10px;
    transition: 0.2s;
}
.hero-img:hover {
    transform: scale(1.1);
    cursor: pointer;
}
.selected-enemy {
    border: 3px solid red;
}
.selected-team {
    border: 3px solid green;
}
.card {
    background: #111827;
    padding: 10px;
    border-radius: 12px;
    text-align: center;
    margin: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Dota 2 Drafter")

# --- MODE SWITCH ---
col1, col2 = st.columns(2)

with col1:
    if st.button("🟥 Add Enemy"):
        st.session_state.mode = "enemy"

with col2:
    if st.button("🟩 Add Your Team"):
        st.session_state.mode = "team"

st.write(f"Current Mode: **{st.session_state.mode.upper()}**")

# --- HERO GRID ---
heroes = list(hero_map.values())
cols = st.columns(8)

for i, name in enumerate(heroes):
    col = cols[i % 8]
    hero_id = name_to_id[name]

    with col:
        img = get_img(name)

        css_class = ""
        if hero_id in st.session_state.enemy:
            css_class = "selected-enemy"
        elif hero_id in st.session_state.team:
            css_class = "selected-team"

        if st.button(name, key=f"{name}_{i}"):

            # --- UNIVERSAL TOGGLE ---
            if hero_id in st.session_state.enemy:
                st.session_state.enemy.remove(hero_id)

            elif hero_id in st.session_state.team:
                st.session_state.team.remove(hero_id)

            else:
                if st.session_state.mode == "enemy":
                    st.session_state.enemy.append(hero_id)
                else:
                    st.session_state.team.append(hero_id)

        st.markdown(
            f'<img src="{img}" class="hero-img {css_class}" width="80">',
            unsafe_allow_html=True
        )

# --- CURRENT PICKS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟥 Enemy Team")
    st.write([id_to_name[h] for h in st.session_state.enemy])

with col2:
    st.subheader("🟩 Your Team")
    st.write([id_to_name[h] for h in st.session_state.team])

# --- SUGGEST ---
if st.button("🔥 Suggest Picks"):

    results = []

    for hero in hero_map.keys():
        if hero in st.session_state.enemy or hero in st.session_state.team:
            continue

        score = 0

        # --- MATCHUP ---
        for e in st.session_state.enemy:
            score += matchup_matrix.get((hero, e), 0)

        # --- SYNERGY ---
        for t in st.session_state.team:
            score += synergy_matrix.get((hero, t), 0)

        results.append((hero, score))

    results = sorted(results, key=lambda x: x[1], reverse=True)

    # --- GROUP BY ROLE ---
    grouped = {
        "carry": [],
        "mid": [],
        "offlane": [],
        "support": []
    }

    for hero, score in results:
        role = get_primary_role(hero)
        grouped[role].append((hero, score))

    st.subheader("🎯 Recommended Picks")

    for role, heroes in grouped.items():
        if not heroes:
            continue

        st.markdown(f"### {role.upper()}")

        cols = st.columns(3)

        for i, (hero, score) in enumerate(heroes[:3]):
            with cols[i]:
                name = id_to_name[hero]

                st.markdown(f"""
                <div class="card">
                    <img src="{get_img(name)}" width="100">
                    <h4>{name}</h4>
                    <p>Score: {round(score, 3)}</p>
                </div>
                """, unsafe_allow_html=True)

                # --- EXPLANATION ---
                with st.expander("Why this hero?"):
                    reasons = explain(hero, st.session_state.enemy, st.session_state.team)
                    for r in reasons:
                        st.write(f"- {r}")