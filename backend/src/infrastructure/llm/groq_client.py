"""
Groq implementation of ILLMClient.
Infrastructure layer — only file that imports the groq SDK.
Uses llama-3.3-70b-versatile by default (fast, free tier generous).
"""
from __future__ import annotations

import logging
import os

from groq import AsyncGroq

from domain.ports.llm_client import ILLMClient

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_MAX_TOKENS = 4096


class GroqClient(ILLMClient):
    """
    Wraps the Groq Chat Completions API (OpenAI-compatible).
    Async client — safe to share across concurrent FastAPI requests.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        api_key: str | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("GROQ_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Obtain a free key at https://console.groq.com/."
            )
        self._client = AsyncGroq(api_key=resolved_key)
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, system: str, prompt: str) -> str:
        """
        Send system + user prompt to Groq and return the text response.
        Raises groq.APIError on unrecoverable failures.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        logger.debug("Groq response length: %d chars", len(text))
        return text
