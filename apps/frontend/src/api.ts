import type {
  LocalizationResult,
  Preferences,
  RouteResult,
  Station,
  StationMap,
  WifiObservation,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getStations() {
  return request<Station[]>("/stations");
}

export function getStationMap(stationId: string) {
  return request<StationMap>(`/stations/${stationId}/map`);
}

export function localizeWifi(stationId: string, observedAps: WifiObservation[]) {
  return request<LocalizationResult>("/localize/wifi", {
    method: "POST",
    body: JSON.stringify({
      station_id: stationId,
      observed_aps: observedAps,
    }),
  });
}

export function getRoute(params: {
  stationId: string;
  fromNodeId?: string | null;
  fromZoneId?: string | null;
  toPoiId: string;
  preferences: Preferences;
}) {
  return request<RouteResult>("/route", {
    method: "POST",
    body: JSON.stringify({
      station_id: params.stationId,
      from_node_id: params.fromNodeId || undefined,
      from_zone_id: params.fromZoneId || undefined,
      to_poi_id: params.toPoiId,
      preferences: params.preferences,
    }),
  });
}
