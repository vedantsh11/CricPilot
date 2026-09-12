from __future__ import annotations

from typing import Any

from backend.models.state import AgentState


class WeatherTool:
    """
    Deterministic tool for retrieving and comparing match weather.

    The tool reads the current weather from the simulated environment.
    It does not decide whether a player should be selected.
    """

    name = "weather"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def get_current_weather(self) -> dict[str, Any] | None:
        """
        Return the current weather conditions for the match.

        Returns None when no match is loaded.
        """
        match = self.state.environment.match

        if match is None:
            return None

        weather = match.weather

        return {
            "environment_version": self.state.environment.version,
            "temperature": weather.temperature,
            "humidity": weather.humidity,
            "rain_probability": weather.rain_probability,
            "wind_speed": weather.wind_speed,
            "condition": weather.condition,
        }

    def get_rain_probability(self) -> float | None:
        """Return the current rain probability."""
        weather = self.get_current_weather()

        if weather is None:
            return None

        return weather["rain_probability"]

    def is_rain_risk_high(
        self,
        threshold: float = 60.0,
    ) -> bool:
        """
        Return True when rain probability reaches the given threshold.
        """
        rain_probability = self.get_rain_probability()

        if rain_probability is None:
            return False

        return rain_probability >= threshold

    def is_weather_changed(
        self,
        previous_weather: dict[str, Any] | None,
    ) -> bool:
        """
        Compare the current weather with a previous weather snapshot.

        Environment version alone is not used because other environment
        events can also change the version.
        """
        current_weather = self.get_current_weather()

        if current_weather is None or previous_weather is None:
            return current_weather != previous_weather

        weather_fields = (
            "temperature",
            "humidity",
            "rain_probability",
            "wind_speed",
            "condition",
        )

        return any(
            current_weather[field] != previous_weather.get(field)
            for field in weather_fields
        )

    def get_weather_impact(
        self,
        previous_weather: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Return a deterministic summary of the current weather risk.

        This does not select players. It provides context that the
        decision-making layer can use.
        """
        current_weather = self.get_current_weather()

        if current_weather is None:
            return {
                "available": False,
                "changed": previous_weather is not None,
                "rain_risk": "unknown",
                "impact": "No match weather available.",
            }

        rain_probability = current_weather["rain_probability"]

        if rain_probability >= 75:
            rain_risk = "very_high"
            impact = (
                "High rain probability may reduce playing time "
                "and increase match uncertainty."
            )
        elif rain_probability >= 50:
            rain_risk = "high"
            impact = (
                "Rain is a significant match-risk factor."
            )
        elif rain_probability >= 30:
            rain_risk = "moderate"
            impact = (
                "Some rain risk exists, but conditions may remain playable."
            )
        else:
            rain_risk = "low"
            impact = (
                "Rain is currently a relatively low-risk factor."
            )

        return {
            "available": True,
            "changed": self.is_weather_changed(previous_weather),
            "rain_risk": rain_risk,
            "impact": impact,
            "weather": current_weather,
        }

    def get_weather_snapshot(self) -> dict[str, Any] | None:
        """
        Return a snapshot suitable for storing before an agent action.
        """
        weather = self.get_current_weather()

        if weather is None:
            return None

        return dict(weather)


def create_weather_tool(
    state: AgentState,
) -> WeatherTool:
    """Create a weather tool for the current agent state."""
    return WeatherTool(state)