from services.model_loader import model_store
from repositories.hero_repository import hero_repository


class RecommendationEngine:

    def __init__(self):

        self.repo = hero_repository

        self.hero_map = self.repo.get_hero_map()

        self.id_to_name = self.hero_map

        self.name_to_id = {
            v.lower(): k
            for k, v in self.hero_map.items()
        }

        print("Recommendation Engine Loaded")

    def resolve_names(self, names):

        result = []

        for name in names:

            hero_id = self.name_to_id.get(
                name.lower()
            )

            if hero_id is not None:
                result.append(hero_id)

        return result

    def get_roles(self, hero_id):

        roles = self.repo.get_roles(hero_id)

        if isinstance(roles, str):
            roles = [roles]

        return [
            role.lower()
            for role in roles
        ]

    def norm_matchup(
        self,
        hero_id,
        enemy_ids
    ):

        if not enemy_ids:
            return 0.0

        baseline = self.repo.get_avg_matchup(
            hero_id
        )

        total = 0.0

        for enemy_id in enemy_ids:

            raw = self.repo.get_matchup(
                hero_id,
                enemy_id
            )

            if raw is None:

                raw = self.repo.get_matchup(
                    enemy_id,
                    hero_id
                )

            if raw is None:
                raw = baseline

            total += raw - baseline

        return total / len(enemy_ids)

    def synergy_score(
        self,
        hero_id,
        ally_ids
    ):

        if not ally_ids:
            return 0.0

        total = 0.0

        for ally_id in ally_ids:

            value = self.repo.get_synergy(
                hero_id,
                ally_id
            )

            if value is None:

                value = self.repo.get_synergy(
                    ally_id,
                    hero_id
                )

            if value is None:
                value = 0.5

            total += value - 0.5

        return total / len(ally_ids)

    def build_reasons(
        self,
        hero_id,
        enemy_ids,
        enemy_names,
        ally_ids,
        ally_names
    ):

        reasons = []

        baseline = self.repo.get_avg_matchup(
            hero_id
        )

        counters = []
        neutral = []

        for eid, ename in zip(
            enemy_ids,
            enemy_names
        ):

            raw = self.repo.get_matchup(
                hero_id,
                eid
            )

            if raw is None:

                raw = self.repo.get_matchup(
                    eid,
                    hero_id
                )

            if raw is None:
                raw = baseline

            adj = raw - baseline

            if adj >= 0.01:

                counters.append(
                    (ename, adj)
                )

            elif adj >= -0.005:

                neutral.append(
                    (ename, adj)
                )

        counters.sort(
            key=lambda x: x[1],
            reverse=True
        )

        neutral.sort(
            key=lambda x: x[1],
            reverse=True
        )

        if counters:

            for name, adj in counters:

                reasons.append(
                    f"Counters {name} ({adj:+.3f} WR)"
                )

        elif neutral:

            for name, adj in neutral[:2]:

                reasons.append(
                    f"Even vs {name} ({adj:+.3f} WR)"
                )

        else:

            reasons.append(
                "Picked for synergy / meta"
            )

        syn = []

        for aid, aname in zip(
            ally_ids,
            ally_names
        ):

            value = self.repo.get_synergy(
                hero_id,
                aid
            )

            if value is None:

                value = self.repo.get_synergy(
                    aid,
                    hero_id
                )

            if value is None:
                value = 0.5

            adj = value - 0.5

            if adj >= 0.01:

                syn.append(
                    (aname, adj)
                )

        syn.sort(
            key=lambda x: x[1],
            reverse=True
        )

        for name, adj in syn[:2]:

            reasons.append(
                f"Synergy: {name} ({adj:+.3f} WR)"
            )

        winrate = self.repo.get_winrate(
            hero_id
        )

        if winrate > 0.53:

            reasons.append(
                f"Meta strong ({winrate:.1%} WR)"
            )

        return reasons

    def suggest(
        self,
        enemy_names,
        ally_names
    ):

        enemy_ids = self.resolve_names(
            enemy_names
        )

        ally_ids = self.resolve_names(
            ally_names
        )

        selected = set(
            enemy_ids + ally_ids
        )

        scored = []

        for hero_id in self.hero_map:

            if (
                hero_id in selected
            ):
                continue

            matchup = self.norm_matchup(
                hero_id,
                enemy_ids
            )

            synergy = self.synergy_score(
                hero_id,
                ally_ids
            )

            winrate = self.repo.get_winrate(
                hero_id
            )

            score = (
                1.50 * matchup
                + 0.35 * synergy
                + 0.06 * (winrate - 0.5)
            )

            if abs(matchup) < 0.005:
                score -= 0.02

            scored.append(
                (hero_id, score)
            )

        scored.sort(
            key=lambda x: x[1],
            reverse=True
        )

        result = []

        for hero_id, score in scored[:9]:

            result.append({
                "id": hero_id,
                "name": self.id_to_name[
                    hero_id
                ],
                "score": round(
                    score,
                    4
                ),
                "reasons": self.build_reasons(
                    hero_id,
                    enemy_ids,
                    enemy_names,
                    ally_ids,
                    ally_names
                ),
                "roles": self.get_roles(
                    hero_id
                )
            })

        return result


engine = RecommendationEngine()