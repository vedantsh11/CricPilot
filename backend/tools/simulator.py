from __future__ import annotations

from typing import Any

from backend.models.player import Player
from backend.models.team import FantasyTeam
from backend.models.state import AgentState


class FantasySimulatorTool:
    """
    Deterministic fantasy-cricket scoring simulator.

    The simulator estimates fantasy performance for a team using the
    current player statistics and match environment.

    It does not:
    - modify players,
    - modify the environment,
    - create or submit teams,
    - make autonomous decisions.

    It only evaluates a supplied team.
    """

    name = "fantasy_simulator"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def simulate_team(
        self,
        team: FantasyTeam,
    ) -> dict[str, Any]:
        """
        Simulate fantasy performance for one team.
        """
        player_results = []

        for player in team.players:
            base_points = self._calculate_base_points(player)
            weather_adjustment = self._calculate_weather_adjustment(
                player
            )

            simulated_points = max(
                0.0,
                base_points + weather_adjustment,
            )

            multiplier = self._get_multiplier(
                team,
                player,
            )

            final_points = simulated_points * multiplier

            player_results.append(
                {
                    "player_id": player.id,
                    "player_name": player.name,
                    "role": player.role.value,
                    "base_points": round(base_points, 2),
                    "weather_adjustment": round(
                        weather_adjustment,
                        2,
                    ),
                    "multiplier": multiplier,
                    "simulated_points": round(
                        final_points,
                        2,
                    ),
                }
            )

        total_points = sum(
            result["simulated_points"]
            for result in player_results
        )

        return {
            "team_id": team.id,
            "environment_version": self.state.environment.version,
            "total_simulated_points": round(
                total_points,
                2,
            ),
            "players": player_results,
            "weather": self._get_weather_context(),
        }

    def simulate_candidates(
        self,
        teams: list[FantasyTeam],
    ) -> list[dict[str, Any]]:
        """
        Simulate multiple candidate teams and rank them by score.
        """
        results = [
            self.simulate_team(team)
            for team in teams
        ]

        results.sort(
            key=lambda result: result["total_simulated_points"],
            reverse=True,
        )

        return results

    def simulate_candidate_dicts(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Compatibility helper for optimizer output.

        Converts serialized candidate dictionaries back into teams
        using the current environment players.
        """
        teams = []

        for candidate in candidates:
            player_ids = candidate.get(
                "player_ids",
                [],
            )

            players = []

            for player_id in player_ids:
                player = self.state.environment.get_player(
                    player_id
                )

                if player is not None:
                    players.append(player)

            if len(players) != len(player_ids):
                continue

            team = FantasyTeam(
                id=candidate.get(
                    "team_id",
                    "SIMULATED_TEAM",
                ),
                players=players,
                captain_id=candidate.get(
                    "captain_id"
                ),
                vice_captain_id=candidate.get(
                    "vice_captain_id"
                ),
            )

            team.calculate_cost()
            teams.append(team)

        return self.simulate_candidates(teams)

    def estimate_player_points(
        self,
        player: Player,
    ) -> float:
        """
        Estimate fantasy points for one player under current conditions.
        """
        base_points = self._calculate_base_points(player)
        weather_adjustment = self._calculate_weather_adjustment(
            player
        )

        return round(
            max(
                0.0,
                base_points + weather_adjustment,
            ),
            2,
        )

    def _calculate_base_points(
        self,
        player: Player,
    ) -> float:
        """
        Calculate deterministic baseline fantasy points.

        Recent form and fantasy average carry the greatest weight.
        Ceiling and role-specific ratings add upside.
        """
        return (
            player.fantasy_avg * 0.45
            + player.recent_form * 0.25
            + player.fantasy_ceiling * 0.15
            + player.form_rating * 0.05
            + player.consistency_rating * 0.05
            + player.venue_rating * 0.05
        )

    def _calculate_weather_adjustment(
        self,
        player: Player,
    ) -> float:
        """
        Apply a deterministic weather adjustment.

        This is deliberately modest. Weather should influence the
        simulation without completely overriding player quality.

        Rain itself creates uncertainty and possible lost playing time.
        Bowling-related ratings receive a small benefit in more
        difficult/cloudy conditions, while batting-heavy players can
        receive a small negative adjustment.
        """
        match = self.state.environment.match

        if match is None:
            return 0.0

        weather = match.weather

        rain = weather.rain_probability
        condition = weather.condition.lower()

        adjustment = 0.0

        if rain >= 75:
            if player.bowling_rating > player.batting_rating:
                adjustment += 2.5
            else:
                adjustment -= 3.0

        elif rain >= 50:
            if player.bowling_rating > player.batting_rating:
                adjustment += 1.5
            else:
                adjustment -= 1.5

        elif rain >= 30:
            adjustment -= 0.5

        if "cloud" in condition:
            if player.bowling_rating > player.batting_rating:
                adjustment += 1.0

        return adjustment

    def _get_multiplier(
        self,
        team: FantasyTeam,
        player: Player,
    ) -> float:
        """
        Return captain/vice-captain fantasy multipliers.
        """
        if team.captain_id == player.id:
            return 2.0

        if team.vice_captain_id == player.id:
            return 1.5

        return 1.0

    def _get_weather_context(self) -> dict[str, Any] | None:
        """Return current weather information used by the simulation."""
        match = self.state.environment.match

        if match is None:
            return None

        weather = match.weather

        return {
            "rain_probability": weather.rain_probability,
            "condition": weather.condition,
            "humidity": weather.humidity,
            "wind_speed": weather.wind_speed,
        }


def create_simulator_tool(
    state: AgentState,
) -> FantasySimulatorTool:
    """Create a fantasy simulator for the current agent state."""
    return FantasySimulatorTool(state)