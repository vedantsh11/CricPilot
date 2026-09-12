from __future__ import annotations

from typing import Any

from backend.models.player import Player, PlayerRole
from backend.models.state import AgentState


class PlayerStatsTool:
    """
    Deterministic tool for retrieving player statistics.

    The tool reads player information from the current AgentState.
    It does not make team-selection decisions.
    """

    name = "player_stats"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def get_player(self, player_id: str) -> dict[str, Any] | None:
        """
        Return complete statistics for one player.

        Returns None if the player does not exist.
        """
        player = self.state.environment.get_player(player_id)

        if player is None:
            return None

        return self._serialize_player(player)

    def get_all_players(self) -> list[dict[str, Any]]:
        """Return statistics for every player in the environment."""
        players = self.state.environment.players.values()

        return [
            self._serialize_player(player)
            for player in players
        ]

    def get_available_players(self) -> list[dict[str, Any]]:
        """Return statistics for currently selectable players."""
        players = self.state.environment.players.values()

        return [
            self._serialize_player(player)
            for player in players
            if player.is_selectable()
        ]

    def get_players_by_role(
        self,
        role: PlayerRole | str,
    ) -> list[dict[str, Any]]:
        """Return players matching a specific role."""
        if isinstance(role, str):
            try:
                role = PlayerRole(role)
            except ValueError:
                return []

        players = self.state.environment.players.values()

        return [
            self._serialize_player(player)
            for player in players
            if player.role == role
        ]

    def get_players_by_team(
        self,
        real_team: str,
    ) -> list[dict[str, Any]]:
        """Return players belonging to a real-world team."""
        team = real_team.upper()

        players = self.state.environment.players.values()

        return [
            self._serialize_player(player)
            for player in players
            if player.real_team.upper() == team
        ]

    def search_players(
        self,
        role: PlayerRole | str | None = None,
        real_team: str | None = None,
        available_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Retrieve players using optional filters.

        Filters can be combined.
        """
        players = self.state.environment.players.values()

        if isinstance(role, str):
            try:
                role = PlayerRole(role)
            except ValueError:
                return []

        results: list[dict[str, Any]] = []

        for player in players:

            if role is not None and player.role != role:
                continue

            if (
                real_team is not None
                and player.real_team.upper() != real_team.upper()
            ):
                continue

            if available_only and not player.is_selectable():
                continue

            results.append(
                self._serialize_player(player)
            )

        return results

    def get_top_players(
        self,
        limit: int = 10,
        available_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Return players ranked by a deterministic fantasy-stat score.

        This ranking is only a retrieval aid.
        The optimizer remains responsible for constructing the team.
        """
        if limit <= 0:
            return []

        players = self.search_players(
            available_only=available_only
        )

        players.sort(
            key=lambda player: (
                player["fantasy_avg"]
                + player["fantasy_ceiling"] * 0.5
                + player["recent_form"]
            ),
            reverse=True,
        )

        return players[:limit]

    def _serialize_player(
        self,
        player: Player,
    ) -> dict[str, Any]:
        """Convert a Player model into tool-friendly data."""
        return {
            "id": player.id,
            "name": player.name,
            "real_team": player.real_team,
            "role": player.role.value,
            "credits": player.credits,
            "fantasy_avg": player.fantasy_avg,
            "fantasy_ceiling": player.fantasy_ceiling,
            "recent_points": list(player.recent_points),
            "recent_form": player.recent_form,
            "risk_score": player.risk_score,
            "batting_rating": player.batting_rating,
            "bowling_rating": player.bowling_rating,
            "form_rating": player.form_rating,
            "consistency_rating": player.consistency_rating,
            "upside_rating": player.upside_rating,
            "powerplay_rating": player.powerplay_rating,
            "death_overs_rating": player.death_overs_rating,
            "pace_rating": player.pace_rating,
            "spin_rating": player.spin_rating,
            "venue_rating": player.venue_rating,
            "availability": player.availability.value,
            "availability_reason": player.availability_reason,
        }


def create_player_stats_tool(
    state: AgentState,
) -> PlayerStatsTool:
    """Create a player statistics tool for the current agent state."""
    return PlayerStatsTool(state)