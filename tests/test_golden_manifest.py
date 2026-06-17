from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration_tests.golden import load_golden_values  # noqa: E402


def test_golden_manifest_is_valid_and_covers_all_three_sources() -> None:
    entries = load_golden_values()

    assert len(entries) >= 4, "expect at least the 4 seed golden values"
    assert {e.source for e in entries} == {"abs", "rba", "apra"}, "all three sources must be pinned"

    for entry in entries:
        assert entry.tolerance >= 0.0
        assert entry.note.strip(), f"{entry.id} must explain why the value is non-revising"
        assert "REPLACE_WITH" not in entry.key
