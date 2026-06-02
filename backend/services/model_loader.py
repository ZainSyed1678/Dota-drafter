import os
import pickle


class ModelStore:

    def __init__(self):

        model_dir = os.getenv(
            "MODEL_DIR",
            "/app/model"
        )

        print(
            f"Loading models from: {model_dir}"
        )

        self.hero_map = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "hero_map.pkl"
                ),
                "rb"
            )
        )

        self.matchup_matrix = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "matchup.pkl"
                ),
                "rb"
            )
        )

        self.synergy_matrix = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "synergy.pkl"
                ),
                "rb"
            )
        )

        self.hero_roles = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "roles.pkl"
                ),
                "rb"
            )
        )

        self.hero_avg_matchup = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "hero_avg_matchup.pkl"
                ),
                "rb"
            )
        )

        self.hero_winrate = pickle.load(
            open(
                os.path.join(
                    model_dir,
                    "hero_winrate.pkl"
                ),
                "rb"
            )
        )

        print(
            "ModelStore loaded successfully"
        )


model_store = ModelStore()