from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


NodeType = Literal[
    "gate",
    "exit",
    "passage",
    "stairs",
    "escalator",
    "elevator",
    "landmark",
    "poi_anchor",
    "connector",
]
PoiCategory = Literal[
    "restroom",
    "convenience",
    "coffee",
    "locker",
    "exit",
    "gate",
    "landmark",
    "tourist_info",
]


class Station(BaseModel):
    station_id: str
    name: str
    name_ja: str
    name_zh: str
    description: str


class Floor(BaseModel):
    floor_id: str
    station_id: str
    label: str
    level: int
    display_order: int


class Node(BaseModel):
    node_id: str
    station_id: str
    floor_id: str
    type: NodeType
    name: str
    name_ja: str
    name_zh: str
    x: float
    y: float
    connected_zone_ids: list[str] = Field(default_factory=list)


class EdgeAccessibility(BaseModel):
    stairs_only: bool = False
    elevator_available: bool = False
    escalator_available: bool = False
    barrier_free: bool = True


class Edge(BaseModel):
    edge_id: str
    station_id: str
    from_node_id: str
    to_node_id: str
    distance_m: float
    bidirectional: bool = True
    floor_change: bool = False
    from_floor_id: str
    to_floor_id: str
    accessibility: EdgeAccessibility


class Poi(BaseModel):
    poi_id: str
    station_id: str
    floor_id: str
    anchor_node_id: str
    category: PoiCategory
    name: str
    name_ja: str
    name_zh: str
    description: str
    opening_hours: str
    tags: list[str] = Field(default_factory=list)


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class LocationZone(BaseModel):
    zone_id: str
    station_id: str
    floor_id: str
    name: str
    name_ja: str
    name_zh: str
    nearby_node_ids: list[str]
    nearby_gate_ids: list[str] = Field(default_factory=list)
    nearby_exit_ids: list[str] = Field(default_factory=list)
    description: str
    confidence_label: str
    bbox: BoundingBox


class WifiAccessPointReading(BaseModel):
    bssid: str
    ssid: str
    rssi: int


class WifiFingerprint(BaseModel):
    fingerprint_id: str
    station_id: str
    zone_id: str
    floor_id: str
    observed_aps: list[WifiAccessPointReading]
    collected_at: str
    device_type: str


class Beacon(BaseModel):
    beacon_id: str
    station_id: str
    zone_id: str
    uuid: str
    major: int
    minor: int
    floor_id: str
    x: float
    y: float
    description: str


class BeaconObservation(BaseModel):
    beacon_id: str
    rssi: int
    proximity: str
    observed_at: str


class BeaconZoneMapping(BaseModel):
    beacon_id: str
    zone_id: str
    weight: float


class StationBundle(BaseModel):
    station: Station
    floors: list[Floor]
    nodes: list[Node]
    edges: list[Edge]
    pois: list[Poi]
    zones: list[LocationZone]
    wifi_fingerprints: list[WifiFingerprint]
    beacons: list[Beacon] = Field(default_factory=list)
    beacon_observations: list[BeaconObservation] = Field(default_factory=list)
    beacon_zone_mappings: list[BeaconZoneMapping] = Field(default_factory=list)


class StationMapResponse(BaseModel):
    station: Station
    floors: list[Floor]
    nodes: list[Node]
    edges: list[Edge]
    pois: list[Poi]
    zones: list[LocationZone]


class WifiAccessPointObservation(BaseModel):
    bssid: str
    rssi: int


class WifiLocalizationRequest(BaseModel):
    station_id: str
    observed_aps: list[WifiAccessPointObservation]


class WifiLocalizationResponse(BaseModel):
    station_id: str
    estimated_zone_id: str | None
    estimated_zone_name: str | None
    confidence: float
    nearest_start_node_ids: list[str]
    message: str


class RoutePreferences(BaseModel):
    avoid_stairs: bool = True
    prefer_elevator: bool = False
    language: Literal["en", "ja", "zh-TW"] = "en"


class RouteRequest(BaseModel):
    station_id: str
    from_node_id: str | None = None
    from_zone_id: str | None = None
    to_poi_id: str
    preferences: RoutePreferences = Field(default_factory=RoutePreferences)


class RoutePathNode(BaseModel):
    node_id: str
    floor_id: str
    name: str
    x: float
    y: float


class RouteInstruction(BaseModel):
    type: Literal["walk", "floor_change", "arrive"]
    text: str
    floor_id: str
    distance_m: float | None = None
    to_floor_id: str | None = None


class RouteResponse(BaseModel):
    station_id: str
    distance_m: float
    estimated_minutes: int
    start_node_id: str
    destination_poi_id: str
    floors: list[str]
    requires_stairs: bool
    uses_elevator: bool
    path: list[RoutePathNode]
    instructions: list[RouteInstruction]
