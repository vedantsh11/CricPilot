from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:

    def __init__(self):

        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"

        load_dotenv(env_path)

        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        if not self.api_key:
            raise RuntimeError(
                f"GROQ_API_KEY is not configured. "
                f"Expected .env at: {env_path}"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    def ask(self, prompt: str) -> str:

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text


def create_llm_client() -> LLMClient:
    return LLMClient()