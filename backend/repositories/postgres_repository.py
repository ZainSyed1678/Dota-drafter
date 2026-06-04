from sqlalchemy import text

from config.database import engine


class PostgresRepository:

    def __init__(self):

        self.engine = engine

        self.hero_map_cache = {}
        self.winrate_cache = {}
        self.avg_matchup_cache = {}
        self.roles_cache = {}

        self.matchup_cache = {}
        self.synergy_cache = {}

        self._warm_cache()

    def stats(self):

     return {
        "total_heroes":
            len(self.hero_map_cache),

        "total_matchup_pairs":
            len(self.matchup_cache),

        "total_synergy_pairs":
            len(self.synergy_cache)
    }

    def _warm_cache(self):

        print("Loading repository cache...")

        with self.engine.connect() as conn:

            # Heroes
            heroes = conn.execute(
                text(
                    """
                    SELECT id, name
                    FROM heroes
                    """
                )
            )

            for row in heroes:

                self.hero_map_cache[
                    row.id
                ] = row.name

            # Hero stats
            stats = conn.execute(
                text(
                    """
                    SELECT
                        hero_id,
                        winrate,
                        avg_matchup
                    FROM hero_stats
                    """
                )
            )

            for row in stats:

                self.winrate_cache[
                    row.hero_id
                ] = row.winrate

                self.avg_matchup_cache[
                    row.hero_id
                ] = row.avg_matchup

            # Roles
            roles = conn.execute(
                text(
                    """
                    SELECT
                        hero_id,
                        role
                    FROM hero_roles
                    """
                )
            )

            for row in roles:

                self.roles_cache.setdefault(
                    row.hero_id,
                    []
                ).append(
                    row.role
                )

            # Matchups
            matchups = conn.execute(
                text(
                    """
                    SELECT
                        hero_id,
                        enemy_id,
                        matchup
                    FROM matchups
                    """
                )
            )

            for row in matchups:

                self.matchup_cache[
                    (
                        row.hero_id,
                        row.enemy_id
                    )
                ] = row.matchup

            # Synergies
            synergies = conn.execute(
                text(
                    """
                    SELECT
                        hero_id,
                        ally_id,
                        synergy
                    FROM synergies
                    """
                )
            )

            for row in synergies:

                self.synergy_cache[
                    (
                        row.hero_id,
                        row.ally_id
                    )
                ] = row.synergy

        print("Repository cache loaded")

        print(
            f"Heroes cached: {len(self.hero_map_cache)}"
        )

        print(
            f"Hero stats cached: {len(self.winrate_cache)}"
        )

        print(
            f"Role entries cached: {len(self.roles_cache)}"
        )

        print(
            f"Matchups cached: {len(self.matchup_cache)}"
        )

        print(
            f"Synergies cached: {len(self.synergy_cache)}"
        )

    def get_hero_map(self):

        return self.hero_map_cache

    def get_winrate(
        self,
        hero_id
    ):

        return self.winrate_cache.get(
            hero_id,
            0.5
        )

    def get_avg_matchup(
        self,
        hero_id
    ):

        return self.avg_matchup_cache.get(
            hero_id,
            0.5
        )

    def get_roles(
        self,
        hero_id
    ):

        return self.roles_cache.get(
            hero_id,
            []
        )

    def get_matchup(
        self,
        hero_id,
        enemy_id
    ):

        return self.matchup_cache.get(
            (
                hero_id,
                enemy_id
            )
        )

    def get_synergy(
        self,
        hero_id,
        ally_id
    ):

        return self.synergy_cache.get(
            (
                hero_id,
                ally_id
            )
        )


postgres_repository = PostgresRepository()