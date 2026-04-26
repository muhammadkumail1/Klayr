"""
PubMed search implementation via NCBI E-utilities.
Two-step: ESearch (get IDs) → EFetch (get full XML records with abstracts).
"""
from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET

import httpx

from domain.entities.experiment import Paper
from domain.ports.lit_search import ILitSearch

logger = logging.getLogger(__name__)

_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT = 15.0


class PubMedClient(ILitSearch):
    """Queries NCBI PubMed via the E-utilities REST API."""

    def __init__(self, api_key: str = "") -> None:
        # Free NCBI account key raises rate limit from 3 → 10 req/sec
        self._api_key = api_key or os.environ.get("NCBI_API_KEY", "")

    async def search(self, query: str) -> list[Paper]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Step 1 — ESearch: get PubMed IDs
            search_params: dict = {
                "db": "pubmed",
                "term": query,
                "retmax": 5,
                "retmode": "json",
                "usehistory": "n",
            }
            if self._api_key:
                search_params["api_key"] = self._api_key

            search_resp = await client.get(_ESEARCH, params=search_params)
            search_resp.raise_for_status()

            ids: list[str] = (
                search_resp.json().get("esearchresult", {}).get("idlist", [])
            )
            if not ids:
                logger.debug("PubMed: no results for query: %.80s", query)
                return []

            # Step 2 — EFetch: get full records (XML)
            fetch_params: dict = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml",
                "rettype": "abstract",
            }
            if self._api_key:
                fetch_params["api_key"] = self._api_key

            fetch_resp = await client.get(_EFETCH, params=fetch_params)
            fetch_resp.raise_for_status()

        papers = self._parse_xml(fetch_resp.text)
        logger.debug("PubMed returned %d results for query: %.80s", len(papers), query)
        return papers

    def _parse_xml(self, xml_text: str) -> list[Paper]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.error("PubMed XML parse error: %s", exc)
            return []

        papers: list[Paper] = []
        for article in root.findall(".//PubmedArticle"):
            try:
                medline = article.find("MedlineCitation")
                if medline is None:
                    continue
                art = medline.find("Article")
                if art is None:
                    continue

                title = art.findtext("ArticleTitle", default="").strip()

                year_el = art.find("Journal/JournalIssue/PubDate/Year")
                year = int(year_el.text) if year_el is not None and year_el.text else 0

                authors: list[str] = []
                for a in art.findall("AuthorList/Author")[:3]:
                    last = a.findtext("LastName", "")
                    fore = a.findtext("ForeName", "")
                    name = f"{fore} {last}".strip()
                    if name:
                        authors.append(name)

                # Structured abstracts have multiple AbstractText elements with Label attrs
                abstract_parts = art.findall("Abstract/AbstractText")
                abstract: str | None = None
                if abstract_parts:
                    segments = []
                    for el in abstract_parts:
                        label = el.get("Label", "")
                        text = el.text or ""
                        segments.append(f"{label + ': ' if label else ''}{text}")
                    joined = " ".join(segments).strip()
                    abstract = joined if joined else None

                pmid = medline.findtext("PMID", "")
                doi_el = article.find(".//ArticleId[@IdType='doi']")
                doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""

                papers.append(
                    Paper(
                        title=title,
                        authors=authors,
                        year=year,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        abstract=abstract,
                        abstract_summary=None,
                        source="pubmed",
                        relevance_note=doi,  # temp DOI for dedup
                    )
                )
            except Exception as exc:
                logger.debug("Skipping malformed PubMed record: %s", exc)
                continue

        return papers
