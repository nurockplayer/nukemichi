from app.data_store import load_station_bundle
from app.routing import calculate_route
from app.schemas import RoutePreferences


def test_demo_data_references_existing_entities():
    bundle = load_station_bundle("ikebukuro")
    floor_ids = {floor.floor_id for floor in bundle.floors}
    node_ids = {node.node_id for node in bundle.nodes}
    zone_ids = {zone.zone_id for zone in bundle.zones}

    for node in bundle.nodes:
        assert node.floor_id in floor_ids
        assert set(node.connected_zone_ids).issubset(zone_ids)

    for edge in bundle.edges:
        assert edge.from_node_id in node_ids
        assert edge.to_node_id in node_ids
        assert edge.from_floor_id in floor_ids
        assert edge.to_floor_id in floor_ids

    for poi in bundle.pois:
        assert poi.anchor_node_id in node_ids
        assert poi.floor_id in floor_ids

    for zone in bundle.zones:
        assert zone.floor_id in floor_ids
        assert set(zone.nearby_node_ids).issubset(node_ids)
        assert set(zone.nearby_gate_ids).issubset(node_ids)
        assert set(zone.nearby_exit_ids).issubset(node_ids)

    for fingerprint in bundle.wifi_fingerprints:
        assert fingerprint.zone_id in zone_ids
        assert fingerprint.floor_id in floor_ids

    for beacon in bundle.beacons:
        assert beacon.zone_id in zone_ids
        assert beacon.floor_id in floor_ids

    for mapping in bundle.beacon_zone_mappings:
        assert mapping.zone_id in zone_ids
        assert any(beacon.beacon_id == mapping.beacon_id for beacon in bundle.beacons)


def test_main_pois_are_reachable_from_primary_gates():
    bundle = load_station_bundle("ikebukuro")
    primary_gate_ids = [
        "jr_east_gate",
        "jr_central_gate",
        "tobu_central_gate",
        "seibu_ikebukuro_gate",
        "marunouchi_line_gate",
    ]

    for gate_id in primary_gate_ids:
        for poi in bundle.pois:
            route = calculate_route(
                bundle,
                from_node_id=gate_id,
                to_poi_id=poi.poi_id,
                preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
            )
            assert route.path, f"{poi.poi_id} should be reachable from {gate_id}"
