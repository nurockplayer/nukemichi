export type NodeType =
  | "gate"
  | "exit"
  | "passage"
  | "stairs"
  | "escalator"
  | "elevator"
  | "landmark"
  | "poi_anchor"
  | "connector";

export type PoiCategory =
  | "restroom"
  | "convenience"
  | "coffee"
  | "locker"
  | "exit"
  | "gate"
  | "landmark"
  | "tourist_info";

export interface Station {
  station_id: string;
  name: string;
  name_ja: string;
  name_zh: string;
  description: string;
}

export interface Floor {
  floor_id: string;
  station_id: string;
  label: string;
  level: number;
  display_order: number;
}

export interface Node {
  node_id: string;
  station_id: string;
  floor_id: string;
  type: NodeType;
  name: string;
  name_ja: string;
  name_zh: string;
  x: number;
  y: number;
  connected_zone_ids: string[];
}

export interface EdgeAccessibility {
  stairs_only: boolean;
  elevator_available: boolean;
  escalator_available: boolean;
  barrier_free: boolean;
}

export interface Edge {
  edge_id: string;
  station_id: string;
  from_node_id: string;
  to_node_id: string;
  distance_m: number;
  bidirectional: boolean;
  floor_change: boolean;
  from_floor_id: string;
  to_floor_id: string;
  accessibility: EdgeAccessibility;
}

export interface Poi {
  poi_id: string;
  station_id: string;
  floor_id: string;
  anchor_node_id: string;
  category: PoiCategory;
  name: string;
  name_ja: string;
  name_zh: string;
  description: string;
  opening_hours: string;
  tags: string[];
}

export interface LocationZone {
  zone_id: string;
  station_id: string;
  floor_id: string;
  name: string;
  name_ja: string;
  name_zh: string;
  nearby_node_ids: string[];
  nearby_gate_ids: string[];
  nearby_exit_ids: string[];
  description: string;
  confidence_label: string;
  bbox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface StationMap {
  station: Station;
  floors: Floor[];
  nodes: Node[];
  edges: Edge[];
  pois: Poi[];
  zones: LocationZone[];
}

export interface WifiObservation {
  bssid: string;
  rssi: number;
}

export interface LocalizationResult {
  station_id: string;
  estimated_zone_id: string | null;
  estimated_zone_name: string | null;
  confidence: number;
  nearest_start_node_ids: string[];
  message: string;
}

export interface Preferences {
  avoid_stairs: boolean;
  prefer_elevator: boolean;
  language: "en" | "ja" | "zh-TW";
}

export interface RoutePathNode {
  node_id: string;
  floor_id: string;
  name: string;
  x: number;
  y: number;
}

export interface RouteInstruction {
  type: "walk" | "floor_change" | "arrive";
  text: string;
  floor_id: string;
  distance_m?: number | null;
  to_floor_id?: string | null;
}

export interface RouteResult {
  station_id: string;
  distance_m: number;
  estimated_minutes: number;
  start_node_id: string;
  destination_poi_id: string;
  floors: string[];
  requires_stairs: boolean;
  uses_elevator: boolean;
  path: RoutePathNode[];
  instructions: RouteInstruction[];
}

export interface PoiFilters {
  q: string;
  category: PoiCategory | "all";
  floor_id: string | "all";
}
