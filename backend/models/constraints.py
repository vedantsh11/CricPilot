from dataclasses import dataclass, field
from enum import Enum


class RiskProfile(str, Enum):
    """
    Defines how aggressively CricPilot should select players.
    """

    SAFE = "safe"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class TeamConstraints:
    """
    Hard constraints that every generated fantasy team
    must satisfy.

    These constraints are deterministic and should be
    verified by the validator rather than by the LLM.
    """

    # -------------------------
    # Basic constraints
    # -------------------------

    budget: float = 100.0

    squad_size: int = 11

    max_players_per_real_team: int = 7

    # -------------------------
    # Role constraints
    # -------------------------

    min_wicketkeepers: int = 1

    min_batters: int = 3

    min_all_rounders: int = 1

    min_bowlers: int = 3

    # -------------------------
    # Validation helpers
    # -------------------------

    def minimum_required_players(self) -> int:
        """
        Return the minimum number of players required
        by the role constraints.
        """

        return (
            self.min_wicketkeepers
            + self.min_batters
            + self.min_all_rounders
            + self.min_bowlers
        )

    def is_role_configuration_possible(self) -> bool:
        """
        Check whether the role minimums can fit inside
        the requested squad size.
        """

        return (
            self.minimum_required_players()
            <= self.squad_size
        )

    def to_dict(self) -> dict:
        """
        Convert constraints into a serializable dictionary.
        """

        return {
            "budget": self.budget,
            "squad_size": self.squad_size,
            "max_players_per_real_team": (
                self.max_players_per_real_team
            ),
            "min_wicketkeepers": (
                self.min_wicketkeepers
            ),
            "min_batters": self.min_batters,
            "min_all_rounders": (
                self.min_all_rounders
            ),
            "min_bowlers": self.min_bowlers,
        }


@dataclass
class UserPreferences:
    """
    Soft preferences provided by the user.

    Unlike TeamConstraints, these do not necessarily make
    a team invalid. They influence how candidate teams
    are ranked.
    """

    # -------------------------
    # Risk
    # -------------------------

    risk_profile: RiskProfile = (
        RiskProfile.BALANCED
    )

    # -------------------------
    # Player preferences
    # -------------------------

    preferred_players: list[str] = field(
        default_factory=list
    )

    avoided_players: list[str] = field(
        default_factory=list
    )

    # -------------------------
    # Optimization preferences
    # -------------------------

    prioritize_form: bool = True

    prioritize_consistency: bool = True

    prioritize_high_ceiling: bool = False

    # -------------------------
    # Serialization
    # -------------------------

    def to_dict(self) -> dict:
        """
        Convert user preferences into a serializable
        dictionary.
        """

        return {
            "risk_profile": (
                self.risk_profile.value
            ),
            "preferred_players": (
                self.preferred_players
            ),
            "avoided_players": (
                self.avoided_players
            ),
            "prioritize_form": (
                self.prioritize_form
            ),
            "prioritize_consistency": (
                self.prioritize_consistency
            ),
            "prioritize_high_ceiling": (
                self.prioritize_high_ceiling
            ),
        }