from __future__ import annotations

from typing import Any

from backend.models.team import FantasyTeam
from backend.models.state import AgentState


class ValidatorTool:
    """
    Deterministic validator for fantasy teams.

    This tool independently checks hard constraints.
    It does not generate, optimize, or modify teams.
    """

    name = "validator"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def validate_team(self, team: FantasyTeam) -> dict[str, Any]:
        checks = {
            "squad_size": self._check_squad_size(team),
            "budget": self._check_budget(team),
            "max_players_per_real_team": self._check_max_players_per_real_team(team),
            "wicketkeepers": self._check_role_minimum(team, "wicketkeeper"),
            "batters": self._check_role_minimum(team, "batter"),
            "all_rounders": self._check_role_minimum(team, "all_rounder"),
            "bowlers": self._check_role_minimum(team, "bowler"),
            "player_availability": self._check_player_availability(team),
        }

        valid = all(check["valid"] for check in checks.values())

        return {
            "team_id": team.id,
            "valid": valid,
            "checks": checks,
            "total_cost": round(team.calculate_cost(), 2),
            "squad_size": team.size,
        }

    def validate_teams(
        self,
        teams: list[FantasyTeam],
    ) -> list[dict[str, Any]]:
        return [self.validate_team(team) for team in teams]

    def is_valid(self, team: FantasyTeam) -> bool:
        return self.validate_team(team)["valid"]

    def _check_squad_size(self, team: FantasyTeam) -> dict[str, Any]:
        actual = team.size
        required = self.state.constraints.squad_size

        return {
            "valid": actual == required,
            "actual": actual,
            "required": required,
        }

    def _check_budget(self, team: FantasyTeam) -> dict[str, Any]:
        actual = team.calculate_cost()
        limit = self.state.constraints.budget

        return {
            "valid": actual <= limit,
            "actual": round(actual, 2),
            "limit": limit,
        }

    def _check_max_players_per_real_team(
        self,
        team: FantasyTeam,
    ) -> dict[str, Any]:
        limit = self.state.constraints.max_players_per_real_team

        team_counts: dict[str, int] = {}

        for player in team.players:
            team_counts[player.real_team] = (
                team_counts.get(player.real_team, 0) + 1
            )

        maximum = max(team_counts.values(), default=0)

        return {
            "valid": maximum <= limit,
            "maximum": maximum,
            "limit": limit,
            "team_counts": team_counts,
        }

    def _check_role_minimum(
        self,
        team: FantasyTeam,
        role_name: str,
    ) -> dict[str, Any]:
        role_map = {
            "wicketkeeper": self.state.constraints.min_wicketkeepers,
            "batter": self.state.constraints.min_batters,
            "all_rounder": self.state.constraints.min_all_rounders,
            "bowler": self.state.constraints.min_bowlers,
        }

        required = role_map[role_name]

        actual = sum(
            1
            for player in team.players
            if player.role.value == role_name
        )

        return {
            "valid": actual >= required,
            "actual": actual,
            "required": required,
        }

    def _check_player_availability(
        self,
        team: FantasyTeam,
    ) -> dict[str, Any]:
        unavailable = [
            {
                "player_id": player.id,
                "player_name": player.name,
                "reason": player.availability_reason,
            }
            for player in team.players
            if not player.is_selectable
        ]

        return {
            "valid": len(unavailable) == 0,
            "unavailable_players": unavailable,
        }


def create_validator_tool(state: AgentState) -> ValidatorTool:
    return ValidatorTool(state)