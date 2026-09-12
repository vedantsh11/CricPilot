
from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.models.team import FantasyTeam


class FantasyPlatformTool:
    """
    Simulated fantasy sports platform.

    This tool represents the external environment where the agent
    creates, modifies, and submits fantasy teams.

    It does NOT interact with any real fantasy sports platform.
    """

    name = "fantasy_platform"

    def __init__(self, state: AgentState) -> None:
        self.state = state

        # Simulated platform state
        self.active_team: FantasyTeam | None = None
        self.submitted: bool = False

    # ============================================================
    # CREATE TEAM
    # ============================================================

    def create_team(
        self,
        team: FantasyTeam,
    ) -> dict[str, Any]:
        """
        Create a fantasy team on the simulated platform.
        """

        if self.active_team is not None:
            return {
                "success": False,
                "action": "create_team",
                "message": "An active team already exists.",
                "team_id": self.active_team.id,
            }

        if team.size != self.state.constraints.squad_size:
            return {
                "success": False,
                "action": "create_team",
                "message": (
                    "Team size does not match the required squad size."
                ),
                "team_id": team.id,
                "actual_size": team.size,
                "required_size": self.state.constraints.squad_size,
            }

        self.active_team = self._copy_team(team)
        self.submitted = False

        return {
            "success": True,
            "action": "create_team",
            "message": "Team created successfully.",
            "team_id": self.active_team.id,
            "player_ids": self.active_team.player_ids,
        }

    # ============================================================
    # SWAP PLAYER
    # ============================================================

    def swap_player(
        self,
        player_out_id: str,
        player_in_id: str,
    ) -> dict[str, Any]:
        """
        Swap one player in the active fantasy team.

        The incoming player must:
        - exist in the environment
        - be available
        - not already be in the team

        The outgoing player must:
        - exist in the current team
        """

        if self.active_team is None:
            return {
                "success": False,
                "action": "swap_player",
                "message": "No active team exists.",
            }

        if self.submitted:
            return {
                "success": False,
                "action": "swap_player",
                "message": "Submitted teams cannot be modified.",
            }

        player_out = self.state.environment.get_player(
            player_out_id
        )

        player_in = self.state.environment.get_player(
            player_in_id
        )

        if player_out is None:
            return {
                "success": False,
                "action": "swap_player",
                "message": f"Outgoing player {player_out_id} was not found.",
            }

        if player_in is None:
            return {
                "success": False,
                "action": "swap_player",
                "message": f"Incoming player {player_in_id} was not found.",
            }

        if not self.active_team.contains_player(player_out_id):
            return {
                "success": False,
                "action": "swap_player",
                "message": (
                    f"Player {player_out_id} is not in the active team."
                ),
            }

        if self.active_team.contains_player(player_in_id):
            return {
                "success": False,
                "action": "swap_player",
                "message": (
                    f"Player {player_in_id} is already in the active team."
                ),
            }

        if not player_in.is_selectable:
            return {
                "success": False,
                "action": "swap_player",
                "message": (
                    f"Player {player_in_id} is not available for selection."
                ),
                "player_id": player_in_id,
                "availability": player_in.availability,
                "availability_reason": player_in.availability_reason,
            }

        # Remove outgoing player
        self.active_team.remove_player(player_out_id)

        # Add incoming player
        self.active_team.add_player(player_in)

        # Keep team size unchanged
        self.active_team.total_cost = (
            self.active_team.calculate_cost()
        )

        return {
            "success": True,
            "action": "swap_player",
            "message": "Player swapped successfully.",
            "team_id": self.active_team.id,
            "player_out": player_out_id,
            "player_in": player_in_id,
            "player_ids": self.active_team.player_ids,
            "total_cost": self.active_team.total_cost,
        }

    # ============================================================
    # SUBMIT TEAM
    # ============================================================

    def submit_team(self) -> dict[str, Any]:
        """
        Submit the active team on the simulated platform.
        """

        if self.active_team is None:
            return {
                "success": False,
                "action": "submit_team",
                "message": "No active team exists.",
            }

        if self.submitted:
            return {
                "success": False,
                "action": "submit_team",
                "message": "Team has already been submitted.",
                "team_id": self.active_team.id,
            }

        self.submitted = True

        return {
            "success": True,
            "action": "submit_team",
            "message": "Team submitted successfully.",
            "team_id": self.active_team.id,
            "player_ids": self.active_team.player_ids,
            "total_cost": self.active_team.total_cost,
        }

    # ============================================================
    # GET ACTIVE TEAM
    # ============================================================

    def get_active_team(self) -> FantasyTeam | None:
        """
        Return a copy of the currently active team.
        """

        if self.active_team is None:
            return None

        return self._copy_team(self.active_team)

    # ============================================================
    # GET PLATFORM STATE
    # ============================================================

    def get_platform_state(self) -> dict[str, Any]:
        """
        Return a serializable snapshot of the simulated platform.
        """

        if self.active_team is None:
            return {
                "has_active_team": False,
                "team_id": None,
                "submitted": False,
                "player_ids": [],
            }

        return {
            "has_active_team": True,
            "team_id": self.active_team.id,
            "submitted": self.submitted,
            "player_ids": self.active_team.player_ids,
        }

    # ============================================================
    # COPY TEAM
    # ============================================================

    def _copy_team(
        self,
        team: FantasyTeam,
    ) -> FantasyTeam:
        """
        Create a separate FantasyTeam object.

        This prevents the simulated platform from directly sharing
        the same mutable team object with AgentState.
        """

        return FantasyTeam(
            id=team.id,
            players=list(team.players),
            captain_id=team.captain_id,
            vice_captain_id=team.vice_captain_id,
            status=team.status,
            projected_points=team.projected_points,
            total_cost=team.total_cost,
        )


def create_fantasy_platform_tool(
    state: AgentState,
) -> FantasyPlatformTool:

    return FantasyPlatformTool(state)
