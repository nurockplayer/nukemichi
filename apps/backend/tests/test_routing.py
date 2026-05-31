from app.data_store import load_station_bundle
from app.routing import calculate_route
from app.schemas import RoutePreferences


def test_routes_from_jr_east_gate_to_sunshine_city_exit():
    bundle = load_station_bundle("ikebukuro")

    route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="sunshine_city_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    assert route.path
    assert route.distance_m > 0
    assert route.instructions
    assert route.destination_poi_id == "sunshine_city_exit"


def test_routes_from_zone_using_first_nearby_node():
    bundle = load_station_bundle("ikebukuro")
    zone = next(item for item in bundle.zones if item.zone_id == "jr_east_gate_area")

    route = calculate_route(
        bundle,
        from_zone_id=zone.zone_id,
        to_poi_id="sunshine_city_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    assert route.path
    assert route.start_node_id == zone.nearby_node_ids[0]
    assert route.destination_poi_id == "sunshine_city_exit"


def test_avoid_stairs_uses_elevator_when_barrier_free_alternative_exists():
    bundle = load_station_bundle("ikebukuro")

    route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="east_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    path_node_ids = [node.node_id for node in route.path]
    assert "stairs_b1_to_1f_east" not in path_node_ids
    assert "elevator_b1_to_1f_east" in path_node_ids
    assert route.requires_stairs is False


def test_floor_change_instruction_localizes_method_names():
    bundle = load_station_bundle("ikebukuro")

    zh_route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="east_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="zh-TW"),
    )
    ja_route = calculate_route(
        bundle,
        from_node_id="jr_east_gate",
        to_poi_id="east_exit",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="ja"),
    )

    assert any("電梯" in instruction.text for instruction in zh_route.instructions)
    assert all("elevator" not in instruction.text for instruction in zh_route.instructions)
    assert any("エレベーター" in instruction.text for instruction in ja_route.instructions)
    assert all("elevator" not in instruction.text for instruction in ja_route.instructions)


def test_route_to_current_anchor_returns_zero_distance_and_non_empty_floor():
    bundle = load_station_bundle("ikebukuro")

    route = calculate_route(
        bundle,
        from_node_id="jr_east_restroom_anchor",
        to_poi_id="restroom_jr_east",
        preferences=RoutePreferences(avoid_stairs=True, prefer_elevator=False, language="en"),
    )

    assert route.distance_m == 0
    assert route.estimated_minutes == 0
    assert route.path[0].node_id == "jr_east_restroom_anchor"
    assert route.instructions[0].floor_id == "B1"
    assert "already" in route.instructions[0].text.lower()
