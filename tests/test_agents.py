import pytest

from backend.main import create_initial_state
from backend.models.team import FantasyTeam
from backend.simulation.environment import SimulationEnvironment
from backend.agents.monitor_agent import MonitorAgent
from backend.agents.optimizer_agent import OptimizerAgent
from backend.agents.planner import PlannerAgent
from backend.agents.validator_agent import ValidatorAgent
from backend.agents.platform_agent import PlatformAgent


@pytest.fixture
def state():
    return create_initial_state()


@pytest.fixture
def environment(state):
    return SimulationEnvironment(state)


def test_monitor_agent_initial_observation(state, environment):
    monitor = MonitorAgent(state, environment)
    result = monitor.monitor_once()
    assert result["observation"]["environment_version"] == 1
    assert result["changes"]["environment_changed"] is False


def test_monitor_agent_detects_availability_change(state, environment):
    monitor = MonitorAgent(state, environment)
    player = state.environment.get_player("P001")
    assert player is not None
    player.mark_unavailable("Late injury")
    result = monitor.monitor_once()
    assert result["changes"]["availability_changed"] is True
    assert result["changes"]["environment_changed"] is True


def test_monitor_agent_updates_baseline(state, environment):
    monitor = MonitorAgent(state, environment)
    player = state.environment.get_player("P001")
    assert player is not None
    player.mark_unavailable("Late injury")
    assert monitor.monitor_once()["changes"]["environment_changed"] is True
    monitor.update_baseline()
    assert monitor.monitor_once()["changes"]["environment_changed"] is False


def test_optimizer_agent_generates_candidates(state):
    optimizer_agent = OptimizerAgent(state)
    candidates = optimizer_agent.generate_candidates(limit=3)
    assert len(candidates) == 3
    for candidate in candidates:
        assert len(candidate["player_ids"]) == 11
        assert candidate["size"] == 11
    assert len(state.candidate_teams) == 3


def test_optimizer_agent_optimize(state):
    optimizer_agent = OptimizerAgent(state)
    result = optimizer_agent.optimize(limit=3)
    assert result["success"] is True
    assert result["candidate_count"] == 3
    assert len(result["candidates"]) == 3
    assert any(item["tool"] == "optimizer" for item in state.tool_results)


def test_planner_generates_candidates_when_none_exist(state):
    planner = PlannerAgent(state)
    plan = planner.plan()
    assert plan["action"] == "GENERATE_CANDIDATES"


def test_planner_validates_candidates(state):
    OptimizerAgent(state).generate_candidates(limit=3)
    plan = PlannerAgent(state).plan()
    assert plan["action"] == "VALIDATE_CANDIDATE"


def test_planner_verifies_existing_team(state):
    OptimizerAgent(state).generate_candidates(limit=1)
    ValidatorAgent(state).select_best_valid_candidate(state.candidate_teams)
    plan = PlannerAgent(state).plan()
    assert plan["action"] == "VERIFY_TEAM"


def test_planner_replans_after_environment_change(state):
    OptimizerAgent(state).generate_candidates(limit=1)
    ValidatorAgent(state).select_best_valid_candidate(state.candidate_teams)
    planner = PlannerAgent(state)
    state.record_observation({
        "source": "monitor_agent",
        "observation": {},
        "changes": {
            "environment_changed": True,
            "environment_version": 2,
        },
    })
    plan = planner.plan()
    assert plan["action"] == "REPLAN"


def test_validator_agent_validates_candidates(state):
    candidates = OptimizerAgent(state).generate_candidates(limit=3)
    results = ValidatorAgent(state).validate_candidates(candidates)
    assert len(results) == 3
    for result in results:
        assert "valid" in result
        assert "checks" in result


def test_validator_agent_selects_best_valid_candidate(state):
    OptimizerAgent(state).generate_candidates(limit=3)
    selected = ValidatorAgent(state).select_best_valid_candidate(
        state.candidate_teams
    )
    assert selected is not None
    assert isinstance(selected, FantasyTeam)
    assert selected.size == 11
    assert state.current_team is selected


def test_platform_agent_create_and_verify_team(state):
    OptimizerAgent(state).generate_candidates(limit=3)
    selected = ValidatorAgent(state).select_best_valid_candidate(
        state.candidate_teams
    )
    assert selected is not None
    platform_agent = PlatformAgent(state)
    create_result = platform_agent.create_team()
    assert create_result["success"] is True
    verify_result = platform_agent.verify_created_team()
    assert verify_result["verified"] is True


def test_platform_agent_sync_current_team(state):
    OptimizerAgent(state).generate_candidates(limit=1)
    selected = ValidatorAgent(state).select_best_valid_candidate(
        state.candidate_teams
    )
    assert selected is not None
    platform_agent = PlatformAgent(state)
    assert platform_agent.create_team()["success"] is True
    state.set_current_team(None)
    sync_result = platform_agent.sync_current_team()
    assert sync_result["success"] is True
    assert state.current_team is not None
    assert state.current_team.id == selected.id


def test_platform_agent_swap_and_verify(state):
    OptimizerAgent(state).generate_candidates(limit=3)
    selected = ValidatorAgent(state).select_best_valid_candidate(
        state.candidate_teams
    )
    assert selected is not None
    platform_agent = PlatformAgent(state)
    assert platform_agent.create_team()["success"] is True

    original_player_ids = set(selected.player_ids)
    player_out_id = selected.player_ids[0]

    available_players = [
        player
        for player in state.environment.players.values()
        if player.is_selectable() and player.id not in original_player_ids
    ]
    assert available_players

    player_in_id = available_players[0].id
    swap_result = platform_agent.swap_player(
        player_out_id=player_out_id,
        player_in_id=player_in_id,
    )
    assert swap_result["success"] is True

    verification = platform_agent.verify_swap(
        player_out_id=player_out_id,
        player_in_id=player_in_id,
    )
    assert verification["verified"] is True
    assert verification["out_removed"] is True
    assert verification["in_added"] is True


def test_agent_flow_optimizer_validator_platform(state):
    environment = SimulationEnvironment(state)
    monitor = MonitorAgent(state, environment)
    optimizer = OptimizerAgent(state)
    validator = ValidatorAgent(state)
    platform = PlatformAgent(state)

    observation = monitor.monitor_once()
    assert observation["changes"]["environment_changed"] is False

    candidates = optimizer.generate_candidates(limit=3)
    assert len(candidates) == 3

    selected = validator.select_best_valid_candidate(candidates)
    assert selected is not None
    assert selected.size == 11

    assert platform.create_team()["success"] is True
    assert platform.verify_created_team()["verified"] is True
