from __future__ import annotations

from dataclasses import dataclass

from app.schemas import StationBundle


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def validate_station_bundle(bundle: StationBundle) -> list[ValidationIssue]:
    floor_ids = {floor.floor_id for floor in bundle.floors}
    node_ids = {node.node_id for node in bundle.nodes}
    poi_ids = {poi.poi_id for poi in bundle.pois}
    zone_ids = {zone.zone_id for zone in bundle.zones}
    beacon_ids = {beacon.beacon_id for beacon in bundle.beacons}

    issues: list[ValidationIssue] = []

    for node in bundle.nodes:
        _require_member(issues, "node.floor_id", node.node_id, node.floor_id, floor_ids)
        _require_all_members(issues, "node.connected_zone_ids", node.node_id, node.connected_zone_ids, zone_ids)

    for edge in bundle.edges:
        _require_member(issues, "edge.from_node_id", edge.edge_id, edge.from_node_id, node_ids)
        _require_member(issues, "edge.to_node_id", edge.edge_id, edge.to_node_id, node_ids)
        _require_member(issues, "edge.from_floor_id", edge.edge_id, edge.from_floor_id, floor_ids)
        _require_member(issues, "edge.to_floor_id", edge.edge_id, edge.to_floor_id, floor_ids)

    for poi in bundle.pois:
        _require_member(issues, "poi.floor_id", poi.poi_id, poi.floor_id, floor_ids)
        _require_member(issues, "poi.anchor_node_id", poi.poi_id, poi.anchor_node_id, node_ids)

    for zone in bundle.zones:
        _require_member(issues, "zone.floor_id", zone.zone_id, zone.floor_id, floor_ids)
        _require_all_members(issues, "zone.nearby_node_ids", zone.zone_id, zone.nearby_node_ids, node_ids)
        _require_all_members(issues, "zone.nearby_gate_ids", zone.zone_id, zone.nearby_gate_ids, node_ids)
        _require_all_members(issues, "zone.nearby_exit_ids", zone.zone_id, zone.nearby_exit_ids, node_ids)

    for fingerprint in bundle.wifi_fingerprints:
        _require_member(issues, "wifi_fingerprint.floor_id", fingerprint.fingerprint_id, fingerprint.floor_id, floor_ids)
        _require_member(issues, "wifi_fingerprint.zone_id", fingerprint.fingerprint_id, fingerprint.zone_id, zone_ids)

    for note in bundle.survey_notes:
        _require_member(issues, "survey_note.floor_id", note.note_id, note.floor_id, floor_ids)
        _require_all_members(issues, "survey_note.related_node_ids", note.note_id, note.related_node_ids, node_ids)
        _require_all_members(issues, "survey_note.related_zone_ids", note.note_id, note.related_zone_ids, zone_ids)

    for point in bundle.fingerprint_collection_points:
        _require_member(issues, "fingerprint_collection_point.floor_id", point.collection_point_id, point.floor_id, floor_ids)
        _require_member(issues, "fingerprint_collection_point.zone_id", point.collection_point_id, point.zone_id, zone_ids)
        if point.suggested_node_id:
            _require_member(
                issues,
                "fingerprint_collection_point.suggested_node_id",
                point.collection_point_id,
                point.suggested_node_id,
                node_ids,
            )

    for beacon in bundle.beacons:
        _require_member(issues, "beacon.floor_id", beacon.beacon_id, beacon.floor_id, floor_ids)
        _require_member(issues, "beacon.zone_id", beacon.beacon_id, beacon.zone_id, zone_ids)

    for observation in bundle.beacon_observations:
        _require_member(issues, "beacon_observation.beacon_id", observation.beacon_id, observation.beacon_id, beacon_ids)

    for mapping in bundle.beacon_zone_mappings:
        _require_member(issues, "beacon_zone_mapping.beacon_id", mapping.beacon_id, mapping.beacon_id, beacon_ids)
        _require_member(issues, "beacon_zone_mapping.zone_id", mapping.beacon_id, mapping.zone_id, zone_ids)

    for poi_id in poi_ids:
        poi = next(poi for poi in bundle.pois if poi.poi_id == poi_id)
        if poi.anchor_node_id not in node_ids:
            issues.append(ValidationIssue("poi.reachable", f"{poi_id} cannot be checked because its anchor is missing."))

    return issues


def _require_member(
    issues: list[ValidationIssue],
    code: str,
    owner_id: str,
    value: str,
    allowed_values: set[str],
) -> None:
    if value not in allowed_values:
        issues.append(ValidationIssue(code, f"{owner_id} references missing value '{value}'."))


def _require_all_members(
    issues: list[ValidationIssue],
    code: str,
    owner_id: str,
    values: list[str],
    allowed_values: set[str],
) -> None:
    for value in values:
        _require_member(issues, code, owner_id, value, allowed_values)
