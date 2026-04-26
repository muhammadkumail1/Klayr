"""
Anthropic Claude implementation of ILLMClient.
Infrastructure layer — only file that imports anthropic SDK.
"""
from __future__ import annotations

import logging
import os

import anthropic

from domain.ports.llm_client import ILLMClient

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 4096


class AnthropicClient(ILLMClient):
    """
    Wraps the Anthropic Messages API.
    Uses the async client — safe to share across concurrent FastAPI requests.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Obtain a key at https://console.anthropic.com/."
            )
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, system: str, prompt: str) -> str:
        """
        Send system + user prompt to Claude and return the text response.
        Raises anthropic.APIError on unrecoverable failures (let the caller handle retries).
        """
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        logger.debug(
            "LLM call: model=%s input_tokens=%d output_tokens=%d",
            self._model,
            msg.usage.input_tokens,
            msg.usage.output_tokens,
        )
        return text
