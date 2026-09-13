from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.main import create_initial_state
from backend.simulation.environment import SimulationEnvironment
from backend.agents.orchestrator import Orchestrator
from backend.llm.client import create_llm_client


app = FastAPI(
    title="CricPilot API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# GLOBAL ENGINE
# =========================================================

state = create_initial_state()

environment = SimulationEnvironment(
    state
)

orchestrator = Orchestrator(
    state=state,
    environment=environment,
)

llm = create_llm_client()


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    message: str


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/health")
def health() -> dict[str, Any]:

    return {
        "success": True,
        "service": "CricPilot",
        "status": "online",
    }


# =========================================================
# COMPACT TEAM DATA
# =========================================================

def compact_team(team) -> dict[str, Any] | None:

    if team is None:
        return None

    players = []

    for player in team.players:

        players.append({
            "id": player.id,
            "name": player.name,
            "role": (
                player.role.value
                if hasattr(player.role, "value")
                else str(player.role)
            ),
            "credits": player.credits,
            "real_team": player.real_team,
            "availability": (
                player.availability.value
                if hasattr(player.availability, "value")
                else str(player.availability)
            ),
        })

    return {
        "players": players,
        "captain": team.captain_id,
        "vice_captain": team.vice_captain_id,
        "projected_points": team.projected_points,
        "total_cost": team.total_cost,
        "size": team.size,
        "status": team.status,
    }


# =========================================================
# COMPACT CONTEXT FOR LLM
# =========================================================

def build_context() -> dict[str, Any]:

    constraints = state.constraints

    return {
        "goal": state.goal,
        "preferences": state.preferences,
        "constraints": {
            "budget": constraints.budget,
            "squad_size": constraints.squad_size,
            "max_players_per_real_team": (
                constraints.max_players_per_real_team
            ),
            "min_wicketkeepers": (
                constraints.min_wicketkeepers
            ),
            "min_batters": constraints.min_batters,
            "min_all_rounders": (
                constraints.min_all_rounders
            ),
            "min_bowlers": constraints.min_bowlers,
        },
        "current_team": compact_team(
            state.current_team
        ),
        "status": state.status,
        "revisions": state.revisions,
    }


# =========================================================
# AI PROMPT
# =========================================================

def create_ai_prompt(
    user_message: str,
    engine_result: dict[str, Any],
) -> str:

    context = build_context()

    prompt = f"""
You are CricPilot, an autonomous fantasy cricket manager.

USER REQUEST:
{user_message[:500]}

ENGINE CONTEXT:
{context}

ENGINE RESULT:
{engine_result}

RULES:
- The CricPilot engine is the source of truth.
- Never invent players.
- Never invent statistics.
- Never change the selected team yourself.
- Explain what the engine actually did.
- Mention important constraints.
- If a team was successfully created, summarize it.
- If the engine failed, clearly explain the failure.
- Be concise.
- Maximum 120 words.

Return a professional fantasy-cricket response.
"""

    return prompt


# =========================================================
# REQUEST DETECTION
# =========================================================

def is_build_request(message: str) -> bool:

    text = message.lower()

    keywords = [
        "build",
        "create team",
        "create a team",
        "best xi",
        "fantasy xi",
        "fantasy team",
        "make team",
        "make a team",
        "select team",
        "pick team",
        "pick players",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


def is_adaptation_request(message: str) -> bool:

    text = message.lower()

    keywords = [
        "replace",
        "replacement",
        "unavailable",
        "injured",
        "injury",
        "weather changed",
        "conditions changed",
        "adapt",
        "adaptation",
        "update team",
        "change team",
        "player is out",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# SAFE AI CALL
# =========================================================

def ask_ai(
    user_message: str,
    engine_result: dict[str, Any],
) -> str:

    prompt = create_ai_prompt(
        user_message,
        engine_result,
    )

    try:

        response = llm.ask(prompt)

        if response:
            return response.strip()

        return "CricPilot completed the engine operation."

    except Exception as exc:

        error_text = str(exc)

        if "413" in error_text:
            return (
                "The fantasy engine completed its operation, "
                "but the AI explanation exceeded the model "
                "request limit."
            )

        if "401" in error_text:
            return (
                "The fantasy engine completed its operation, "
                "but Groq authentication failed."
            )

        return (
            "The fantasy engine completed its operation, "
            "but the AI explanation service is temporarily "
            "unavailable."
        )


# =========================================================
# MAIN CHAT ENDPOINT
# =========================================================

@app.post("/api/agent/chat")
def agent_chat(
    request: ChatRequest,
) -> dict[str, Any]:

    message = request.message.strip()

    if not message:

        return {
            "success": False,
            "error": "Message cannot be empty.",
        }

    # =====================================================
    # BUILD TEAM
    # =====================================================

    if is_build_request(message):

        try:

            result = orchestrator.run_initial_cycle(
                candidate_limit=10
            )

            ai_response = ask_ai(
                message,
                result,
            )

            return {
                "success": result.get(
                    "success",
                    False,
                ),
                "message": ai_response,
                "engine_result": result,
                "team": (
                    compact_team(
                        state.current_team
                    )
                    if state.current_team
                    else None
                ),
            }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc),
            }

    # =====================================================
    # ADAPT TEAM
    # =====================================================

    if is_adaptation_request(message):

        try:

            result = orchestrator.adapt_to_changes()

            ai_response = ask_ai(
                message,
                result,
            )

            return {
                "success": result.get(
                    "success",
                    False,
                ),
                "message": ai_response,
                "engine_result": result,
                "team": (
                    compact_team(
                        state.current_team
                    )
                    if state.current_team
                    else None
                ),
            }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc),
            }

    # =====================================================
    # NORMAL AI CHAT
    # =====================================================

    try:

        context = build_context()

        prompt = f"""
You are CricPilot, a professional autonomous
fantasy cricket assistant.

User:
{message[:500]}

Current system state:
{context}

Answer clearly and briefly.

Do not invent player information.
Do not claim an action was performed unless
the engine performed it.

Maximum 100 words.
"""

        response = llm.ask(prompt)

        return {
            "success": True,
            "message": response.strip(),
            "team": (
                compact_team(
                    state.current_team
                )
                if state.current_team
                else None
            ),
        }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
        }