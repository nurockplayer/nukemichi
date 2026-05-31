from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.data_store import load_station_bundle
from app.data_validation import validate_station_bundle


BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_validate_station_bundle_accepts_ikebukuro_demo_data():
    issues = validate_station_bundle(load_station_bundle("ikebukuro"))

    assert issues == []


def test_validate_station_bundle_reports_missing_edge_node():
    bundle = load_station_bundle("ikebukuro").model_copy(deep=True)
    bundle.edges[0].to_node_id = "missing_node"

    issues = validate_station_bundle(bundle)

    assert any(issue.code == "edge.to_node_id" and "missing_node" in issue.message for issue in issues)


def test_validate_data_cli_returns_zero_for_valid_station():
    result = subprocess.run(
        [sys.executable, "-m", "app.validate_data", "ikebukuro"],
        cwd=BACKEND_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "ikebukuro" in result.stdout
    assert "0 issues" in result.stdout
