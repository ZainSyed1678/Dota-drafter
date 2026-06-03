import os
import pickle

from sqlalchemy import text

from config.database import engine


MODEL_DIR = os.getenv(
    "MODEL_DIR",
    "/app/model"
)
hero_map = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "hero_map.pkl"
        ),
        "rb"
    )
)

hero_winrate = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "hero_winrate.pkl"
        ),
        "rb"
    )
)

hero_avg_matchup = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "hero_avg_matchup.pkl"
        ),
        "rb"
    )
)

hero_roles = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "roles.pkl"
        ),
        "rb"
    )
)

matchups = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "matchup.pkl"
        ),
        "rb"
    )
)

synergies = pickle.load(
    open(
        os.path.join(
            MODEL_DIR,
            "synergy.pkl"
        ),
        "rb"
    )
)
with engine.begin() as conn:

    for hero_id, hero_name in hero_map.items():

        conn.execute(
            text(
                """
                INSERT INTO heroes(id, name)
                VALUES(:id, :name)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "id": hero_id,
                "name": hero_name
            }
        )

with engine.begin() as conn:

    for hero_id in hero_map:

        conn.execute(
            text(
                """
                INSERT INTO hero_stats
                (
                    hero_id,
                    winrate,
                    avg_matchup
                )
                VALUES
                (
                    :hero_id,
                    :winrate,
                    :avg_matchup
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "hero_id": hero_id,
                "winrate":
                    hero_winrate.get(
                        hero_id,
                        0.5
                    ),
                "avg_matchup":
                    hero_avg_matchup.get(
                        hero_id,
                        0.5
                    )
            }
        )

with engine.begin() as conn:

    for hero_id, roles in hero_roles.items():

        if isinstance(
            roles,
            str
        ):
            roles = [roles]

        for role in roles:

            conn.execute(
                text(
                    """
                    INSERT INTO hero_roles
                    (
                        hero_id,
                        role
                    )
                    VALUES
                    (
                        :hero_id,
                        :role
                    )
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "hero_id": hero_id,
                    "role": role
                }
            )

with engine.begin() as conn:

    for (
        hero_id,
        enemy_id
    ), matchup in matchups.items():

        conn.execute(
            text(
                """
                INSERT INTO matchups
                (
                    hero_id,
                    enemy_id,
                    matchup
                )
                VALUES
                (
                    :hero_id,
                    :enemy_id,
                    :matchup
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "hero_id": hero_id,
                "enemy_id": enemy_id,
                "matchup": matchup
            }
        )

with engine.begin() as conn:

    for (
        hero_id,
        ally_id
    ), synergy in synergies.items():

        conn.execute(
            text(
                """
                INSERT INTO synergies
                (
                    hero_id,
                    ally_id,
                    synergy
                )
                VALUES
                (
                    :hero_id,
                    :ally_id,
                    :synergy
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "hero_id": hero_id,
                "ally_id": ally_id,
                "synergy": synergy
            }
        )