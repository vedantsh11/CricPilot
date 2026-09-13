from backend.main import create_initial_state

from backend.tools.player_stats import PlayerStatsTool
from backend.tools.availability import AvailabilityTool
from backend.tools.weather import WeatherTool
from backend.tools.optimizer import OptimizerTool
from backend.tools.validator import ValidatorTool
from backend.tools.simulator import FantasySimulatorTool
from backend.tools.fantasy_platform import FantasyPlatformTool


def test_player_stats_tool():
    state = create_initial_state()
    tool = PlayerStatsTool(state)

    players = tool.get_all_players()

    assert len(players) == 42

    player = tool.get_player("P001")

    assert player is not None
    assert player["id"] == "P001"

    available_players = tool.get_available_players()

    assert len(available_players) == 42


def test_availability_tool():
    state = create_initial_state()
    tool = AvailabilityTool(state)

    status = tool.get_player_status("P001")

    assert status is not None
    assert status["player_id"] == "P001"
    assert status["status"] == "available"
    assert status["selectable"] is True

    assert tool.is_available("P001") is True

    unavailable = tool.get_unavailable_players()

    assert len(unavailable) == 0

    doubtful = tool.get_doubtful_players()

    assert len(doubtful) == 0

    snapshot = tool.get_availability_snapshot()

    assert snapshot["total_players"] == 42
    assert snapshot["available"] == 42
    assert snapshot["doubtful"] == 0
    assert snapshot["unavailable"] == 0


def test_weather_tool():
    state = create_initial_state()
    tool = WeatherTool(state)

    weather = tool.get_current_weather()

    assert weather is not None
    assert weather["rain_probability"] == 20.0
    assert weather["condition"] == "Clear"

    assert tool.get_rain_probability() == 20.0

    assert tool.is_rain_risk_high() is False

    impact = tool.get_weather_impact()

    assert impact["available"] is True
    assert impact["rain_risk"] == "low"


def test_optimizer_tool():
    state = create_initial_state()
    tool = OptimizerTool(state)

    candidates = tool.generate_candidate_dicts(limit=5)

    assert len(candidates) > 0
    assert len(candidates) <= 5

    for candidate in candidates:
        assert candidate["size"] == 11
        assert candidate["total_cost"] <= state.constraints.budget
        assert candidate["score"] > 0


def test_validator_tool():
    state = create_initial_state()

    optimizer = OptimizerTool(state)
    validator = ValidatorTool(state)

    candidates = optimizer.generate_candidates(limit=5)

    assert len(candidates) > 0

    for candidate in candidates:
        result = validator.validate_team(candidate)

        assert result["valid"] is True
        assert result["squad_size"] == 11
        assert result["total_cost"] <= state.constraints.budget


def test_simulator_tool():
    state = create_initial_state()

    optimizer = OptimizerTool(state)
    simulator = FantasySimulatorTool(state)

    candidates = optimizer.generate_candidate_dicts(limit=3)

    assert len(candidates) > 0

    results = simulator.simulate_candidate_dicts(candidates)

    assert len(results) == len(candidates)

    for result in results:
        assert "total_simulated_points" in result
        assert result["total_simulated_points"] > 0


def test_fantasy_platform_tool():
    state = create_initial_state()

    optimizer = OptimizerTool(state)
    platform = FantasyPlatformTool(state)

    candidates = optimizer.generate_candidates(limit=1)

    assert len(candidates) == 1

    team = candidates[0]

    created = platform.create_team(team)

    assert created["success"] is True

    active_team = platform.get_active_team()

    assert active_team is not None
    assert active_team.size == 11

    platform_state = platform.get_platform_state()

    print("\nPLATFORM STATE:", platform_state)

    assert platform_state is not None