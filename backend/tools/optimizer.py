from __future__ import annotations

from itertools import combinations
from typing import Any

from backend.models.player import Player
from backend.models.state import AgentState
from backend.models.team import FantasyTeam


class OptimizerTool:
    """
    Deterministic fantasy-team optimizer.

    The optimizer generates feasible candidate teams using the current
    environment and hard fantasy constraints.

    It does not:
    - call an LLM,
    - execute platform actions,
    - modify the environment,
    - decide which candidate the autonomous agent should finally use.

    Those responsibilities belong to the agent/orchestration layer.
    """

    name = "optimizer"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def generate_candidates(
        self,
        limit: int = 10,
    ) -> list[FantasyTeam]:
        """
        Generate and rank feasible fantasy-team candidates.

        Candidates are built from currently selectable players and are
        ranked using a deterministic player score.
        """
        if limit <= 0:
            return []

        players = self._get_selectable_players()

        if len(players) < self.state.constraints.squad_size:
            return []

        ranked_players = sorted(
            players,
            key=self._player_score,
            reverse=True,
        )

        candidates = self._search_candidates(
            ranked_players,
            limit,
        )

        candidates.sort(
            key=self._team_score,
            reverse=True,
        )

        return candidates[:limit]

    def generate_candidate_dicts(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate candidates and return tool-friendly dictionaries."""
        return [
            self._serialize_team(team)
            for team in self.generate_candidates(limit)
        ]

    def optimize(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Public optimizer entry point.

        Returns ranked candidate teams as dictionaries.
        """
        return self.generate_candidate_dicts(limit)

    def score_player(self, player: Player) -> float:
        """
        Calculate a deterministic player-selection score.

        The score combines:
        - fantasy average,
        - fantasy ceiling,
        - recent form,
        - consistency,
        - upside,
        - venue performance.
        """
        return self._player_score(player)

    def score_team(self, team: FantasyTeam) -> float:
        """Calculate the deterministic score of a fantasy team."""
        return self._team_score(team)

    def _get_selectable_players(self) -> list[Player]:
        """Return players who can currently be selected."""
        return [
            player
            for player in self.state.environment.players.values()
            if player.is_selectable()
        ]

    def _player_score(self, player: Player) -> float:
        """
        Calculate a weighted player score.

        This is intentionally deterministic so results are reproducible
        during the hackathon demo.
        """
        return (
            player.fantasy_avg * 0.30
            + player.fantasy_ceiling * 0.20
            + player.recent_form * 0.20
            + player.consistency_rating * 0.10
            + player.upside_rating * 0.08
            + player.form_rating * 0.07
            + player.venue_rating * 0.05
        )

    def _search_candidates(
        self,
        players: list[Player],
        limit: int,
    ) -> list[FantasyTeam]:
        """
        Search for feasible teams using bounded combinations.

        Players are already ranked by score, so the search prioritizes
        strong candidates while avoiding an unrestricted 42-player
        combinatorial explosion.
        """
        constraints = self.state.constraints
        squad_size = constraints.squad_size

        # Keep the search space manageable while retaining role diversity.
        search_pool = self._build_search_pool(players)

        candidates: list[FantasyTeam] = []
        seen: set[tuple[str, ...]] = set()

        # Start with role-aware combinations rather than blindly trying
        # every possible squad-size combination.
        for combination in combinations(search_pool, squad_size):
            player_ids = tuple(
                sorted(player.id for player in combination)
            )

            if player_ids in seen:
                continue

            seen.add(player_ids)

            if not self._is_feasible(combination):
                continue

            team = FantasyTeam(
                id=f"CANDIDATE_{len(candidates) + 1}",
                players=list(combination),
            )

            team.calculate_cost()
            team.projected_points = self._team_score(team)

            candidates.append(team)

            # Once we have enough feasible candidates, continue only
            # through a bounded number of combinations.
            if len(candidates) >= max(limit * 5, 25):
                break

        return candidates

    def _build_search_pool(
        self,
        players: list[Player],
    ) -> list[Player]:
        """
        Build a bounded search pool.

        We retain strong players from every role so the optimizer does
        not accidentally eliminate an entire role category.
        """
        role_limits = {
            "wicketkeeper": 6,
            "batter": 12,
            "all_rounder": 10,
            "bowler": 12,
        }

        grouped: dict[str, list[Player]] = {
            role: []
            for role in role_limits
        }

        for player in players:
            role = player.role.value
            if role in grouped:
                grouped[role].append(player)

        pool: list[Player] = []

        for role, role_players in grouped.items():
            role_players.sort(
                key=self._player_score,
                reverse=True,
            )
            pool.extend(
                role_players[:role_limits[role]]
            )

        # Remove accidental duplicates while preserving ranking.
        unique_players = {
            player.id: player
            for player in pool
        }

        return sorted(
            unique_players.values(),
            key=self._player_score,
            reverse=True,
        )

    def _is_feasible(
        self,
        players: tuple[Player, ...],
    ) -> bool:
        """Check all hard squad constraints."""
        constraints = self.state.constraints

        if len(players) != constraints.squad_size:
            return False

        total_cost = sum(
            player.credits
            for player in players
        )

        if total_cost > constraints.budget:
            return False

        role_counts = {
            "wicketkeeper": 0,
            "batter": 0,
            "all_rounder": 0,
            "bowler": 0,
        }

        team_counts: dict[str, int] = {}

        for player in players:
            role_counts[player.role.value] += 1

            team_counts[player.real_team] = (
                team_counts.get(player.real_team, 0) + 1
            )

            if (
                team_counts[player.real_team]
                > constraints.max_players_per_real_team
            ):
                return False

        if (
            role_counts["wicketkeeper"]
            < constraints.min_wicketkeepers
        ):
            return False

        if (
            role_counts["batter"]
            < constraints.min_batters
        ):
            return False

        if (
            role_counts["all_rounder"]
            < constraints.min_all_rounders
        ):
            return False

        if (
            role_counts["bowler"]
            < constraints.min_bowlers
        ):
            return False

        # Preferred players are treated as soft preferences, not hard
        # constraints. Avoided players are also handled as soft
        # preferences at this stage so the optimizer can still return
        # feasible candidates when the preference is impossible.
        return True

    def _team_score(
        self,
        team: FantasyTeam,
    ) -> float:
        """
        Calculate total deterministic candidate score.

        Preferred players receive a bonus and avoided players receive
        a penalty.
        """
        score = sum(
            self._player_score(player)
            for player in team.players
        )

        preferred = set(
            self.state.preferences.preferred_players
        )
        avoided = set(
            self.state.preferences.avoided_players
        )

        for player in team.players:
            if player.id in preferred:
                score += 10.0

            if player.id in avoided:
                score -= 10.0

        return round(score, 2)

    def _serialize_team(
        self,
        team: FantasyTeam,
    ) -> dict[str, Any]:
        """Convert a FantasyTeam into tool-friendly output."""
        return {
            "team_id": team.id,
            "player_ids": team.player_ids,
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "real_team": player.real_team,
                    "role": player.role.value,
                    "credits": player.credits,
                }
                for player in team.players
            ],
            "size": team.size,
            "total_cost": team.total_cost,
            "projected_points": team.projected_points,
            "score": self._team_score(team),
        }


def create_optimizer_tool(
    state: AgentState,
) -> OptimizerTool:
    """Create an optimizer tool for the current agent state."""
    return OptimizerTool(state)