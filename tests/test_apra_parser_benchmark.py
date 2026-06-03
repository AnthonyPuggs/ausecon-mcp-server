from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_apra_parser.py"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location("benchmark_apra_parser", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_apra_parser_benchmark_defaults_are_smoke_sized() -> None:
    args = _load_benchmark_module().build_arg_parser().parse_args([])

    assert args.row_count == 100
    assert args.date_count == 12
    assert args.repeats == 1


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
        timeout=15,
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
