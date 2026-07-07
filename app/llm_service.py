"""
Thin wrapper around a local Ollama model (default: phi3). No external API
keys, no network calls beyond localhost -> fully offline-capable once the
model is pulled (`ollama pull phi3`).
"""
import json
import logging
from typing import Optional

import ollama

from app.config import settings

logger = logging.getLogger("codemind.llm")

_client = ollama.Client(host=settings.OLLAMA_HOST)


class LLMService:
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL

    def chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        """Single-turn chat completion. Always stream=False (per your setup)."""
        try:
            response = _client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                options={"temperature": temperature},
                stream=False,
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise RuntimeError(
                f"Could not reach Ollama at {settings.OLLAMA_HOST} with model "
                f"'{self.model}'. Is `ollama serve` running and has the model "
                f"been pulled (`ollama pull {self.model}`)? Original error: {e}"
            )

    def chat_json(self, system: str, user: str, temperature: float = 0.1) -> dict:
        """Ask the model for strict JSON output and parse it defensively."""
        raw = self.chat(
            system=system + "\n\nRespond with ONLY valid JSON. No markdown fences, no prose.",
            user=user,
            temperature=temperature,
        )
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError:
                    pass
            logger.warning("LLM did not return valid JSON, returning raw text wrapper")
            return {"raw": raw}


llm = LLMService()
