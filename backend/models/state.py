from dataclasses import dataclass, field
from typing import Any

from .player import Player
from .match import Match
from .team import FantasyTeam
from .constraints import (
    TeamConstraints,
    UserPreferences,
)


@dataclass
class EnvironmentState:
    """
    Represents the current observable state of the simulated
    fantasy-cricket environment.
    """

    version: int = 1

    players: dict[str, Player] = field(
        default_factory=dict
    )

    match: Match | None = None

    latest_news: list[dict[str, Any]] = field(
        default_factory=list
    )

    events: list[dict[str, Any]] = field(
        default_factory=list
    )

    def get_player(self, player_id: str) -> Player | None:
        """Return a player by ID if present."""

        return self.players.get(player_id)

    def add_event(self, event: dict[str, Any]) -> None:
        """Record an event that occurred in the environment."""

        self.events.append(event)

    def add_news(self, news_item: dict[str, Any]) -> None:
        """Record the latest news item."""

        self.latest_news.append(news_item)

    def increment_version(self) -> None:
        """Increment the environment version after a state change."""

        self.version += 1

    def to_dict(self) -> dict[str, Any]:
        """Return the complete environment as a serializable dictionary."""

        return {
            "version": self.version,
            "players": {
                player_id: player.to_dict()
                for player_id, player in self.players.items()
            },
            "match": (
                self.match.to_dict()
                if self.match is not None
                else None
            ),
            "latest_news": list(self.latest_news),
            "events": list(self.events),
        }


@dataclass
class AgentState:
    """
    Central state object used by the CricPilot autonomous agent.

    The state contains the user's goal, preferences, hard constraints,
    current environment, generated teams, observations, actions,
    tool results, and adaptation history.
    """

    goal: str = ""

    preferences: UserPreferences = field(
        default_factory=UserPreferences
    )

    constraints: TeamConstraints = field(
        default_factory=TeamConstraints
    )

    environment: EnvironmentState = field(
        default_factory=EnvironmentState
    )

    current_team: FantasyTeam | None = None

    candidate_teams: list[FantasyTeam] = field(
        default_factory=list
    )

    observations: list[dict[str, Any]] = field(
        default_factory=list
    )

    actions: list[dict[str, Any]] = field(
        default_factory=list
    )

    tool_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    revisions: int = 0

    status: str = "idle"

    def record_observation(
        self,
        observation: dict[str, Any],
    ) -> None:
        """Record something the agent observed from the environment."""

        self.observations.append(observation)

    def record_action(
        self,
        action: dict[str, Any],
    ) -> None:
        """Record an action selected or executed by the agent."""

        self.actions.append(action)

    def record_tool_result(
        self,
        tool_name: str,
        result: Any,
    ) -> None:
        """Record the result returned by a tool."""

        self.tool_results.append(
            {
                "tool": tool_name,
                "result": result,
            }
        )

    def increment_revision(self) -> None:
        """Record that the agent had to revise its previous decision."""

        self.revisions += 1

    def set_status(self, status: str) -> None:
        """Update the current agent lifecycle status."""

        self.status = status

    def set_current_team(
        self,
        team: FantasyTeam | None,
    ) -> None:
        """Set or clear the team's current selected team."""

        self.current_team = team

    def add_candidate_team(
        self,
        team: FantasyTeam,
    ) -> None:
        """Add a generated candidate team."""

        self.candidate_teams.append(team)

    def clear_candidate_teams(self) -> None:
        """Remove previously generated candidate teams."""

        self.candidate_teams.clear()

    def to_dict(self) -> dict[str, Any]:
        """Return the complete agent state as a serializable dictionary."""

        return {
            "goal": self.goal,
            "preferences": self.preferences.to_dict(),
            "constraints": self.constraints.to_dict(),
            "environment": self.environment.to_dict(),
            "current_team": (
                self.current_team.to_dict()
                if self.current_team is not None
                else None
            ),
            "candidate_teams": [
                team.to_dict()
                for team in self.candidate_teams
            ],
            "observations": list(self.observations),
            "actions": list(self.actions),
            "tool_results": list(self.tool_results),
            "revisions": self.revisions,
            "status": self.status,
        }

