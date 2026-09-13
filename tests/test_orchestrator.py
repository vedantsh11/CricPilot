import json

from backend.main import create_initial_state
from backend.simulation.environment import SimulationEnvironment
from backend.agents.orchestrator import Orchestrator


def create_test_environment(state, tmp_path):
    events = [
        {
            "id": "EVENT001",
            "type": "player_unavailable",
            "timestamp": "2026-09-20T18:15:00",
            "player_id": "P001",
            "payload": {
                "status": "unavailable",
                "reason": "Late injury reported before match",
            },
            "processed": False,
        },
        {
            "id": "EVENT002",
            "type": "weather_update",
            "timestamp": "2026-09-20T18:20:00",
            "payload": {
                "rain_probability": 75.0,
                "condition": "Cloudy",
                "humidity": 78.0,
                "wind_speed": 18.0,
            },
            "processed": False,
        },
    ]

    events_path = tmp_path / "events.json"

    with events_path.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)

    return SimulationEnvironment(
        state,
        events_path=events_path,
    )


def test_initial_cycle(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    result = orchestrator.run_initial_cycle(candidate_limit=5)

    assert result["success"] is True
    assert result["stage"] == "initial_cycle_complete"

    assert state.current_team is not None
    assert state.current_team.size == 11
    assert state.status == "team_created"


def test_observe(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    result = orchestrator.observe()

    assert "observation" in result
    assert "changes" in result

    assert (
        result["observation"]["environment_version"]
        == state.environment.version
    )


def test_plan(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    plan = orchestrator.plan()

    assert plan["action"] == "GENERATE_CANDIDATES"


def test_generate_candidates(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    result = orchestrator.generate_candidates(limit=5)

    assert result["success"] is True
    assert result["candidate_count"] > 0
    assert len(state.candidate_teams) > 0


def test_validate_and_select(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    orchestrator.generate_candidates(limit=5)

    result = orchestrator.validate_and_select()

    assert result["success"] is True
    assert state.current_team is not None
    assert state.current_team.size == 11


def test_create_and_verify(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    orchestrator.generate_candidates(limit=5)
    orchestrator.validate_and_select()

    result = orchestrator.create_and_verify()

    assert result["success"] is True
    assert result["verify_result"]["verified"] is True


def test_adaptation_without_change(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    orchestrator.run_initial_cycle(candidate_limit=5)

    result = orchestrator.run_adaptation_cycle()

    assert result["success"] is True
    assert result["adaptation"]["adapted"] is False


def test_adaptation_after_environment_change(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    orchestrator.run_initial_cycle(candidate_limit=5)

    environment.process_pending_events()

    result = orchestrator.run_adaptation_cycle()

    assert result["success"] is True
    assert result["adaptation"]["adapted"] is True

    assert state.current_team is not None
    assert state.revisions == 1


def test_full_workflow(tmp_path):
    state = create_initial_state()
    environment = create_test_environment(state, tmp_path)
    orchestrator = Orchestrator(state, environment)

    initial = orchestrator.run_initial_cycle(candidate_limit=5)

    assert initial["success"] is True

    environment.process_pending_events()

    adaptation = orchestrator.run_adaptation_cycle()

    assert adaptation["success"] is True
    assert state.current_team is not None
    assert state.status == "adapted"