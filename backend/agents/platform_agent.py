from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.models.team import FantasyTeam
from backend.tools.fantasy_platform import FantasyPlatformTool


class PlatformAgent:
    """
    Agent responsible for interacting with the simulated fantasy platform.
    """

    name = "platform_agent"

    def __init__(self, state: AgentState) -> None:
        self.state = state
        self.platform_tool = FantasyPlatformTool(state)

    def create_team(
        self,
        team: FantasyTeam | None = None,
    ) -> dict[str, Any]:
        """
        Create the supplied team or the current agent team
        on the simulated fantasy platform.
        """

        if team is None:
            team = self.state.current_team

        if team is None:
            result = {
                "success": False,
                "action": "create_team",
                "message": "No current team is available.",
            }

            self.state.record_action({
                "agent": self.name,
                "action": "create_team",
                "success": False,
            })

            self.state.record_tool_result(
                "fantasy_platform",
                result,
            )

            return result

        result = self.platform_tool.create_team(team)

        self.state.record_action({
            "agent": self.name,
            "action": "create_team",
            "team_id": team.id,
            "success": bool(result.get("success", False)),
        })

        self.state.record_tool_result(
            "fantasy_platform",
            result,
        )

        return result

    def swap_player(
        self,
        player_out_id: str,
        player_in_id: str,
    ) -> dict[str, Any]:
        """
        Swap one player on the simulated fantasy platform.
        """

        result = self.platform_tool.swap_player(
            player_out_id=player_out_id,
            player_in_id=player_in_id,
        )

        self.state.record_action({
            "agent": self.name,
            "action": "swap_player",
            "player_out": player_out_id,
            "player_in": player_in_id,
            "success": bool(result.get("success", False)),
        })

        self.state.record_tool_result(
            "fantasy_platform",
            result,
        )

        return result

    def verify_swap(
        self,
        player_out_id: str,
        player_in_id: str,
    ) -> dict[str, Any]:
        """
        Verify that the requested player swap actually happened.
        """

        platform_state = (
            self.platform_tool.get_platform_state()
        )

        player_ids = platform_state.get(
            "player_ids",
            [],
        )

        if not isinstance(
            player_ids,
            (list, tuple, set),
        ):
            player_ids = []

        out_removed = player_out_id not in player_ids
        in_added = player_in_id in player_ids

        verified = (
            out_removed
            and in_added
        )

        result = {
            "verified": verified,
            "player_out": player_out_id,
            "player_in": player_in_id,
            "out_removed": out_removed,
            "in_added": in_added,
            "platform_state": platform_state,
        }

        self.state.record_action({
            "agent": self.name,
            "action": "verify_swap",
            "player_out": player_out_id,
            "player_in": player_in_id,
            "verified": verified,
        })

        self.state.record_tool_result(
            "fantasy_platform_swap_verification",
            result,
        )

        return result

    def get_platform_state(self) -> dict[str, Any]:
        """
        Observe the current state of the simulated platform.
        """

        result = (
            self.platform_tool.get_platform_state()
        )

        self.state.record_observation({
            "source": self.name,
            "type": "platform_state",
            "data": result,
        })

        return result

    def verify_created_team(self) -> dict[str, Any]:
        """
        Verify that the platform contains the expected current team.
        """

        platform_state = (
            self.platform_tool.get_platform_state()
        )

        current_team = self.state.current_team

        if current_team is None:

            result = {
                "verified": False,
                "reason": (
                    "No current team exists "
                    "in agent state."
                ),
                "platform_state": platform_state,
            }

        elif not platform_state.get(
            "has_active_team",
            False,
        ):

            result = {
                "verified": False,
                "reason": (
                    "Platform does not contain "
                    "an active team."
                ),
                "platform_state": platform_state,
            }

        elif platform_state.get(
            "team_id"
        ) != current_team.id:

            result = {
                "verified": False,
                "reason": (
                    "Platform team does not match "
                    "current team."
                ),
                "platform_state": platform_state,
            }

        else:

            result = {
                "verified": True,
                "reason": (
                    "Platform team matches "
                    "current team."
                ),
                "team_id": current_team.id,
                "platform_state": platform_state,
            }

        self.state.record_action({
            "agent": self.name,
            "action": "verify_created_team",
            "verified": result["verified"],
        })

        self.state.record_tool_result(
            "fantasy_platform_verification",
            result,
        )

        return result


def create_platform_agent(
    state: AgentState,
) -> PlatformAgent:
    """
    Factory function for creating a PlatformAgent.
    """

    return PlatformAgent(state)