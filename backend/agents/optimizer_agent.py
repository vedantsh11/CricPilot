from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.tools.optimizer import OptimizerTool


class OptimizerAgent:
    """
    Agent responsible for generating candidate fantasy teams.

    The agent decides when to invoke the deterministic optimizer.
    It does not perform constraint calculations itself.
    """

    name = "optimizer_agent"

    def __init__(self, state: AgentState) -> None:
        self.state = state
        self.optimizer_tool = OptimizerTool(state)

    def generate_candidates(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Generate candidate teams using the deterministic optimizer.
        """

        candidates = self.optimizer_tool.generate_candidate_dicts(
            limit=limit
        )

        self.state.clear_candidate_teams()

        for candidate in candidates:
            self.state.add_candidate_team(candidate)

        self.state.record_action(
            {
                "agent": self.name,
                "action": "generate_candidates",
                "candidate_count": len(candidates),
                "limit": limit,
            }
        )

        return candidates

    def optimize(self, limit: int = 10) -> dict[str, Any]:
        """
        Run the optimization step and return a structured result.
        """

        candidates = self.generate_candidates(limit=limit)

        result = {
            "success": len(candidates) > 0,
            "candidate_count": len(candidates),
            "candidates": candidates,
        }

        self.state.record_tool_result(
    "optimizer",
    result
)
        

        return result


def create_optimizer_agent(state: AgentState) -> OptimizerAgent:
    return OptimizerAgent(state)