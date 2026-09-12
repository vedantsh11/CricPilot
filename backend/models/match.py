from dataclasses import dataclass, field
from typing import Dict


@dataclass
class WeatherState:
    """Current weather conditions for a match."""

    temperature: float
    humidity: float
    rain_probability: float
    wind_speed: float
    condition: str

    def to_dict(self) -> dict:
        """Return weather state as a serializable dictionary."""

        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "rain_probability": self.rain_probability,
            "wind_speed": self.wind_speed,
            "condition": self.condition,
        }

    def update_rain_probability(self, probability: float) -> None:
        """Update rain probability while keeping it within 0-100."""

        self.rain_probability = max(0.0, min(100.0, probability))


@dataclass
class MatchContext:
    """Match-specific conditions that can influence player selection."""

    pitch_type: str
    batting_friendly: float
    bowling_friendly: float

    toss_winner: str | None = None
    decision_after_toss: str | None = None

    def to_dict(self) -> dict:
        """Return match context as a serializable dictionary."""

        return {
            "pitch_type": self.pitch_type,
            "batting_friendly": self.batting_friendly,
            "bowling_friendly": self.bowling_friendly,
            "toss_winner": self.toss_winner,
            "decision_after_toss": self.decision_after_toss,
        }

    def update_toss(
        self,
        toss_winner: str,
        decision_after_toss: str,
    ) -> None:
        """Update toss information after the toss occurs."""

        self.toss_winner = toss_winner
        self.decision_after_toss = decision_after_toss


@dataclass
class Match:
    """Represents the complete context of a fantasy cricket match."""

    id: str

    team_a: str
    team_b: str

    venue: str

    date: str
    start_time: str

    weather: WeatherState
    context: MatchContext

    status: str = "upcoming"

    metadata: Dict[str, str] = field(default_factory=dict)

    def involves_team(self, team_name: str) -> bool:
        """Return True if the given real-world team is playing this match."""

        return team_name in (self.team_a, self.team_b)

    def get_opponent(self, team_name: str) -> str | None:
        """Return the opponent of a team participating in this match."""

        if team_name == self.team_a:
            return self.team_b

        if team_name == self.team_b:
            return self.team_a

        return None

    def to_dict(self) -> dict:
        """Return the complete match as a serializable dictionary."""

        return {
            "id": self.id,
            "team_a": self.team_a,
            "team_b": self.team_b,
            "venue": self.venue,
            "date": self.date,
            "start_time": self.start_time,
            "weather": self.weather.to_dict(),
            "context": self.context.to_dict(),
            "status": self.status,
            "metadata": self.metadata.copy(),
        }