from abc import ABC, abstractmethod
from domain.entities.experiment import Paper


class ILitSearch(ABC):
    """Port: literature search.
    Implementations may call Semantic Scholar, PubMed, or a combined client.
    """

    @abstractmethod
    async def search(self, query: str) -> list[Paper]:
        """Return up to 3 deduplicated, summarised Papers for *query*."""
        ...
