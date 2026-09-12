from __future__ import annotations

from typing import Any

from backend.models.player import AvailabilityStatus
from backend.models.state import AgentState


class AvailabilityTool:
    """
    Deterministic tool for checking player availability.

    The tool reads the current environment state and reports whether
    players are available, doubtful, or unavailable.

    It does not select or modify players.
    """

    name = "availability"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def get_player_status(
        self,
        player_id: str,
    ) -> dict[str, Any] | None:
        """
        Return the current availability status of one player.

        Returns None if the player does not exist.
        """
        player = self.state.environment.get_player(player_id)

        if player is None:
            return None

        return {
            "player_id": player.id,
            "player_name": player.name,
            "real_team": player.real_team,
            "status": player.availability.value,
            "selectable": player.is_selectable(),
            "reason": player.availability_reason,
        }

    def is_available(self, player_id: str) -> bool:
        """Return True when a player is currently selectable."""
        player = self.state.environment.get_player(player_id)

        if player is None:
            return False

        return player.availability == AvailabilityStatus.AVAILABLE

    def get_available_players(self) -> list[dict[str, Any]]:
        """Return all currently available players."""
        return self._get_players_by_status(
            AvailabilityStatus.AVAILABLE
        )

    def get_doubtful_players(self) -> list[dict[str, Any]]:
        """Return all players currently marked doubtful."""
        return self._get_players_by_status(
            AvailabilityStatus.DOUBTFUL
        )

    def get_unavailable_players(self) -> list[dict[str, Any]]:
        """Return all players currently unavailable."""
        return self._get_players_by_status(
            AvailabilityStatus.UNAVAILABLE
        )

    def get_unavailable_reasons(self) -> list[dict[str, Any]]:
        """
        Return unavailable players together with the reason
        they cannot currently be selected.
        """
        players = self.state.environment.players.values()

        return [
            {
                "player_id": player.id,
                "player_name": player.name,
                "reason": player.availability_reason,
            }
            for player in players
            if player.availability == AvailabilityStatus.UNAVAILABLE
        ]

    def get_availability_snapshot(self) -> dict[str, Any]:
        """
        Return a complete availability snapshot.

        The environment version is included so the agent can compare
        snapshots and detect whether the environment has changed.
        """
        players = self.state.environment.players.values()

        counts = {
            AvailabilityStatus.AVAILABLE.value: 0,
            AvailabilityStatus.DOUBTFUL.value: 0,
            AvailabilityStatus.UNAVAILABLE.value: 0,
        }

        for player in players:
            counts[player.availability.value] += 1

        return {
            "environment_version": self.state.environment.version,
            "total_players": len(self.state.environment.players),
            "available": counts["available"],
            "doubtful": counts["doubtful"],
            "unavailable": counts["unavailable"],
            "players": [
                self.get_player_status(player.id)
                for player in players
            ],
        }

    def has_availability_changed(
        self,
        previous_snapshot: dict[str, Any],
    ) -> bool:
        """
        Determine whether availability changed since a previous snapshot.

        The comparison is based on player IDs and their availability
        statuses, rather than relying only on environment version.
        """
        previous_players = {
            player["player_id"]: player["status"]
            for player in previous_snapshot.get("players", [])
        }

        current_players = {
            player.id: player.availability.value
            for player in self.state.environment.players.values()
        }

        return previous_players != current_players

    def _get_players_by_status(
        self,
        status: AvailabilityStatus,
    ) -> list[dict[str, Any]]:
        """Return basic availability information for a given status."""
        players = self.state.environment.players.values()

        return [
            {
                "player_id": player.id,
                "player_name": player.name,
                "real_team": player.real_team,
                "status": player.availability.value,
                "selectable": player.is_selectable(),
                "reason": player.availability_reason,
            }
            for player in players
            if player.availability == status
        ]


def create_availability_tool(
    state: AgentState,
) -> AvailabilityTool:
    """Create an availability tool for the current agent state."""
    return AvailabilityTool(state)