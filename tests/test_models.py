from backend.data.seed_data import create_match, create_players
from backend.models.constraints import TeamConstraints, UserPreferences
from backend.models.player import Player
from backend.models.state import AgentState, EnvironmentState
from backend.models.team import FantasyTeam


def test_player_model():
    player = Player(
        id="PTEST",
        name="Test Player",
        real_team="IND",
        role="batter",
        credits=9.0,
        fantasy_avg=70.0,
        fantasy_ceiling=100.0,
        recent_points=[60.0, 70.0, 80.0],
        batting_rating=85.0,
        bowling_rating=20.0,
        form_rating=80.0,
        consistency_rating=75.0,
        upside_rating=85.0,
        powerplay_rating=80.0,
        death_overs_rating=20.0,
        pace_rating=30.0,
        spin_rating=20.0,
        venue_rating=75.0,
    )

    assert player.id == "PTEST"
    assert player.name == "Test Player"
    assert player.real_team == "IND"
    assert player.role == "batter"
    assert player.is_selectable() is True
    assert player.average_recent_points == 70.0


def test_fantasy_team_model():
    players = create_players()

    team = FantasyTeam(
        id="TEAM_TEST",
        players=players[:2],
    )

    assert team.size == 2
    assert team.contains_player(players[0].id)
    assert team.contains_player(players[1].id)
    assert team.calculate_cost() == 18.0
    assert team.total_cost == 18.0

    team.set_captain(players[0].id)
    team.set_vice_captain(players[1].id)

    assert team.captain_id == players[0].id
    assert team.vice_captain_id == players[1].id


def test_team_constraints():
    constraints = TeamConstraints()

    assert constraints.budget == 100.0
    assert constraints.squad_size == 11
    assert constraints.max_players_per_real_team == 7
    assert constraints.minimum_required_players() == 8
    assert constraints.is_role_configuration_possible() is True


def test_user_preferences():
    preferences = UserPreferences()

    assert preferences.risk_profile.value == "balanced"
    assert preferences.prioritize_form is True
    assert preferences.prioritize_consistency is True


def test_match_model():
    match = create_match()

    assert match.id == "MATCH001"
    assert match.team_a == "IND"
    assert match.team_b == "AUS"
    assert match.venue == "Mumbai"

    original_rain = match.weather.rain_probability

    match.weather.update_rain_probability(75.0)

    assert match.weather.rain_probability == 75.0
    assert match.weather.rain_probability != original_rain


def test_agent_state():
    players = create_players()

    environment = EnvironmentState(
        version=1,
        players={player.id: player for player in players},
        match=create_match(),
    )

    state = AgentState(
        goal="Build the best fantasy cricket team.",
        environment=environment,
    )

    assert state.status == "idle"
    assert len(state.environment.players) == 42

    state.set_status("planning")
    state.record_observation({"type": "test_observation"})
    state.record_action({"type": "test_action"})
    state.record_tool_result("test_tool", {"success": True})
    state.increment_revision()

    assert state.status == "planning"
    assert len(state.observations) == 1
    assert len(state.actions) == 1
    assert len(state.tool_results) == 1
    assert state.revisions == 1