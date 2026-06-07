from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_apra_parser_benchmark_outputs_layout_metrics() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_apra_parser.py",
            "--row-count",
            "14",
            "--date-count",
            "3",
            "--repeats",
            "1",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["benchmark"] == "apra_parser"
    assert payload["row_count"] == 14
    assert payload["date_count"] == 3
    assert payload["repeats"] == 1

    results = payload["results"]
    assert {item["layout"] for item in results} == {"row_records", "matrix", "period_rows"}
    for item in results:
        assert item["rows"] > 0
        assert item["columns"] > 0
        assert item["workbook_bytes"] > 0
        assert item["series"] > 0
        assert item["observations"] > 0
        assert item["elapsed_ms"] >= 0
        assert item["observations_per_second"] >= 0
