from abc import ABC, abstractmethod


class ILLMClient(ABC):
    """Port: language-model completion.
    Domain layer depends on this abstraction only — never on anthropic/openai directly.
    """

    @abstractmethod
    async def complete(self, system: str, prompt: str) -> str:
        """Send a system + user prompt; return the model's text response."""
        ...
