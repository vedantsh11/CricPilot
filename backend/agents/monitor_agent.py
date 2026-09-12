from __future__ import annotations

from typing import Any

from backend.models.state import AgentState
from backend.simulation.environment import SimulationEnvironment
from backend.tools.availability import AvailabilityTool
from backend.tools.news import NewsTool
from backend.tools.weather import WeatherTool


class MonitorAgent:
    """
    Monitors the simulated fantasy environment for changes.

    The monitor detects:
    - player availability changes
    - weather changes
    - news changes
    - environment version changes

    It does not decide how the team should be changed.
    """

    name = "monitor_agent"

    def __init__(
        self,
        state: AgentState,
        environment: SimulationEnvironment,
    ) -> None:
        self.state = state
        self.environment = environment

        self.availability_tool = AvailabilityTool(state)
        self.weather_tool = WeatherTool(state)
        self.news_tool = NewsTool(state)

        self.last_environment_version = state.environment.version
        self.last_availability_snapshot = (
            self.availability_tool.get_availability_snapshot()
        )
        self.last_weather_snapshot = (
            self.weather_tool.get_weather_snapshot()
        )
        self.last_news_count = self.news_tool.get_news_count()

    def observe(self) -> dict[str, Any]:
        """
        Observe the current environment without modifying it.
        """

        return {
            "environment_version": self.state.environment.version,
            "availability": (
                self.availability_tool.get_availability_snapshot()
            ),
            "weather": self.weather_tool.get_weather_snapshot(),
            "news": self.news_tool.get_news_snapshot(),
        }

    def detect_changes(self) -> dict[str, Any]:
        """
        Compare the current environment with the previous observation.
        """

        current_version = self.state.environment.version

        availability_changed = (
            self.availability_tool.has_availability_changed(
                self.last_availability_snapshot
            )
        )

        weather_changed = (
            self.weather_tool.is_weather_changed(
                self.last_weather_snapshot
            )
        )

        news_changed = self.news_tool.has_news_changed(
            self.last_news_count
        )

        version_changed = (
            current_version != self.last_environment_version
        )

        changes = {
            "environment_version_changed": version_changed,
            "availability_changed": availability_changed,
            "weather_changed": weather_changed,
            "news_changed": news_changed,
            "environment_version": current_version,
        }

        changes["environment_changed"] = any(
            [
                version_changed,
                availability_changed,
                weather_changed,
                news_changed,
            ]
        )

        return changes

    def update_baseline(self) -> None:
        """
        Store the current environment as the new monitoring baseline.
        """

        self.last_environment_version = (
            self.state.environment.version
        )

        self.last_availability_snapshot = (
            self.availability_tool.get_availability_snapshot()
        )

        self.last_weather_snapshot = (
            self.weather_tool.get_weather_snapshot()
        )

        self.last_news_count = (
            self.news_tool.get_news_count()
        )

    def monitor_once(self) -> dict[str, Any]:
        """
        Perform one monitoring cycle.

        Returns the observation and detected changes.
        """

        observation = self.observe()
        changes = self.detect_changes()

        self.state.record_observation(
            {
                "source": self.name,
                "observation": observation,
                "changes": changes,
            }
        )

        return {
            "observation": observation,
            "changes": changes,
        }


def create_monitor_agent(
    state: AgentState,
    environment: SimulationEnvironment,
) -> MonitorAgent:
    return MonitorAgent(state, environment)