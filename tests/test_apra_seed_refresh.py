import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_apra_url_seeds.py"
SPEC = importlib.util.spec_from_file_location("refresh_apra_url_seeds", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
refresh_apra_url_seeds = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh_apra_url_seeds)
_normalise_for_check = refresh_apra_url_seeds._normalise_for_check


def test_apra_seed_refresh_check_ignores_checked_at_clock_values() -> None:
    current = {
        "TEST_PUBLICATION": [
            {
                "url": "https://www.apra.gov.au/sites/default/files/test.xlsx",
                "label": "Test publication",
                "checked_at": "2026-05-20T00:00:00Z",
            }
        ]
    }
    refreshed = {
        "TEST_PUBLICATION": [
            {
                "url": "https://www.apra.gov.au/sites/default/files/test.xlsx",
                "label": "Test publication",
                "checked_at": "2026-06-03T00:00:00Z",
            }
        ]
    }

    assert _normalise_for_check(current) == _normalise_for_check(refreshed)
