from __future__ import annotations

_GEOGRAPHY_ALIASES = {
    "aus": "aus",
    "australia": "aus",
    "commonwealth of australia": "aus",
    "national": "aus",
    "nsw": "nsw",
    "new south wales": "nsw",
    "vic": "vic",
    "victoria": "vic",
    "qld": "qld",
    "queensland": "qld",
    "sa": "sa",
    "south australia": "sa",
    "wa": "wa",
    "western australia": "wa",
    "tas": "tas",
    "tasmania": "tas",
    "nt": "nt",
    "northern territory": "nt",
    "act": "act",
    "australian capital territory": "act",
}


def normalise_geography(value: str | None) -> str | None:
    if value is None:
        return None
    normalised = " ".join(value.strip().lower().replace("_", " ").split())
    if not normalised:
        return ""
    return _GEOGRAPHY_ALIASES.get(normalised, normalised)


def geography_alias_rows() -> list[dict[str, str]]:
    return [
        {"alias": alias, "canonical": canonical}
        for alias, canonical in sorted(_GEOGRAPHY_ALIASES.items())
    ]
