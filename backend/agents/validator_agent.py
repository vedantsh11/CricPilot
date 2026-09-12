from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.models.team import FantasyTeam
from backend.tools.validator import ValidatorTool


class ValidatorAgent:
    """
    Agent responsible for independently validating fantasy teams.

    Candidate teams are stored in AgentState as dictionaries.
    This agent converts them back into FantasyTeam objects before
    passing them to the deterministic ValidatorTool.
    """

    name = "validator_agent"

    def __init__(self, state: AgentState) -> None:
        self.state = state
        self.validator_tool = ValidatorTool(state)

    def _candidate_to_team(
        self,
        candidate: dict[str, Any],
    ) -> FantasyTeam:
        """
        Convert a serialized candidate dictionary into a FantasyTeam.
        """

        players = []

        for player_id in candidate["player_ids"]:
            player = self.state.environment.get_player(player_id)

            if player is None:
                raise ValueError(
                    f"Player {player_id} was not found in the environment."
                )

            players.append(player)

        return FantasyTeam(
            id=candidate["team_id"],
            players=players,
            captain_id=candidate.get("captain_id"),
            vice_captain_id=candidate.get("vice_captain_id"),
            status=candidate.get("status", "draft"),
            projected_points=candidate.get(
                "projected_points",
                0.0,
            ),
            total_cost=candidate.get(
                "total_cost",
                0.0,
            ),
        )

    def validate_candidate(
        self,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate one candidate team independently.
        """

        team = self._candidate_to_team(candidate)

        result = self.validator_tool.validate_team(team)

        self.state.record_action(
            {
                "agent": self.name,
                "action": "validate_candidate",
                "team_id": candidate.get("team_id"),
                "valid": result.get("valid", False),
            }
        )

        self.state.record_tool_result(
            "validator",
            result,
        )

        return result

    def validate_candidates(
        self,
        candidates: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Validate all candidate teams independently.
        """

        if candidates is None:
            candidates = self.state.candidate_teams

        results = []

        for candidate in candidates:
            result = self.validate_candidate(candidate)
            results.append(result)

        valid_count = sum(
            1
            for result in results
            if result.get("valid", False)
        )

        self.state.record_action(
            {
                "agent": self.name,
                "action": "validate_candidates",
                "candidate_count": len(candidates),
                "valid_count": valid_count,
            }
        )

        return results

    def select_best_valid_candidate(
        self,
        candidates: list[dict[str, Any]] | None = None,
    ) -> FantasyTeam | None:
        """
        Validate candidates and select the highest-scoring valid team.
        """

        if candidates is None:
            candidates = self.state.candidate_teams

        valid_candidates = []

        for candidate in candidates:
            result = self.validate_candidate(candidate)

            if result.get("valid", False):
                valid_candidates.append(candidate)

        if not valid_candidates:
            self.state.record_action(
                {
                    "agent": self.name,
                    "action": "select_best_valid_candidate",
                    "selected": False,
                    "reason": "No valid candidate teams found.",
                }
            )

            return None

        best_candidate = max(
            valid_candidates,
            key=lambda candidate: candidate.get(
                "projected_points",
                candidate.get("score", 0.0),
            ),
        )

        team = self._candidate_to_team(best_candidate)

        self.state.set_current_team(team)

        self.state.record_action(
            {
                "agent": self.name,
                "action": "select_best_valid_candidate",
                "selected": True,
                "team_id": team.id,
                "projected_points": team.projected_points,
            }
        )

        return team

    def is_valid(
        self,
        candidate: dict[str, Any],
    ) -> bool:
        """
        Return True if the candidate satisfies all constraints.
        """

        team = self._candidate_to_team(candidate)

        return self.validator_tool.is_valid(team)


def create_validator_agent(
    state: AgentState,
) -> ValidatorAgent:

    return ValidatorAgent(state)