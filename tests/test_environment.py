import json

import pytest

from backend.main import create_initial_state
from backend.simulation.environment import SimulationEnvironment


EVENTS = [
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


@pytest.fixture
def environment(tmp_path):
    """
    Create a fresh simulation environment with its own temporary
    events.json file.

    This prevents one test from modifying the real backend/data/events.json
    file and affecting another test.
    """

    events_path = tmp_path / "events.json"

    events_path.write_text(
        json.dumps(EVENTS, indent=2),
        encoding="utf-8",
    )

    state = create_initial_state()

    simulation_environment = SimulationEnvironment(
        state,
        events_path=events_path,
    )

    return state, simulation_environment


def test_environment_initial_state(environment):
    state, simulation_environment = environment

    observation = simulation_environment.observe()

    assert observation["environment_version"] == 1
    assert len(observation["players"]) == 42
    assert observation["match"] is not None

    player = state.environment.get_player("P001")

    assert player is not None
    assert player.is_selectable() is True

    assert (
        state.environment.match.weather.rain_probability
        == 20.0
    )


def test_environment_loads_events(environment):
    state, simulation_environment = environment

    events = simulation_environment.load_events()

    assert len(events) == 2

    event_types = {
        event["type"]
        for event in events
    }

    assert "player_unavailable" in event_types
    assert "weather_update" in event_types


def test_environment_processes_events(environment):
    state, simulation_environment = environment

    assert state.environment.version == 1

    processed_events = (
        simulation_environment.process_pending_events()
    )

    assert len(processed_events) == 2
    assert state.environment.version == 3

    player = state.environment.get_player("P001")

    assert player is not None
    assert player.is_selectable() is False
    assert (
        player.availability_reason
        == "Late injury reported before match"
    )

    weather = state.environment.match.weather

    assert weather.rain_probability == 75.0
    assert weather.condition == "Cloudy"
    assert weather.humidity == 78.0
    assert weather.wind_speed == 18.0


def test_environment_detects_change(environment):
    state, simulation_environment = environment

    initial_version = (
        simulation_environment.get_version()
    )

    assert initial_version == 1

    assert (
        simulation_environment.has_environment_changed(
            initial_version
        )
        is False
    )

    simulation_environment.process_pending_events()

    assert simulation_environment.get_version() == 3

    assert (
        simulation_environment.has_environment_changed(
            initial_version
        )
        is True
    )


def test_environment_events_are_processed_only_once(environment):
    state, simulation_environment = environment

    simulation_environment.process_pending_events()

    first_version = (
        simulation_environment.get_version()
    )

    assert first_version == 3

    second_processed_events = (
        simulation_environment.process_pending_events()
    )

    assert second_processed_events == []
    assert simulation_environment.get_version() == first_version
