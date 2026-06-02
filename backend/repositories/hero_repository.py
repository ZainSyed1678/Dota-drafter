from services.model_loader import model_store


class HeroRepository:

    def __init__(self):

        self.hero_map = model_store.hero_map
        self.matchup_matrix = model_store.matchup_matrix
        self.synergy_matrix = model_store.synergy_matrix
        self.hero_roles = model_store.hero_roles
        self.hero_avg_matchup = model_store.hero_avg_matchup
        self.hero_winrate = model_store.hero_winrate

    def get_hero_map(self):
        return self.hero_map

    def get_matchup(self, hero_id, enemy_id):

        return self.matchup_matrix.get(
            (hero_id, enemy_id)
        )

    def get_synergy(self, hero_id, ally_id):

        return self.synergy_matrix.get(
            (hero_id, ally_id)
        )

    def get_roles(self, hero_id):

        return self.hero_roles.get(
            hero_id,
            ["offlane"]
        )

    def get_avg_matchup(
        self,
        hero_id
    ):

        return self.hero_avg_matchup.get(
            hero_id,
            0.5
        )

    def get_winrate(
        self,
        hero_id
    ):

        return self.hero_winrate.get(
            hero_id,
            0.5
        )


hero_repository = HeroRepository()