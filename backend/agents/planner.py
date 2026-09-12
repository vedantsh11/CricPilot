from __future__ import annotations

from typing import Any

from backend.models.state import AgentState


class PlannerAgent:
    """
    Decides the next action in the CricPilot workflow.

    The planner does not:
    - generate teams
    - validate constraints
    - execute platform actions

    It only looks at the current state and chooses what
    should happen next.
    """

    name = "planner_agent"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def plan(self) -> dict[str, Any]:
        """
        Decide the next action based on the current agent state.
        """

        # --------------------------------------------------
        # 1. Environment changed while a team exists
        # --------------------------------------------------

        if (
            self.state.current_team is not None
            and self._environment_changed()
        ):
            return self._create_plan(
                action="REPLAN",
                reason=(
                    "The environment changed after a team was created. "
                    "The current team must be re-evaluated."
                ),
            )

        # --------------------------------------------------
        # 2. No candidate teams exist
        # --------------------------------------------------

        if not self.state.candidate_teams:
            return self._create_plan(
                action="GENERATE_CANDIDATES",
                reason=(
                    "No candidate teams are available, "
                    "so the optimizer should generate them."
                ),
            )

        # --------------------------------------------------
        # 3. Candidates exist but no current team exists
        # --------------------------------------------------

        if self.state.current_team is None:
            return self._create_plan(
                action="VALIDATE_CANDIDATE",
                reason=(
                    "Candidate teams exist but no current team "
                    "has been selected yet."
                ),
            )

        # --------------------------------------------------
        # 4. A current team exists and environment is stable
        # --------------------------------------------------

        return self._create_plan(
            action="VERIFY_TEAM",
            reason=(
                "A current team exists and the environment "
                "has not changed. The team should be verified."
            ),
        )

    def _environment_changed(self) -> bool:
        """
        Check whether the latest observation reports
        an environment change.
        """

        if not self.state.observations:
            return False

        latest_observation = self.state.observations[-1]

        changes = latest_observation.get("changes", {})

        return bool(
            changes.get("environment_changed", False)
        )

    def _create_plan(
        self,
        action: str,
        reason: str,
    ) -> dict[str, Any]:
        """
        Create and record a structured planning decision.
        """

        plan = {
            "agent": self.name,
            "action": action,
            "reason": reason,
            "revision": self.state.revisions,
            "environment_version": (
                self.state.environment.version
            ),
        }

        self.state.record_action(plan)

        return plan


def create_planner_agent(
    state: AgentState,
) -> PlannerAgent:
    return PlannerAgent(state)