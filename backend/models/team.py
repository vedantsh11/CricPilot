from dataclasses import dataclass, field
from typing import List

from .player import Player


@dataclass
class FantasyTeam:
    """
    Represents a fantasy cricket team inside the CricPilot
    simulated environment.

    This model stores the selected players and basic team state.
    Hard constraint validation is handled separately by the
    validator tool.
    """

    # -------------------------
    # Identity
    # -------------------------

    id: str

    # -------------------------
    # Squad
    # -------------------------

    players: List[Player] = field(
        default_factory=list
    )

    # -------------------------
    # Captaincy
    # -------------------------

    captain_id: str | None = None

    vice_captain_id: str | None = None

    # -------------------------
    # Team state
    # -------------------------

    status: str = "draft"

    projected_points: float = 0.0

    total_cost: float = 0.0

    # -------------------------
    # Cost
    # -------------------------

    def calculate_cost(self) -> float:
        """
        Calculate and update the total credit cost
        of the team.
        """

        self.total_cost = sum(
            player.credits
            for player in self.players
        )

        return self.total_cost

    # -------------------------
    # Player lookup
    # -------------------------

    def contains_player(
        self,
        player_id: str
    ) -> bool:
        """
        Check whether a player is already in the team.
        """

        return any(
            player.id == player_id
            for player in self.players
        )

    def get_player(
        self,
        player_id: str
    ) -> Player | None:
        """
        Return a player by ID.

        Returns None if the player is not in the team.
        """

        for player in self.players:
            if player.id == player_id:
                return player

        return None

    # -------------------------
    # Player management
    # -------------------------

    def add_player(
        self,
        player: Player
    ) -> bool:
        """
        Add a player to the team.

        Returns:
            True  -> player was added
            False -> player was already present
        """

        if self.contains_player(player.id):
            return False

        self.players.append(player)

        self.calculate_cost()

        return True

    def remove_player(
        self,
        player_id: str
    ) -> bool:
        """
        Remove a player from the team.

        Returns:
            True  -> player was removed
            False -> player was not found
        """

        original_length = len(
            self.players
        )

        self.players = [
            player
            for player in self.players
            if player.id != player_id
        ]

        removed = (
            len(self.players)
            < original_length
        )

        if removed:

            # Clear captaincy if the removed player
            # was captain or vice-captain.
            if self.captain_id == player_id:
                self.captain_id = None

            if self.vice_captain_id == player_id:
                self.vice_captain_id = None

            self.calculate_cost()

        return removed

    # -------------------------
    # Captain / Vice-Captain
    # -------------------------

    def set_captain(
        self,
        player_id: str
    ) -> bool:
        """
        Set a player as captain.

        The player must already belong to the team.
        """

        if not self.contains_player(player_id):
            return False

        # Captain and vice-captain should not
        # be the same player.
        if self.vice_captain_id == player_id:
            self.vice_captain_id = None

        self.captain_id = player_id

        return True

    def set_vice_captain(
        self,
        player_id: str
    ) -> bool:
        """
        Set a player as vice-captain.

        The player must already belong to the team.
        """

        if not self.contains_player(player_id):
            return False

        # Captain and vice-captain cannot
        # be the same player.
        if self.captain_id == player_id:
            return False

        self.vice_captain_id = player_id

        return True

    # -------------------------
    # Team information
    # -------------------------

    @property
    def size(self) -> int:
        """
        Return the number of players currently
        selected in the team.
        """

        return len(self.players)

    @property
    def player_ids(self) -> List[str]:
        """
        Return the IDs of all selected players.
        """

        return [
            player.id
            for player in self.players
        ]

    # -------------------------
    # Serialization
    # -------------------------

    def to_dict(self) -> dict:
        """
        Convert the fantasy team into a dictionary.

        Useful for:
        - API responses
        - frontend display
        - logging
        - agent traces
        """

        return {
            "id": self.id,
            "players": [
                player.to_dict()
                for player in self.players
            ],
            "player_ids": self.player_ids,
            "captain_id": self.captain_id,
            "vice_captain_id": self.vice_captain_id,
            "status": self.status,
            "projected_points": self.projected_points,
            "total_cost": self.total_cost,
            "size": self.size,
        }