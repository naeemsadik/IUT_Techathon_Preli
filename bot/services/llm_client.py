"""Groq-backed LLM response service."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are a friendly office energy assistant for a Discord server. "
    "Turn structured office energy data into a warm, concise, human reply. "
    "Do not mention JSON, schemas, fields, APIs, or implementation details. "
    "Keep command replies under 120 words. "
    "Keep alert replies under 45 words. "
    "Use plain text that reads well in Discord."
)


class LlmClientError(Exception):
    """Raised when the LLM service cannot produce a reply."""


class LlmClient:
    """Client for Groq's OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        enabled: bool = True,
        timeout_seconds: float = 20.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._enabled = enabled and bool(api_key)
        self._client = http_client or httpx.AsyncClient(timeout=timeout_seconds)

    @property
    def is_enabled(self) -> bool:
        """Return whether LLM calls are enabled and configured."""

        return self._enabled

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def command_reply(self, command_name: str, deterministic_text: str) -> str:
        """Create a friendly command response."""

        prompt = (
            f"The user ran !{command_name}. Rewrite this office energy response "
            f"into a helpful, conversational Discord message:\n\n{deterministic_text}"
        )
        return await self._complete(prompt)

    async def alert_reply(self, alert_message: str) -> str:
        """Create a friendly alert response."""

        prompt = (
            "Rewrite this office energy alert into a friendly proactive Discord "
            f"notification:\n\n{alert_message}"
        )
        return await self._complete(prompt)

    async def conversation_reply(self, user_message: str, context: str) -> str:
        """Answer a general user question using current office context."""

        prompt = (
            "A Discord user asked a question about the office energy system. "
            "Answer conversationally using only the context below. If the context "
            "does not contain the answer, say what you can infer and suggest a "
            "specific command to check next.\n\n"
            f"Question:\n{user_message}\n\nContext:\n{context}"
        )
        return await self._complete(prompt)

    async def _complete(self, prompt: str) -> str:
        if not self._enabled:
            raise LlmClientError("LLM is not configured.")

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                GROQ_CHAT_COMPLETIONS_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("LLM request failed: %s", exc)
            raise LlmClientError("The LLM response service is unavailable.") from exc

        if not content:
            raise LlmClientError("The LLM returned an empty response.")
        return content
