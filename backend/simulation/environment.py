from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.models.state import AgentState


class SimulationEnvironment:
    """
    Simulated fantasy-cricket environment used by CricPilot.

    The environment represents the external world in which the agent
    operates. It can expose observations and apply deterministic events
    such as player injuries and weather changes.

    The environment does NOT decide which team should be selected.
    That responsibility belongs to the agent and optimization layers.
    """

    def __init__(
        self,
        state: AgentState,
        events_path: str | Path | None = None,
    ) -> None:
        self.state = state

        if events_path is None:
            events_path = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "events.json"
            )

        self.events_path = Path(events_path)

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def observe(self) -> dict[str, Any]:
        """
        Return the current observable environment state.

        This is what the agent can use as its current view of the world.
        """

        environment = self.state.environment

        observation = {
            "environment_version": environment.version,
            "players": {
                player_id: player.to_dict()
                for player_id, player in environment.players.items()
            },
            "match": (
                environment.match.to_dict()
                if environment.match is not None
                else None
            ),
            "latest_news": environment.latest_news,
            "events": environment.events,
        }

        self.state.record_observation(
            {
                "type": "environment_observation",
                "environment_version": environment.version,
            }
        )

        return observation

    # ------------------------------------------------------------------
    # Event loading
    # ------------------------------------------------------------------

    def load_events(self) -> list[dict[str, Any]]:
        """
        Load deterministic simulation events from events.json.

        The file is intentionally used as the source of truth for the
        hackathon demo so that the autonomous adaptation scenario is
        reproducible.
        """

        if not self.events_path.exists():
            return []

        with self.events_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("events.json must contain a JSON list.")

        return data

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_pending_events(self) -> list[dict[str, Any]]:
        """
        Apply all unprocessed simulation events.

        Returns the events that were actually processed.
        """

        events = self.load_events()
        processed_events: list[dict[str, Any]] = []

        for event in events:
            if event.get("processed", False):
                continue

            self.apply_event(event)

            event["processed"] = True
            processed_events.append(event)

        if processed_events:
            self._save_events(events)

        return processed_events

    def apply_event(self, event: dict[str, Any]) -> None:
        """
        Apply one event to the simulated environment.
        """

        event_type = event.get("type")

        if event_type == "player_unavailable":
            self._handle_player_unavailable(event)

        elif event_type == "weather_update":
            self._handle_weather_update(event)

        elif event_type == "news_update":
            self._handle_news_update(event)

        else:
            raise ValueError(
                f"Unsupported simulation event type: {event_type}"
            )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_player_unavailable(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Mark a player as unavailable because of a simulated event.
        """

        player_id = event.get("player_id")
        payload = event.get("payload", {})

        if not player_id:
            raise ValueError(
                "player_unavailable event requires player_id."
            )

        player = self.state.environment.get_player(player_id)

        if player is None:
            raise ValueError(
                f"Player '{player_id}' does not exist."
            )

        reason = payload.get(
            "reason",
            "Player became unavailable.",
        )

        player.mark_unavailable(reason)

        self.state.environment.add_event(
            {
                "id": event.get("id"),
                "type": event.get("type"),
                "player_id": player_id,
                "reason": reason,
            }
        )

        self.state.environment.increment_version()

    def _handle_weather_update(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Update the simulated match weather.
        """

        match = self.state.environment.match

        if match is None:
            raise ValueError(
                "Cannot update weather without a match."
            )

        payload = event.get("payload", {})

        if "rain_probability" in payload:
            match.weather.update_rain_probability(
                payload["rain_probability"]
            )

        if "condition" in payload:
            match.weather.condition = payload["condition"]

        if "humidity" in payload:
            match.weather.humidity = payload["humidity"]

        if "wind_speed" in payload:
            match.weather.wind_speed = payload["wind_speed"]

        if "temperature" in payload:
            match.weather.temperature = payload["temperature"]

        self.state.environment.add_event(
            {
                "id": event.get("id"),
                "type": event.get("type"),
                "payload": payload,
            }
        )

        self.state.environment.increment_version()

    def _handle_news_update(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Add a simulated news update to the environment.
        """

        payload = event.get("payload", {})

        news_item = {
            "id": event.get("id"),
            "type": event.get("type"),
            **payload,
        }

        self.state.environment.add_news(news_item)
        self.state.environment.add_event(news_item)

        self.state.environment.increment_version()

    # ------------------------------------------------------------------
    # Event persistence
    # ------------------------------------------------------------------

    def _save_events(
        self,
        events: list[dict[str, Any]],
    ) -> None:
        """
        Persist processed-event status back to events.json.
        """

        self.events_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.events_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                events,
                file,
                indent=2,
            )

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def has_environment_changed(
        self,
        previous_version: int,
    ) -> bool:
        """
        Check whether the environment changed since a previous version.
        """

        return self.state.environment.version != previous_version

    def get_version(self) -> int:
        """
        Return the current environment version.
        """

        return self.state.environment.version