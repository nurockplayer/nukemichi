from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.data_store import load_station_bundle
from app.seed_pipeline import StationSeedDraft, dry_run_seed_draft


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _valid_seed_payload() -> dict:
    return {
        "station_id": "ikebukuro",
        "summary": "Add a hand-surveyed east-side locker candidate.",
        "nodes": [
            {
                "node_id": "survey_east_locker_anchor",
                "station_id": "ikebukuro",
                "floor_id": "B1",
                "type": "poi_anchor",
                "name": "Survey East Locker Anchor",
                "name_ja": "調査用東側ロッカーアンカー",
                "name_zh": "調查用東側置物櫃錨點",
                "x": 332,
                "y": 92,
                "connected_zone_ids": ["east_exit_underground_area"],
            }
        ],
        "edges": [
            {
                "edge_id": "edge_east_passage_to_survey_locker",
                "station_id": "ikebukuro",
                "from_node_id": "east_underground_passage",
                "to_node_id": "survey_east_locker_anchor",
                "distance_m": 18,
                "bidirectional": True,
                "floor_change": False,
                "from_floor_id": "B1",
                "to_floor_id": "B1",
                "accessibility": {
                    "stairs_only": False,
                    "elevator_available": False,
                    "escalator_available": False,
                    "barrier_free": True,
                },
            }
        ],
        "pois": [
            {
                "poi_id": "survey_east_locker",
                "station_id": "ikebukuro",
                "floor_id": "B1",
                "anchor_node_id": "survey_east_locker_anchor",
                "category": "locker",
                "name": "Survey East Locker",
                "name_ja": "調査用東側コインロッカー",
                "name_zh": "調查用東側投幣置物櫃",
                "description": "Draft POI from survey notes; not yet promoted to demo data.",
                "opening_hours": "Unknown",
                "tags": ["survey", "draft", "locker"],
            }
        ],
    }


def test_seed_dry_run_reports_planned_graph_and_poi_additions_without_mutating_bundle():
    bundle = load_station_bundle("ikebukuro")
    draft = StationSeedDraft.model_validate(_valid_seed_payload())

    result = dry_run_seed_draft(bundle, draft)

    assert result.valid is True
    assert result.issues == []
    assert result.additions.nodes == 1
    assert result.additions.edges == 1
    assert result.additions.pois == 1
    assert "survey_east_locker" not in {poi.poi_id for poi in bundle.pois}
    assert "survey_east_locker_anchor" not in {node.node_id for node in bundle.nodes}


def test_seed_dry_run_reports_reference_and_duplicate_errors():
    payload = _valid_seed_payload()
    payload["station_id"] = "shinjuku"
    payload["pois"][0]["poi_id"] = "east_exit"
    payload["pois"][0]["anchor_node_id"] = "missing_anchor"
    payload["edges"][0]["to_node_id"] = "missing_node"
    draft = StationSeedDraft.model_validate(payload)

    result = dry_run_seed_draft(load_station_bundle("ikebukuro"), draft)

    assert result.valid is False
    issue_codes = {issue.code for issue in result.issues}
    assert "seed.station_id" in issue_codes
    assert "seed.poi_id.duplicate_existing" in issue_codes
    assert "seed.poi.anchor_node_id" in issue_codes
    assert "seed.edge.to_node_id" in issue_codes


def test_seed_pipeline_cli_dry_run_returns_zero_for_valid_seed(tmp_path: Path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_valid_seed_payload()), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "app.seed_pipeline", "ikebukuro", str(seed_path), "--dry-run"],
        cwd=BACKEND_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Dry run for ikebukuro" in result.stdout
    assert "nodes: 1" in result.stdout
    assert "pois: 1" in result.stdout


def test_seed_pipeline_cli_dry_run_returns_one_for_invalid_seed(tmp_path: Path):
    payload = _valid_seed_payload()
    payload["pois"][0]["anchor_node_id"] = "missing_anchor"
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "app.seed_pipeline", "ikebukuro", str(seed_path), "--dry-run"],
        cwd=BACKEND_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "seed.poi.anchor_node_id" in result.stdout
