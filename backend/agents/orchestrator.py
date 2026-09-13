from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.models.team import FantasyTeam
from backend.simulation.environment import SimulationEnvironment

from backend.agents.monitor_agent import MonitorAgent
from backend.agents.optimizer_agent import OptimizerAgent
from backend.agents.planner import PlannerAgent
from backend.agents.validator_agent import ValidatorAgent
from backend.agents.platform_agent import PlatformAgent


class Orchestrator:
    """
    Coordinates the CricPilot autonomous agent workflow.

    Initial workflow:

        OBSERVE
            ↓
        PLAN
            ↓
        GENERATE CANDIDATES
            ↓
        VALIDATE + SELECT
            ↓
        CREATE TEAM
            ↓
        VERIFY

    Adaptation workflow:

        OBSERVE
            ↓
        DETECT CHANGE
            ↓
        REPLAN
            ↓
        FIND REPLACEMENT
            ↓
        VALIDATE ADAPTED TEAM
            ↓
        SWAP PLAYER
            ↓
        VERIFY SWAP
            ↓
        SYNC STATE
            ↓
        FINAL VALIDATION
    """

    name = "orchestrator"

    def __init__(
        self,
        state: AgentState,
        environment: SimulationEnvironment,
    ) -> None:

        self.state = state
        self.environment = environment

        self.monitor_agent = MonitorAgent(
            state,
            environment,
        )

        self.optimizer_agent = OptimizerAgent(
            state,
        )

        self.planner_agent = PlannerAgent(
            state,
        )

        self.validator_agent = ValidatorAgent(
            state,
        )

        self.platform_agent = PlatformAgent(
            state,
        )

    # =========================================================
    # OBSERVE
    # =========================================================

    def observe(self) -> dict[str, Any]:
        return self.monitor_agent.monitor_once()

    # =========================================================
    # PLAN
    # =========================================================

    def plan(self) -> dict[str, Any]:
        return self.planner_agent.plan()

    # =========================================================
    # GENERATE CANDIDATES
    # =========================================================

    def generate_candidates(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:

        return self.optimizer_agent.optimize(
            limit=limit
        )

    # =========================================================
    # VALIDATE + SELECT
    # =========================================================

    def validate_and_select(self) -> dict[str, Any]:

        selected_team = (
            self.validator_agent.select_best_valid_candidate()
        )

        if selected_team is None:

            return {
                "success": False,
                "team": None,
                "error": (
                    "No valid candidate team was selected."
                ),
            }

        return {
            "success": True,
            "team": selected_team.to_dict(),
        }

    # =========================================================
    # CREATE + VERIFY
    # =========================================================

    def create_and_verify(self) -> dict[str, Any]:

        if self.state.current_team is None:

            return {
                "success": False,
                "stage": "create_team",
                "error": "No current team selected.",
            }

        create_result = self.platform_agent.create_team(
            self.state.current_team
        )

        if not create_result.get("success"):

            return {
                "success": False,
                "stage": "create_team",
                "create_result": create_result,
            }

        verify_result = (
            self.platform_agent.verify_created_team()
        )

        return {
            "success": verify_result.get(
                "verified",
                False,
            ),
            "stage": "create_and_verify",
            "create_result": create_result,
            "verify_result": verify_result,
        }

    # =========================================================
    # FIND REPLACEMENT CANDIDATES
    # =========================================================

    def _find_replacement_candidates(
        self,
        player_out_id: str,
    ) -> list[Any]:

        current_team = self.state.current_team

        if current_team is None:
            return []

        outgoing_player = (
            self.state.environment.get_player(
                player_out_id
            )
        )

        if outgoing_player is None:
            return []

        candidates = []

        for player in self.state.environment.players.values():

            if player.id == player_out_id:
                continue

            if current_team.contains_player(player.id):
                continue

            if not player.is_selectable():
                continue

            candidates.append(player)

        candidates.sort(
            key=lambda player: (
                player.fantasy_avg
                + player.fantasy_ceiling
                + player.average_recent_points
                + player.form_rating
                + player.consistency_rating
            ),
            reverse=True,
        )

        return candidates

    # =========================================================
    # BUILD REPLACEMENT TEAM
    # =========================================================

    def _build_replacement_team(
        self,
        player_out_id: str,
        player_in: Any,
    ) -> FantasyTeam | None:

        current_team = self.state.current_team

        if current_team is None:
            return None

        players = [
            player
            for player in current_team.players
            if player.id != player_out_id
        ]

        players.append(player_in)

        return FantasyTeam(
            id=current_team.id,
            players=players,
            captain_id=current_team.captain_id,
            vice_captain_id=current_team.vice_captain_id,
            status=current_team.status,
            projected_points=current_team.projected_points,
        )

    # =========================================================
    # ADAPT TO ENVIRONMENT CHANGES
    # =========================================================

    def adapt_to_changes(self) -> dict[str, Any]:
        """
        Adapt the currently active team to environment changes.

        The adaptation is targeted: replace only an unavailable
        player instead of generating a completely new team.
        """

        current_team = self.state.current_team

        if current_team is None:

            return {
                "success": False,
                "stage": "adaptation",
                "error": "No current team exists.",
            }

        unavailable_players = [
            player
            for player in current_team.players
            if not player.is_selectable()
        ]

        if not unavailable_players:

            self.monitor_agent.update_baseline()

            return {
                "success": True,
                "stage": "adaptation",
                "adapted": False,
                "message": (
                    "Environment changed, but the current "
                    "team remains selectable."
                ),
            }

        player_out = unavailable_players[0]

        replacement_candidates = (
            self._find_replacement_candidates(
                player_out.id
            )
        )

        if not replacement_candidates:

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "replacement_search",
                "error": (
                    "No selectable replacement candidates "
                    "were found."
                ),
                "player_out": player_out.id,
            }

        selected_replacement = None
        replacement_team = None
        validation_result = None

        for player_in in replacement_candidates:

            candidate_team = self._build_replacement_team(
                player_out.id,
                player_in,
            )

            if candidate_team is None:
                continue

            validation_result = (
                self.validator_agent.validator_tool.validate_team(
                    candidate_team
                )
            )

            if validation_result.get("valid", False):

                selected_replacement = player_in
                replacement_team = candidate_team

                break

        if selected_replacement is None:

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "replacement_validation",
                "error": (
                    "No replacement produced a valid "
                    "complete team."
                ),
                "player_out": player_out.id,
                "candidates_checked": len(
                    replacement_candidates
                ),
            }

        self.state.record_action({
            "agent": self.name,
            "action": "select_replacement",
            "player_out": player_out.id,
            "player_in": selected_replacement.id,
            "reason": (
                "Selected highest-ranked replacement "
                "that produces a valid team."
            ),
        })

        self.state.record_tool_result(
            "replacement_validator",
            {
                "player_out": player_out.id,
                "player_in": selected_replacement.id,
                "validation": validation_result,
            },
        )

        self.state.set_status("swapping")

        swap_result = self.platform_agent.swap_player(
            player_out_id=player_out.id,
            player_in_id=selected_replacement.id,
        )

        if not swap_result.get("success", False):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "swap",
                "player_out": player_out.id,
                "player_in": selected_replacement.id,
                "swap_result": swap_result,
            }

        self.state.set_status("verifying_swap")

        verify_result = self.platform_agent.verify_swap(
            player_out_id=player_out.id,
            player_in_id=selected_replacement.id,
        )

        if not verify_result.get("verified", False):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "swap_verification",
                "swap_result": swap_result,
                "verify_result": verify_result,
            }

        self.state.set_status("synchronizing")

        sync_result = (
            self.platform_agent.sync_current_team()
        )

        if not sync_result.get("success", False):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "state_sync",
                "swap_result": swap_result,
                "verify_result": verify_result,
                "sync_result": sync_result,
            }

        final_team = self.state.current_team

        if final_team is None:

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "final_validation",
                "error": (
                    "No team exists after synchronization."
                ),
            }

        final_validation = (
            self.validator_agent.validator_tool.validate_team(
                final_team
            )
        )

        if not final_validation.get("valid", False):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "final_validation",
                "validation": final_validation,
            }

        self.state.increment_revision()

        self.monitor_agent.update_baseline()

        self.state.set_status("adapted")

        return {
            "success": True,
            "stage": "adaptation_complete",
            "adapted": True,
            "player_out": player_out.id,
            "player_in": selected_replacement.id,
            "replacement_team": (
                replacement_team.to_dict()
                if replacement_team is not None
                else None
            ),
            "swap_result": swap_result,
            "verify_result": verify_result,
            "sync_result": sync_result,
            "final_validation": final_validation,
            "revision": self.state.revisions,
            "current_team": final_team.to_dict(),
        }

    # =========================================================
    # INITIAL AUTONOMOUS CYCLE
    # =========================================================

    def run_initial_cycle(
        self,
        candidate_limit: int = 10,
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # IMPORTANT:
        # Start every new team-building request from a clean
        # candidate/team state.
        # -----------------------------------------------------

        self.state.clear_candidate_teams()
        self.state.set_current_team(None)

        self.state.set_status("observing")

        # -----------------------------------------------------
        # OBSERVE
        # -----------------------------------------------------

        observation = self.observe()

        # -----------------------------------------------------
        # PLAN
        # -----------------------------------------------------

        self.state.set_status("planning")

        plan = self.plan()

        action = plan.get("action")

        if action != "GENERATE_CANDIDATES":

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "planning",
                "observation": observation,
                "plan": plan,
                "error": (
                    f"Unexpected planner action: {action}"
                ),
            }

        # -----------------------------------------------------
        # GENERATE CANDIDATES
        # -----------------------------------------------------

        self.state.set_status(
            "generating_candidates"
        )

        optimizer_result = self.generate_candidates(
            limit=candidate_limit
        )

        if not optimizer_result.get("success"):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "candidate_generation",
                "observation": observation,
                "plan": plan,
                "optimizer_result": optimizer_result,
            }

        # -----------------------------------------------------
        # VALIDATE + SELECT
        # -----------------------------------------------------

        self.state.set_status("validating")

        selection_result = self.validate_and_select()

        if not selection_result.get("success"):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "validation",
                "observation": observation,
                "plan": plan,
                "optimizer_result": optimizer_result,
                "selection_result": selection_result,
            }

        # -----------------------------------------------------
        # CREATE + VERIFY
        # -----------------------------------------------------

        self.state.set_status("creating_team")

        platform_result = self.create_and_verify()

        if not platform_result.get("success"):

            self.state.set_status("failed")

            return {
                "success": False,
                "stage": "platform_creation",
                "observation": observation,
                "plan": plan,
                "optimizer_result": optimizer_result,
                "selection_result": selection_result,
                "platform_result": platform_result,
            }

        # -----------------------------------------------------
        # COMPLETE
        # -----------------------------------------------------

        self.state.set_status("team_created")

        return {
            "success": True,
            "stage": "initial_cycle_complete",
            "observation": observation,
            "plan": plan,
            "optimizer_result": optimizer_result,
            "selection_result": selection_result,
            "platform_result": platform_result,
            "current_team": (
                self.state.current_team.to_dict()
                if self.state.current_team is not None
                else None
            ),
        }

    # =========================================================
    # ADAPTATION CYCLE
    # =========================================================

    def run_adaptation_cycle(self) -> dict[str, Any]:
        """
        Run one autonomous adaptation cycle after an
        environment change.
        """

        self.state.set_status("observing")

        observation = self.observe()

        self.state.set_status("planning")

        plan = self.plan()

        if plan.get("action") != "REPLAN":

            self.state.set_status("stable")

            adaptation_result = {
                "success": True,
                "stage": "no_adaptation_required",
                "adapted": False,
                "message": (
                    "No environment change requires "
                    "team adaptation."
                ),
            }

            return {
                "success": True,
                "stage": "no_adaptation_required",
                "observation": observation,
                "plan": plan,
                "adaptation": adaptation_result,
            }

        self.state.set_status("adapting")

        adaptation_result = self.adapt_to_changes()

        return {
            "success": adaptation_result.get(
                "success",
                False,
            ),
            "stage": "adaptation_cycle_complete",
            "observation": observation,
            "plan": plan,
            "adaptation": adaptation_result,
        }