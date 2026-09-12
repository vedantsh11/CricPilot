from backend.models.state import (
    AgentState,
    EnvironmentState
)

from backend.data.seed_data import (
    create_players,
    create_match
)

def create_initial_state() -> AgentState:

    players = create_players()

    environment = EnvironmentState(
        version=1,
        players={
            player.id: player
            for player in players
        },
        match=create_match()
    )

    state = AgentState(
        goal=(
            "Create the best balanced fantasy cricket "
            "team while satisfying all constraints."
        ),
        environment=environment
    )

    return state


def print_state(state: AgentState):

    match = state.environment.match

    print("\n" + "=" * 50)
    print("             CRICPILOT")
    print("        AGENTIC SPORTS ENGINE")
    print("=" * 50)

    print(f"\nEnvironment Version : {state.environment.version}")

    if match:
        print(
            f"Match               : "
            f"{match.team_a} vs {match.team_b}"
        )

        print(f"Venue               : {match.venue}")

        print(
            f"Weather             : "
            f"{match.weather.condition}"
        )

        print(
            f"Rain Probability    : "
            f"{match.weather.rain_probability}%"
        )

    print(
        f"\nPlayers Loaded      : "
        f"{len(state.environment.players)}"
    )

    print(
        f"Budget              : "
        f"{state.constraints.budget}"
    )

    print(
        f"Squad Size          : "
        f"{state.constraints.squad_size}"
    )

    print(
        f"Risk Profile        : "
        f"{state.preferences.risk_profile.value}"
    )

    print(
        f"\nAgent Status        : "
        f"{state.status}"
    )

    print("=" * 50)


if __name__ == "__main__":

    state = create_initial_state()

    print_state(state)