from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, Field, ValidationError

from app.data_store import load_station_bundle
from app.data_validation import validate_station_bundle
from app.schemas import (
    Edge,
    FingerprintCollectionPoint,
    LocationZone,
    Node,
    Poi,
    StationBundle,
    StationSurveyNote,
)


@dataclass(frozen=True)
class SeedValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class SeedAdditions:
    nodes: int = 0
    edges: int = 0
    pois: int = 0
    zones: int = 0
    survey_notes: int = 0
    fingerprint_collection_points: int = 0


@dataclass(frozen=True)
class SeedDryRunResult:
    station_id: str
    summary: str
    additions: SeedAdditions
    planned_ids: dict[str, list[str]]
    issues: list[SeedValidationIssue]

    @property
    def valid(self) -> bool:
        return not self.issues


class SeedPromotionError(ValueError):
    def __init__(self, issues: list[SeedValidationIssue]) -> None:
        self.issues = issues
        super().__init__("Seed draft is not valid for promotion.")


class StationSeedDraft(BaseModel):
    station_id: str
    summary: str = ""
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    pois: list[Poi] = Field(default_factory=list)
    zones: list[LocationZone] = Field(default_factory=list)
    survey_notes: list[StationSurveyNote] = Field(default_factory=list)
    fingerprint_collection_points: list[FingerprintCollectionPoint] = Field(default_factory=list)


def load_seed_draft(path: Path) -> StationSeedDraft:
    with path.open("r", encoding="utf-8") as file:
        return StationSeedDraft.model_validate(json.load(file))


def dry_run_seed_draft(bundle: StationBundle, draft: StationSeedDraft) -> SeedDryRunResult:
    issues = validate_seed_draft(bundle, draft)
    return SeedDryRunResult(
        station_id=draft.station_id,
        summary=draft.summary,
        additions=SeedAdditions(
            nodes=len(draft.nodes),
            edges=len(draft.edges),
            pois=len(draft.pois),
            zones=len(draft.zones),
            survey_notes=len(draft.survey_notes),
            fingerprint_collection_points=len(draft.fingerprint_collection_points),
        ),
        planned_ids={
            "nodes": [item.node_id for item in draft.nodes],
            "edges": [item.edge_id for item in draft.edges],
            "pois": [item.poi_id for item in draft.pois],
            "zones": [item.zone_id for item in draft.zones],
            "survey_notes": [item.note_id for item in draft.survey_notes],
            "fingerprint_collection_points": [
                item.collection_point_id for item in draft.fingerprint_collection_points
            ],
        },
        issues=issues,
    )


def promote_seed_draft(bundle: StationBundle, draft: StationSeedDraft) -> StationBundle:
    issues = validate_seed_draft(bundle, draft)
    if issues:
        raise SeedPromotionError(issues)

    promoted = bundle.model_copy(
        update={
            "nodes": [*bundle.nodes, *draft.nodes],
            "edges": [*bundle.edges, *draft.edges],
            "pois": [*bundle.pois, *draft.pois],
            "zones": [*bundle.zones, *draft.zones],
            "survey_notes": [*bundle.survey_notes, *draft.survey_notes],
            "fingerprint_collection_points": [
                *bundle.fingerprint_collection_points,
                *draft.fingerprint_collection_points,
            ],
        }
    )
    bundle_issues = validate_station_bundle(promoted)
    if bundle_issues:
        raise SeedPromotionError([
            SeedValidationIssue(f"promoted_station.{issue.code}", issue.message)
            for issue in bundle_issues
        ])
    return promoted


def write_station_bundle(bundle: StationBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_seed_draft(bundle: StationBundle, draft: StationSeedDraft) -> list[SeedValidationIssue]:
    floor_ids = {floor.floor_id for floor in bundle.floors}
    existing_node_ids = {node.node_id for node in bundle.nodes}
    existing_edge_ids = {edge.edge_id for edge in bundle.edges}
    existing_poi_ids = {poi.poi_id for poi in bundle.pois}
    existing_zone_ids = {zone.zone_id for zone in bundle.zones}
    existing_note_ids = {note.note_id for note in bundle.survey_notes}
    existing_collection_point_ids = {
        point.collection_point_id for point in bundle.fingerprint_collection_points
    }

    draft_node_ids = [node.node_id for node in draft.nodes]
    draft_edge_ids = [edge.edge_id for edge in draft.edges]
    draft_poi_ids = [poi.poi_id for poi in draft.pois]
    draft_zone_ids = [zone.zone_id for zone in draft.zones]
    draft_note_ids = [note.note_id for note in draft.survey_notes]
    draft_collection_point_ids = [
        point.collection_point_id for point in draft.fingerprint_collection_points
    ]

    all_node_ids = existing_node_ids | set(draft_node_ids)
    all_zone_ids = existing_zone_ids | set(draft_zone_ids)

    issues: list[SeedValidationIssue] = []
    if draft.station_id != bundle.station.station_id:
        issues.append(
            SeedValidationIssue(
                "seed.station_id",
                f"Draft station_id '{draft.station_id}' does not match target station '{bundle.station.station_id}'.",
            )
        )

    _require_unique_ids(issues, "seed.node_id", draft_node_ids)
    _require_unique_ids(issues, "seed.edge_id", draft_edge_ids)
    _require_unique_ids(issues, "seed.poi_id", draft_poi_ids)
    _require_unique_ids(issues, "seed.zone_id", draft_zone_ids)
    _require_unique_ids(issues, "seed.survey_note_id", draft_note_ids)
    _require_unique_ids(issues, "seed.fingerprint_collection_point_id", draft_collection_point_ids)

    _reject_existing_ids(issues, "seed.node_id.duplicate_existing", draft_node_ids, existing_node_ids)
    _reject_existing_ids(issues, "seed.edge_id.duplicate_existing", draft_edge_ids, existing_edge_ids)
    _reject_existing_ids(issues, "seed.poi_id.duplicate_existing", draft_poi_ids, existing_poi_ids)
    _reject_existing_ids(issues, "seed.zone_id.duplicate_existing", draft_zone_ids, existing_zone_ids)
    _reject_existing_ids(
        issues,
        "seed.survey_note_id.duplicate_existing",
        draft_note_ids,
        existing_note_ids,
    )
    _reject_existing_ids(
        issues,
        "seed.fingerprint_collection_point_id.duplicate_existing",
        draft_collection_point_ids,
        existing_collection_point_ids,
    )

    for node in draft.nodes:
        _require_station_id(issues, "seed.node.station_id", node.node_id, node.station_id, draft.station_id)
        _require_member(issues, "seed.node.floor_id", node.node_id, node.floor_id, floor_ids)
        _require_all_members(
            issues,
            "seed.node.connected_zone_ids",
            node.node_id,
            node.connected_zone_ids,
            all_zone_ids,
        )

    for edge in draft.edges:
        _require_station_id(issues, "seed.edge.station_id", edge.edge_id, edge.station_id, draft.station_id)
        _require_member(issues, "seed.edge.from_node_id", edge.edge_id, edge.from_node_id, all_node_ids)
        _require_member(issues, "seed.edge.to_node_id", edge.edge_id, edge.to_node_id, all_node_ids)
        _require_member(issues, "seed.edge.from_floor_id", edge.edge_id, edge.from_floor_id, floor_ids)
        _require_member(issues, "seed.edge.to_floor_id", edge.edge_id, edge.to_floor_id, floor_ids)

    for poi in draft.pois:
        _require_station_id(issues, "seed.poi.station_id", poi.poi_id, poi.station_id, draft.station_id)
        _require_member(issues, "seed.poi.floor_id", poi.poi_id, poi.floor_id, floor_ids)
        _require_member(issues, "seed.poi.anchor_node_id", poi.poi_id, poi.anchor_node_id, all_node_ids)

    for zone in draft.zones:
        _require_station_id(issues, "seed.zone.station_id", zone.zone_id, zone.station_id, draft.station_id)
        _require_member(issues, "seed.zone.floor_id", zone.zone_id, zone.floor_id, floor_ids)
        _require_all_members(issues, "seed.zone.nearby_node_ids", zone.zone_id, zone.nearby_node_ids, all_node_ids)
        _require_all_members(issues, "seed.zone.nearby_gate_ids", zone.zone_id, zone.nearby_gate_ids, all_node_ids)
        _require_all_members(issues, "seed.zone.nearby_exit_ids", zone.zone_id, zone.nearby_exit_ids, all_node_ids)

    for note in draft.survey_notes:
        _require_station_id(issues, "seed.survey_note.station_id", note.note_id, note.station_id, draft.station_id)
        _require_member(issues, "seed.survey_note.floor_id", note.note_id, note.floor_id, floor_ids)
        _require_all_members(
            issues,
            "seed.survey_note.related_node_ids",
            note.note_id,
            note.related_node_ids,
            all_node_ids,
        )
        _require_all_members(
            issues,
            "seed.survey_note.related_zone_ids",
            note.note_id,
            note.related_zone_ids,
            all_zone_ids,
        )

    for point in draft.fingerprint_collection_points:
        _require_station_id(
            issues,
            "seed.fingerprint_collection_point.station_id",
            point.collection_point_id,
            point.station_id,
            draft.station_id,
        )
        _require_member(
            issues,
            "seed.fingerprint_collection_point.floor_id",
            point.collection_point_id,
            point.floor_id,
            floor_ids,
        )
        _require_member(
            issues,
            "seed.fingerprint_collection_point.zone_id",
            point.collection_point_id,
            point.zone_id,
            all_zone_ids,
        )
        if point.suggested_node_id:
            _require_member(
                issues,
                "seed.fingerprint_collection_point.suggested_node_id",
                point.collection_point_id,
                point.suggested_node_id,
                all_node_ids,
            )

    return issues


def _require_unique_ids(issues: list[SeedValidationIssue], code: str, values: list[str]) -> None:
    counts = Counter(values)
    for value, count in counts.items():
        if count > 1:
            issues.append(SeedValidationIssue(code, f"Draft id '{value}' appears {count} times."))


def _reject_existing_ids(
    issues: list[SeedValidationIssue],
    code: str,
    values: list[str],
    existing_values: set[str],
) -> None:
    for value in values:
        if value in existing_values:
            issues.append(SeedValidationIssue(code, f"Draft id '{value}' already exists in station data."))


def _require_station_id(
    issues: list[SeedValidationIssue],
    code: str,
    owner_id: str,
    station_id: str,
    expected_station_id: str,
) -> None:
    if station_id != expected_station_id:
        issues.append(
            SeedValidationIssue(
                code,
                f"{owner_id} uses station_id '{station_id}' but draft station_id is '{expected_station_id}'.",
            )
        )


def _require_member(
    issues: list[SeedValidationIssue],
    code: str,
    owner_id: str,
    value: str,
    allowed_values: set[str],
) -> None:
    if value not in allowed_values:
        issues.append(SeedValidationIssue(code, f"{owner_id} references missing value '{value}'."))


def _require_all_members(
    issues: list[SeedValidationIssue],
    code: str,
    owner_id: str,
    values: list[str],
    allowed_values: set[str],
) -> None:
    for value in values:
        _require_member(issues, code, owner_id, value, allowed_values)


def _format_dry_run(result: SeedDryRunResult) -> str:
    lines = [
        f"Dry run for {result.station_id}",
        f"summary: {result.summary or '(none)'}",
        "planned additions:",
        _format_additions(result.additions),
    ]
    if result.issues:
        lines.append("issues:")
        lines.extend(f"  {issue.code}: {issue.message}" for issue in result.issues)
    else:
        lines.append("issues: none")
    return "\n".join(lines)


def _format_additions(additions: SeedAdditions) -> str:
    return "\n".join([
        f"  nodes: {additions.nodes}",
        f"  edges: {additions.edges}",
        f"  pois: {additions.pois}",
        f"  zones: {additions.zones}",
        f"  survey_notes: {additions.survey_notes}",
        f"  fingerprint_collection_points: {additions.fingerprint_collection_points}",
    ])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Nukemichi station seed drafts before promotion.")
    parser.add_argument("station_id", help="Target station id, for example ikebukuro.")
    parser.add_argument("seed_path", type=Path, help="Path to a seed draft JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and summarize without changing station data.")
    parser.add_argument("--output", type=Path, help="Write a promoted station bundle to this JSON path.")
    args = parser.parse_args(argv)

    if args.dry_run and args.output:
        parser.error("Use either --dry-run or --output, not both.")
    if not args.dry_run and not args.output:
        parser.error("Choose --dry-run or --output.")

    try:
        bundle = load_station_bundle(args.station_id)
        draft = load_seed_draft(args.seed_path)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        print(f"Seed draft could not be loaded: {error}")
        return 1

    result = dry_run_seed_draft(bundle, draft)
    if args.dry_run:
        print(_format_dry_run(result))
        return 0 if result.valid else 1

    if result.issues:
        print(_format_dry_run(result))
        return 1

    try:
        promoted = promote_seed_draft(bundle, draft)
    except SeedPromotionError as error:
        failed_result = SeedDryRunResult(
            station_id=result.station_id,
            summary=result.summary,
            additions=result.additions,
            planned_ids=result.planned_ids,
            issues=error.issues,
        )
        print(_format_dry_run(failed_result))
        return 1

    write_station_bundle(promoted, args.output)
    print(f"Promoted seed for {bundle.station.station_id} to {args.output}")
    print(_format_additions(result.additions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
