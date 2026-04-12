from __future__ import annotations

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE


def search_catalogue(query: str, source: str | None = None) -> list[dict]:
    needle = query.strip().lower()
    results: list[dict] = []

    collections = []
    if source in (None, "abs"):
        collections.append(("abs", ABS_CATALOGUE))
    if source in (None, "rba"):
        collections.append(("rba", RBA_CATALOGUE))

    for collection_source, collection in collections:
        for entry in collection.values():
            score = _score_entry(needle, entry)
            if score <= 0:
                continue
            results.append(
                {
                    "id": entry["id"],
                    "source": collection_source,
                    "name": entry["name"],
                    "description": entry["description"],
                    "frequency": entry["frequency"],
                    "score": score,
                }
            )

    return sorted(results, key=lambda item: item["score"], reverse=True)


def _score_entry(query: str, entry: dict) -> int:
    if not query:
        return 0

    score = 0
    aliases = [alias.lower() for alias in entry.get("aliases", [])]
    name = entry["name"].lower()
    description = entry["description"].lower()

    if query in aliases:
        score += 120
    if query == name:
        score += 100
    if query in name:
        score += 45
    if query in description:
        score += 25

    query_terms = set(query.split())
    for alias in aliases:
        alias_terms = set(alias.split())
        overlap = len(query_terms & alias_terms)
        if overlap and (
            overlap == len(query_terms)
            or query in alias
            or alias in query
            or (len(query_terms) == 1 and overlap == 1)
        ):
            score += overlap * 20

    return score
