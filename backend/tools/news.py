from __future__ import annotations

from typing import Any

from backend.models.state import AgentState


class NewsTool:
    """
    Deterministic tool for retrieving match and player news.

    News is treated as external information available to the agent.
    The tool retrieves and filters news but does not decide whether
    a team should be changed.
    """

    name = "news"

    def __init__(self, state: AgentState) -> None:
        self.state = state

    def get_latest_news(self) -> list[dict[str, Any]]:
        """Return all news currently available in the environment."""
        return list(self.state.environment.latest_news)

    def get_news_count(self) -> int:
        """Return the number of news items currently available."""
        return len(self.state.environment.latest_news)

    def get_news_for_player(
        self,
        player_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return news items associated with a specific player.

        The method checks common player-id fields so the tool can work
        with different news-event payload structures.
        """
        results: list[dict[str, Any]] = []

        for news_item in self.state.environment.latest_news:
            if self._news_mentions_player(news_item, player_id):
                results.append(dict(news_item))

        return results

    def get_news_for_players(
        self,
        player_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Return news associated with any player in the supplied list."""
        player_id_set = set(player_ids)

        return [
            dict(news_item)
            for news_item in self.state.environment.latest_news
            if any(
                self._news_mentions_player(news_item, player_id)
                for player_id in player_id_set
            )
        ]

    def get_news_by_type(
        self,
        news_type: str,
    ) -> list[dict[str, Any]]:
        """Return news items matching a specific type."""
        return [
            dict(news_item)
            for news_item in self.state.environment.latest_news
            if news_item.get("type") == news_type
        ]

    def has_news_changed(
        self,
        previous_count: int,
    ) -> bool:
        """
        Detect whether new news has appeared since a previous count.
        """
        return self.get_news_count() != previous_count

    def get_news_snapshot(self) -> dict[str, Any]:
        """
        Return a snapshot of the current news state.

        The environment version helps the agent correlate news with
        other environment changes.
        """
        return {
            "environment_version": self.state.environment.version,
            "count": self.get_news_count(),
            "news": self.get_latest_news(),
        }

    def _news_mentions_player(
        self,
        news_item: dict[str, Any],
        player_id: str,
    ) -> bool:
        """Check whether a news item references a given player."""
        if news_item.get("player_id") == player_id:
            return True

        if news_item.get("affected_player_id") == player_id:
            return True

        payload = news_item.get("payload")

        if isinstance(payload, dict):
            if payload.get("player_id") == player_id:
                return True

            if payload.get("affected_player_id") == player_id:
                return True

        return False


def create_news_tool(
    state: AgentState,
) -> NewsTool:
    """Create a news tool for the current agent state."""
    return NewsTool(state)