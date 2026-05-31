from __future__ import annotations

import heapq
from collections import defaultdict

from fastapi import HTTPException

from app.schemas import (
    Edge,
    Node,
    RouteInstruction,
    RoutePathNode,
    RoutePreferences,
    RouteResponse,
    StationBundle,
)


STAIRS_PENALTY = 10_000
ELEVATOR_DISCOUNT = 0.85
WALKING_METERS_PER_MINUTE = 70


def calculate_route(
    bundle: StationBundle,
    to_poi_id: str,
    preferences: RoutePreferences,
    from_node_id: str | None = None,
    from_zone_id: str | None = None,
) -> RouteResponse:
    nodes_by_id = {node.node_id: node for node in bundle.nodes}
    pois_by_id = {poi.poi_id: poi for poi in bundle.pois}
    zones_by_id = {zone.zone_id: zone for zone in bundle.zones}

    if to_poi_id not in pois_by_id:
        raise HTTPException(status_code=404, detail=f"POI '{to_poi_id}' was not found.")

    if from_zone_id:
        zone = zones_by_id.get(from_zone_id)
        if not zone or not zone.nearby_node_ids:
            raise HTTPException(status_code=404, detail=f"Zone '{from_zone_id}' was not found.")
        start_node_id = zone.nearby_node_ids[0]
    elif from_node_id:
        start_node_id = from_node_id
    else:
        raise HTTPException(status_code=400, detail="Provide either from_node_id or from_zone_id.")

    if start_node_id not in nodes_by_id:
        raise HTTPException(status_code=404, detail=f"Start node '{start_node_id}' was not found.")

    destination = pois_by_id[to_poi_id]
    end_node_id = destination.anchor_node_id
    if end_node_id not in nodes_by_id:
        raise HTTPException(status_code=404, detail=f"Destination anchor '{end_node_id}' was not found.")

    distance_by_node, previous = _dijkstra(bundle.edges, start_node_id, preferences)
    if end_node_id not in distance_by_node:
        raise HTTPException(status_code=404, detail="No route found for the selected destination.")

    path_edges = _reconstruct_edges(previous, start_node_id, end_node_id)
    path_node_ids = [start_node_id] + [edge.to_node_id for edge in path_edges]
    path_nodes = [nodes_by_id[node_id] for node_id in path_node_ids]
    real_distance = sum(edge.distance_m for edge in path_edges)
    floors = sorted({node.floor_id for node in path_nodes}, key=lambda floor_id: _floor_order(bundle, floor_id))
    requires_stairs = any(edge.accessibility.stairs_only for edge in path_edges)
    uses_elevator = any(edge.accessibility.elevator_available and edge.floor_change for edge in path_edges)

    return RouteResponse(
        station_id=bundle.station.station_id,
        distance_m=round(real_distance),
        estimated_minutes=0 if real_distance == 0 else max(1, round(real_distance / WALKING_METERS_PER_MINUTE)),
        start_node_id=start_node_id,
        destination_poi_id=to_poi_id,
        floors=floors,
        requires_stairs=requires_stairs,
        uses_elevator=uses_elevator,
        path=[
            RoutePathNode(
                node_id=node.node_id,
                floor_id=node.floor_id,
                name=node.name,
                x=node.x,
                y=node.y,
            )
            for node in path_nodes
        ],
        instructions=_build_instructions(
            path_edges,
            nodes_by_id,
            destination.name,
            preferences.language,
            start_node_id,
            end_node_id,
        ),
    )


def _dijkstra(
    edges: list[Edge],
    start_node_id: str,
    preferences: RoutePreferences,
) -> tuple[dict[str, float], dict[str, tuple[str, Edge]]]:
    adjacency: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges:
        adjacency[edge.from_node_id].append(edge)
        if edge.bidirectional:
            adjacency[edge.to_node_id].append(edge.model_copy(update={
                "from_node_id": edge.to_node_id,
                "to_node_id": edge.from_node_id,
                "from_floor_id": edge.to_floor_id,
                "to_floor_id": edge.from_floor_id,
            }))

    distances: dict[str, float] = {start_node_id: 0}
    previous: dict[str, tuple[str, Edge]] = {}
    queue: list[tuple[float, str]] = [(0, start_node_id)]

    while queue:
        current_distance, current_node_id = heapq.heappop(queue)
        if current_distance > distances.get(current_node_id, float("inf")):
            continue

        for edge in adjacency[current_node_id]:
            weight = _edge_weight(edge, preferences)
            candidate = current_distance + weight
            if candidate < distances.get(edge.to_node_id, float("inf")):
                distances[edge.to_node_id] = candidate
                previous[edge.to_node_id] = (current_node_id, edge)
                heapq.heappush(queue, (candidate, edge.to_node_id))

    return distances, previous


def _edge_weight(edge: Edge, preferences: RoutePreferences) -> float:
    weight = edge.distance_m
    if preferences.avoid_stairs and edge.accessibility.stairs_only:
        weight += STAIRS_PENALTY
    if preferences.prefer_elevator and edge.accessibility.elevator_available:
        weight *= ELEVATOR_DISCOUNT
    return weight


def _reconstruct_edges(
    previous: dict[str, tuple[str, Edge]],
    start_node_id: str,
    end_node_id: str,
) -> list[Edge]:
    edges: list[Edge] = []
    current = end_node_id
    while current != start_node_id:
        previous_node_id, edge = previous[current]
        edges.append(edge)
        current = previous_node_id
    edges.reverse()
    return edges


def _build_instructions(
    edges: list[Edge],
    nodes_by_id: dict[str, Node],
    destination_name: str,
    language: str,
    start_node_id: str,
    end_node_id: str,
) -> list[RouteInstruction]:
    if not edges:
        start_floor_id = nodes_by_id[start_node_id].floor_id
        return [
            RouteInstruction(
                type="arrive",
                text=_already_near_text(language, destination_name),
                floor_id=start_floor_id,
            )
        ]

    instructions: list[RouteInstruction] = []
    for edge in edges:
        from_node = nodes_by_id[edge.from_node_id]
        to_node = nodes_by_id[edge.to_node_id]
        if edge.floor_change:
            method = "elevator" if edge.accessibility.elevator_available else "escalator" if edge.accessibility.escalator_available else "stairs"
            text = _floor_change_text(language, method, edge.to_floor_id)
            instructions.append(RouteInstruction(
                type="floor_change",
                text=text,
                floor_id=edge.from_floor_id,
                to_floor_id=edge.to_floor_id,
            ))
        else:
            instructions.append(RouteInstruction(
                type="walk",
                text=_walk_text(language, round(edge.distance_m), to_node.name),
                floor_id=from_node.floor_id,
                distance_m=round(edge.distance_m),
            ))

    instructions.append(RouteInstruction(
        type="arrive",
        text=_arrive_text(language, destination_name),
        floor_id=nodes_by_id[end_node_id].floor_id,
    ))
    return instructions


def _walk_text(language: str, distance_m: int, target_name: str) -> str:
    if language == "ja":
        return f"{target_name}方面へ約{distance_m}m進みます。"
    if language == "zh-TW":
        return f"往 {target_name} 方向步行約 {distance_m} 公尺。"
    return f"Walk about {distance_m}m toward {target_name}."


def _floor_change_text(language: str, method: str, to_floor_id: str) -> str:
    if language == "ja":
        return f"{_localized_method_name(method, language)}で{to_floor_id}へ移動します。"
    if language == "zh-TW":
        return f"搭乘{_localized_method_name(method, language)}前往 {to_floor_id}。"
    return f"Take the {method} to {to_floor_id}."


def _arrive_text(language: str, destination_name: str) -> str:
    if language == "ja":
        return f"{destination_name}に到着です。"
    if language == "zh-TW":
        return f"抵達 {destination_name}。"
    return f"Arrive at {destination_name}."


def _already_near_text(language: str, destination_name: str) -> str:
    if language == "ja":
        return f"すでに{destination_name}付近にいます。"
    if language == "zh-TW":
        return f"你已經在 {destination_name} 附近。"
    return f"You are already near {destination_name}."


def _localized_method_name(method: str, language: str) -> str:
    localized = {
        "zh-TW": {
            "elevator": "電梯",
            "escalator": "手扶梯",
            "stairs": "樓梯",
        },
        "ja": {
            "elevator": "エレベーター",
            "escalator": "エスカレーター",
            "stairs": "階段",
        },
    }
    return localized.get(language, {}).get(method, method)


def _floor_order(bundle: StationBundle, floor_id: str) -> int:
    floor = next((item for item in bundle.floors if item.floor_id == floor_id), None)
    return floor.display_order if floor else 99
