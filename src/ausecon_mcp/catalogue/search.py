from __future__ import annotations

import re
from collections.abc import Iterable

from ausecon_mcp.catalogue.abs import ABS_CATALOGUE
from ausecon_mcp.catalogue.rba import RBA_CATALOGUE

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_TOKEN_SYNONYMS = {
    "jobless": "unemployment",
    "jobs": "job",
    "labour": "labour",
    "labor": "labour",
    "prices": "price",
    "rates": "rate",
    "wages": "wage",
    "fx": "exchange",
    "mortgages": "mortgage",
    "loans": "loan",
    "yields": "yield",
}


def search_catalogue(query: str, source: str | None = None) -> list[dict]:
    query_text = _normalise_text(query)
    if not query_text:
        return []

    query_terms = _tokenise(query_text)
    results: list[dict] = []

    for collection_source, collection in _iter_collections(source):
        for entry in collection.values():
            if entry.get("discontinued", False):
                continue

            score = _score_entry(query_text, query_terms, entry)
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

    return sorted(results, key=lambda item: (-item["score"], item["source"], item["id"]))


def _iter_collections(source: str | None) -> Iterable[tuple[str, dict]]:
    if source in (None, "abs"):
        yield "abs", ABS_CATALOGUE
    if source in (None, "rba"):
        yield "rba", RBA_CATALOGUE


def _score_entry(query_text: str, query_terms: set[str], entry: dict) -> int:
    entry_id = _normalise_text(entry["id"])
    aliases = [_normalise_text(alias) for alias in entry.get("aliases", [])]
    name = _normalise_text(entry["name"])
    tags = [_normalise_text(tag) for tag in entry.get("tags", [])]
    description = _normalise_text(entry["description"])

    if query_text == entry_id:
        return 1000
    if query_text in aliases:
        return 900
    if query_text == name:
        return 800

    exact_group = aliases + [name] + tags
    full_match_score = _best_full_term_score(query_terms, exact_group)
    if full_match_score:
        return 700 + full_match_score

    partial_match_score = _best_partial_term_score(query_terms, exact_group)
    if partial_match_score:
        return 400 + partial_match_score

    description_score = _best_partial_term_score(query_terms, [description])
    if description_score:
        return 100 + description_score

    return 0


def _best_full_term_score(query_terms: set[str], candidates: list[str]) -> int:
    best = 0
    for candidate in candidates:
        candidate_terms = _tokenise(candidate)
        if not candidate_terms or not query_terms <= candidate_terms:
            continue

        # Reward full coverage and prefer tighter matches.
        score = len(query_terms) * 20 - (len(candidate_terms) - len(query_terms))
        best = max(best, score)
    return best


def _best_partial_term_score(query_terms: set[str], candidates: list[str]) -> int:
    best = 0
    min_overlap = 1 if len(query_terms) == 1 else min(len(query_terms), 2)
    for candidate in candidates:
        candidate_terms = _tokenise(candidate)
        overlap = len(query_terms & candidate_terms)
        if overlap < min_overlap:
            continue

        score = overlap * 15
        if overlap == len(query_terms):
            score += 10
        best = max(best, score)
    return best


def _normalise_text(value: str) -> str:
    return " ".join(_normalise_tokens(value))


def _tokenise(value: str) -> set[str]:
    return set(_normalise_tokens(value))


def _normalise_tokens(value: str) -> list[str]:
    return [
        _TOKEN_SYNONYMS.get(raw_token, raw_token) for raw_token in _TOKEN_RE.findall(value.lower())
    ]
