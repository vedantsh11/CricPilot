from dataclasses import dataclass, field
from enum import Enum
from typing import List


class PlayerRole(str, Enum):
    WICKETKEEPER = "wicketkeeper"
    BATTER = "batter"
    ALL_ROUNDER = "all_rounder"
    BOWLER = "bowler"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    DOUBTFUL = "doubtful"
    UNAVAILABLE = "unavailable"


@dataclass
class Player:
    # Identity
    id: str
    name: str
    real_team: str
    role: PlayerRole

    # Fantasy attributes
    credits: float
    fantasy_avg: float
    fantasy_ceiling: float

    recent_points: List[float] = field(default_factory=list)

    # Performance ratings
    batting_rating: float = 0.0
    bowling_rating: float = 0.0
    form_rating: float = 0.0
    consistency_rating: float = 0.0
    upside_rating: float = 0.0

    # Match-context ratings
    powerplay_rating: float = 0.0
    death_overs_rating: float = 0.0
    pace_rating: float = 0.0
    spin_rating: float = 0.0
    venue_rating: float = 0.0

    # Availability
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    availability_reason: str | None = None

    def is_selectable(self) -> bool:
        """Return True only when the player is confirmed available."""
        return self.availability == AvailabilityStatus.AVAILABLE

    @property
    def recent_form(self) -> float:
        """
        Return the average of the player's recent fantasy points.

        If no recent match data is available, form_rating is returned.
        """
        if not self.recent_points:
            return self.form_rating

        return sum(self.recent_points) / len(self.recent_points)

    @property
    def average_recent_points(self) -> float:
        """Alias for recent_form."""
        return self.recent_form

    @property
    def risk_score(self) -> float:
        """
        Estimate player risk from recent fantasy-point volatility.

        Higher value means more volatility.
        Lower value means more consistency.
        """
        if not self.recent_points:
            return max(0.0, 100.0 - self.consistency_rating)

        avg = self.recent_form

        variance = sum(
            (point - avg) ** 2
            for point in self.recent_points
        ) / len(self.recent_points)

        volatility = variance ** 0.5

        return round(min(100.0, volatility), 2)

    def mark_unavailable(self, reason: str) -> None:
        """Mark the player as unavailable."""
        self.availability = AvailabilityStatus.UNAVAILABLE
        self.availability_reason = reason

    def mark_doubtful(self, reason: str) -> None:
        """Mark the player as doubtful."""
        self.availability = AvailabilityStatus.DOUBTFUL
        self.availability_reason = reason

    def mark_available(self) -> None:
        """Restore the player to confirmed availability."""
        self.availability = AvailabilityStatus.AVAILABLE
        self.availability_reason = None

    def to_dict(self) -> dict:
        """Convert the player into a JSON/API-friendly dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "real_team": self.real_team,
            "role": self.role.value,
            "credits": self.credits,
            "fantasy_avg": self.fantasy_avg,
            "fantasy_ceiling": self.fantasy_ceiling,
            "recent_points": self.recent_points,
            "batting_rating": self.batting_rating,
            "bowling_rating": self.bowling_rating,
            "form_rating": self.form_rating,
            "consistency_rating": self.consistency_rating,
            "upside_rating": self.upside_rating,
            "powerplay_rating": self.powerplay_rating,
            "death_overs_rating": self.death_overs_rating,
            "pace_rating": self.pace_rating,
            "spin_rating": self.spin_rating,
            "venue_rating": self.venue_rating,
            "availability": self.availability.value,
            "availability_reason": self.availability_reason,
        }


if __name__ == "__main__":
    player = Player(
        id="P001",
        name="Example Player",
        real_team="Team A",
        role=PlayerRole.ALL_ROUNDER,
        credits=9.5,
        fantasy_avg=55.0,
        fantasy_ceiling=120.0,
        recent_points=[45.0, 60.0, 70.0],
        batting_rating=82.0,
        bowling_rating=75.0,
        form_rating=80.0,
        consistency_rating=78.0,
        upside_rating=88.0,
    )

    print(player.to_dict())