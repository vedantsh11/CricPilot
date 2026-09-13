from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    """
    Wrapper around the xAI Grok API.

    xAI provides an OpenAI-compatible API,
    so we can use the OpenAI Python SDK.
    """

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"

        load_dotenv(env_path)

        api_key = os.getenv("XAI_API_KEY")
        model = os.getenv("CRICPILOT_MODEL", "grok-4.6")

        if not api_key:
            raise RuntimeError(
                f"XAI_API_KEY is not configured. "
                f"Expected .env at: {env_path}"
            )

        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

    def ask(self, prompt: str) -> str:
        """
        Send a prompt to Grok and return its text response.
        """

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return response.output_text


def create_llm_client() -> LLMClient:
    """Create and return an LLM client."""
    return LLMClient()