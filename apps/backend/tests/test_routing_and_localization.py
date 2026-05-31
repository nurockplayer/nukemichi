from app.data_store import load_station_bundle
from app.localization import estimate_wifi_zone
from app.routing import calculate_route
from app.schemas import RoutePreferences, WifiAccessPointObservation


def test_dijkstra_routes_from_jr_east_gate_to_sunshine_city_exit():
    bundle = load_station_bundle("ikebukuro")

    route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="sunshine_city_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    assert route.path
    assert route.distance_m > 0
    assert route.start_node_id == "jr_east_gate"
    assert route.destination_poi_id == "sunshine_city_exit"


def test_avoid_stairs_does_not_choose_stairs_only_edge_when_alternative_exists():
    bundle = load_station_bundle("ikebukuro")

    route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="east_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    assert route.path
    path_node_ids = [node.node_id for node in route.path]
    assert "stairs_b1_to_1f_east" not in path_node_ids
    assert route.requires_stairs is False


def test_wifi_localization_estimates_jr_east_gate_area():
    bundle = load_station_bundle("ikebukuro")

    result = estimate_wifi_zone(
        bundle,
        [
            WifiAccessPointObservation(bssid="ap_jr_east_01", rssi=-53),
            WifiAccessPointObservation(bssid="ap_station_core_01", rssi=-69),
            WifiAccessPointObservation(bssid="ap_jr_east_02", rssi=-60),
        ],
    )

    assert result.estimated_zone_id == "jr_east_gate_area"
    assert result.confidence > 0
