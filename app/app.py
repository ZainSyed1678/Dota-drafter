import streamlit as st
import pickle
from core import utils
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Dota 2 Drafter", layout="wide")

# --- LOAD FILES ---
utils.model = pickle.load(open("model/model.pkl", "rb"))
utils.hero_map = pickle.load(open("model/hero_map.pkl", "rb"))
utils.matchup_matrix = pickle.load(open("model/matchup.pkl", "rb"))
utils.synergy_matrix = pickle.load(open("model/synergy.pkl", "rb"))
utils.hero_roles = pickle.load(open("model/roles.pkl", "rb"))

# --- BUILD EXTRA ---
utils.hero_to_idx = {h: i for i, h in enumerate(utils.hero_map.keys())}
utils.NUM_HEROES = len(utils.hero_to_idx)
utils.hero_winrate = {h: 0.5 for h in utils.hero_map.keys()}

# --- STYLE ---
st.markdown("""
<style>
body {
    background-color: #0e0e0e;
}
.hero-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 10px;
    margin: 10px;
}
h1 {
    color: #ff4b4b;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Dota 2 Drafter")

hero_names = list(utils.hero_map.values())
name_to_id = {v: k for k, v in utils.hero_map.items()}

col1, col2 = st.columns(2)

with col1:
    enemy_team = st.multiselect("Enemy Team", hero_names)

with col2:
    my_team = st.multiselect("Your Team", hero_names)

enemy_ids = [name_to_id[n] for n in enemy_team]
my_ids = [name_to_id[n] for n in my_team]

if st.button("🔥 Suggest Picks"):
    results = utils.suggest(enemy_ids, my_ids)

    for hero, score in results:
        name = utils.hero_map[hero]
        reasons = utils.explain_pick(hero, enemy_ids, my_ids)

        st.markdown(f"""
        <div class="hero-card">
            <h3>{name}</h3>
            <p>Score: {round(score, 3)}</p>
            <p>{' | '.join(reasons)}</p>
        </div>
        """, unsafe_allow_html=True)