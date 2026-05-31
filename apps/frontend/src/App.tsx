import { useEffect, useMemo, useState } from "react";
import {
  Accessibility,
  ArrowRight,
  Coffee,
  Landmark,
  LocateFixed,
  MapPin,
  Search,
  Store,
  Ticket,
} from "lucide-react";

import { getRoute, getStationMap, getStations, localizeWifi } from "./api";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { useNukemichiStore } from "./store";
import type { Edge, Node, Poi, PoiCategory, Station, WifiObservation } from "./types";

const categoryOptions: Array<PoiCategory | "all"> = [
  "all",
  "restroom",
  "coffee",
  "convenience",
  "locker",
  "exit",
  "gate",
  "landmark",
];

const wifiPresets: Array<{ label: string; observations: WifiObservation[] }> = [
  {
    label: "Simulate near JR East Gate",
    observations: [
      { bssid: "ap_jr_east_01", rssi: -53 },
      { bssid: "ap_station_core_01", rssi: -69 },
      { bssid: "ap_jr_east_02", rssi: -60 },
    ],
  },
  {
    label: "Simulate near Seibu Gate",
    observations: [
      { bssid: "ap_seibu_01", rssi: -52 },
      { bssid: "ap_seibu_coffee_01", rssi: -66 },
      { bssid: "ap_east_underground_01", rssi: -70 },
    ],
  },
  {
    label: "Simulate near West Exit",
    observations: [
      { bssid: "ap_west_exit_01", rssi: -50 },
      { bssid: "ap_west_underground_01", rssi: -59 },
      { bssid: "ap_tobu_01", rssi: -72 },
    ],
  },
  {
    label: "Simulate near Sunshine City Exit",
    observations: [
      { bssid: "ap_sunshine_01", rssi: -50 },
      { bssid: "ap_sunshine_02", rssi: -60 },
      { bssid: "ap_east_exit_01", rssi: -66 },
    ],
  },
];

export function App() {
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRouting, setIsRouting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    selectedStationId,
    stationMap,
    selectedFloorId,
    selectedStartNodeId,
    selectedStartZoneId,
    localizationResult,
    selectedDestinationPoiId,
    routeResult,
    preferences,
    poiFilters,
    setSelectedStationId,
    setStationMap,
    setSelectedFloorId,
    setSelectedStartNodeId,
    setSelectedStartZoneId,
    setLocalizationResult,
    setSelectedDestinationPoiId,
    setRouteResult,
    setPreferences,
    setPoiFilters,
  } = useNukemichiStore();

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setError(null);
      setIsLoading(true);
      try {
        const [stationList, map] = await Promise.all([
          getStations(),
          getStationMap(selectedStationId),
        ]);
        if (!cancelled) {
          setStations(stationList);
          setStationMap(map);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load station data.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [selectedStationId, setStationMap]);

  const filteredPois = useMemo(() => {
    if (!stationMap) {
      return [];
    }
    return stationMap.pois.filter((poi) => {
      const query = poiFilters.q.trim().toLowerCase();
      const matchesQuery =
        !query ||
        [poi.name, poi.name_ja, poi.name_zh, poi.description, ...poi.tags]
          .join(" ")
          .toLowerCase()
          .includes(query);
      const matchesCategory = poiFilters.category === "all" || poi.category === poiFilters.category;
      const matchesFloor = poiFilters.floor_id === "all" || poi.floor_id === poiFilters.floor_id;
      return matchesQuery && matchesCategory && matchesFloor;
    });
  }, [poiFilters, stationMap]);

  const selectedPoi = stationMap?.pois.find((poi) => poi.poi_id === selectedDestinationPoiId) ?? null;

  async function handleWifiPreset(observations: WifiObservation[]) {
    setError(null);
    try {
      const result = await localizeWifi(selectedStationId, observations);
      setLocalizationResult(result);
      if (result.estimated_zone_id) {
        setSelectedStartZoneId(result.estimated_zone_id);
      }
      if (result.nearest_start_node_ids[0]) {
        setSelectedStartNodeId(result.nearest_start_node_ids[0]);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Wi-Fi localization failed.");
    }
  }

  async function handleRoute() {
    if (!selectedDestinationPoiId) {
      setError("Choose a destination first.");
      return;
    }
    setError(null);
    setIsRouting(true);
    try {
      const route = await getRoute({
        stationId: selectedStationId,
        fromNodeId: selectedStartZoneId ? undefined : selectedStartNodeId,
        fromZoneId: selectedStartZoneId,
        toPoiId: selectedDestinationPoiId,
        preferences,
      });
      setRouteResult(route);
      setSelectedFloorId(route.path[0]?.floor_id ?? selectedFloorId);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Route calculation failed.");
    } finally {
      setIsRouting(false);
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6 px-5 py-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <MapPin aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-normal">Nukemichi</h1>
                <p className="text-sm text-muted-foreground">Ikebukuro indoor station navigation</p>
              </div>
            </div>
          </div>
          <label className="flex w-full max-w-xs flex-col gap-2 text-sm font-medium">
            Station
            <select
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={selectedStationId}
              onChange={(event) => {
                setSelectedStationId(event.target.value);
                setRouteResult(null);
              }}
            >
              {stations.map((station) => (
                <option key={station.station_id} value={station.station_id}>
                  {station.name}
                </option>
              ))}
            </select>
          </label>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <section className="grid items-start gap-6 xl:grid-cols-[380px_minmax(0,1fr)_360px]">
          <div className="flex flex-col gap-6">
            <CurrentLocationPanel
              isLoading={isLoading}
              onWifiPreset={(observations) => void handleWifiPreset(observations)}
            />
            <PreferencesPanel />
          </div>

          <IndoorMapView />

          <div className="flex flex-col gap-6">
            <DestinationPanel
              pois={filteredPois}
              selectedPoi={selectedPoi}
              onRoute={() => void handleRoute()}
              isRouting={isRouting}
            />
            <RouteResultPanel />
          </div>
        </section>
      </div>
    </main>
  );
}

function CurrentLocationPanel({
  isLoading,
  onWifiPreset,
}: {
  isLoading: boolean;
  onWifiPreset: (observations: WifiObservation[]) => void;
}) {
  const {
    stationMap,
    selectedStartNodeId,
    selectedStartZoneId,
    localizationResult,
    setSelectedStartNodeId,
    setSelectedStartZoneId,
    setRouteResult,
  } = useNukemichiStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Where are you now?</CardTitle>
        <CardDescription>Choose a start area manually or use a demo Wi-Fi scan.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <label className="flex flex-col gap-2 text-sm font-medium">
          Start zone
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={selectedStartZoneId ?? ""}
            disabled={isLoading}
            onChange={(event) => {
              const zoneId = event.target.value || null;
              const zone = stationMap?.zones.find((item) => item.zone_id === zoneId);
              setSelectedStartZoneId(zoneId);
              setSelectedStartNodeId(zone?.nearby_node_ids[0] ?? null);
              setRouteResult(null);
            }}
          >
            <option value="">Use selected node instead</option>
            {stationMap?.zones.map((zone) => (
              <option key={zone.zone_id} value={zone.zone_id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm font-medium">
          Start node
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={selectedStartNodeId ?? ""}
            disabled={isLoading}
            onChange={(event) => {
              setSelectedStartNodeId(event.target.value || null);
              setSelectedStartZoneId(null);
              setRouteResult(null);
            }}
          >
            {stationMap?.nodes
              .filter((node) => ["gate", "exit", "passage", "connector"].includes(node.type))
              .map((node) => (
                <option key={node.node_id} value={node.node_id}>
                  {node.name} ({node.floor_id})
                </option>
              ))}
          </select>
        </label>

        <div className="grid gap-2">
          {wifiPresets.map((preset) => (
            <Button key={preset.label} variant="outline" onClick={() => onWifiPreset(preset.observations)}>
              <LocateFixed data-icon="inline-start" />
              {preset.label}
            </Button>
          ))}
        </div>

        {localizationResult ? (
          <div className="rounded-md border bg-muted/60 p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">{localizationResult.estimated_zone_name ?? "Unknown zone"}</span>
              <Badge variant="secondary">{Math.round(localizationResult.confidence * 100)}%</Badge>
            </div>
            <p className="mt-2 text-muted-foreground">{localizationResult.message}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Nearest start: {localizationResult.nearest_start_node_ids.join(", ") || "manual selection needed"}
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function PreferencesPanel() {
  const { preferences, setPreferences, setRouteResult } = useNukemichiStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Preferences</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <label className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm font-medium">
          <span className="flex items-center gap-2">
            <Accessibility aria-hidden="true" />
            Avoid stairs
          </span>
          <input
            type="checkbox"
            checked={preferences.avoid_stairs}
            onChange={(event) => {
              setPreferences({ avoid_stairs: event.target.checked });
              setRouteResult(null);
            }}
          />
        </label>
        <label className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm font-medium">
          Prefer elevator
          <input
            type="checkbox"
            checked={preferences.prefer_elevator}
            onChange={(event) => {
              setPreferences({ prefer_elevator: event.target.checked });
              setRouteResult(null);
            }}
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-medium">
          Language
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={preferences.language}
            onChange={(event) => {
              setPreferences({ language: event.target.value as "en" | "ja" | "zh-TW" });
              setRouteResult(null);
            }}
          >
            <option value="en">en</option>
            <option value="ja">ja</option>
            <option value="zh-TW">zh-TW</option>
          </select>
        </label>
      </CardContent>
    </Card>
  );
}

function DestinationPanel({
  pois,
  selectedPoi,
  onRoute,
  isRouting,
}: {
  pois: Poi[];
  selectedPoi: Poi | null;
  onRoute: () => void;
  isRouting: boolean;
}) {
  const {
    stationMap,
    poiFilters,
    selectedDestinationPoiId,
    setPoiFilters,
    setSelectedDestinationPoiId,
    setSelectedFloorId,
    setRouteResult,
  } = useNukemichiStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Where do you want to go?</CardTitle>
        <CardDescription>Search exits, gates, shops, restrooms, lockers, and landmarks.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-2.5 text-muted-foreground" aria-hidden="true" />
          <Input
            className="pl-10"
            value={poiFilters.q}
            placeholder="Search coffee, exit, restroom..."
            onChange={(event) => setPoiFilters({ q: event.target.value })}
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={poiFilters.category}
            onChange={(event) => setPoiFilters({ category: event.target.value as PoiCategory | "all" })}
          >
            {categoryOptions.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={poiFilters.floor_id}
            onChange={(event) => setPoiFilters({ floor_id: event.target.value })}
          >
            <option value="all">all floors</option>
            {stationMap?.floors.map((floor) => (
              <option key={floor.floor_id} value={floor.floor_id}>
                {floor.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex max-h-[300px] flex-col gap-2 overflow-auto pr-1">
          {pois.map((poi) => (
            <button
              key={poi.poi_id}
              className={[
                "rounded-md border p-3 text-left transition-colors",
                selectedDestinationPoiId === poi.poi_id ? "border-primary bg-primary/10" : "hover:bg-accent",
              ].join(" ")}
              onClick={() => {
                setSelectedDestinationPoiId(poi.poi_id);
                setSelectedFloorId(poi.floor_id);
                setRouteResult(null);
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium">{poi.name}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{poi.description}</div>
                </div>
                <Badge variant="outline">{poi.category}</Badge>
              </div>
            </button>
          ))}
        </div>

        <Button onClick={onRoute} disabled={!selectedPoi || isRouting}>
          <ArrowRight data-icon="inline-start" />
          {isRouting ? "Calculating..." : "Calculate route"}
        </Button>
      </CardContent>
    </Card>
  );
}

function RouteResultPanel() {
  const { routeResult } = useNukemichiStore();

  if (!routeResult) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Route result</CardTitle>
          <CardDescription>Select a destination and calculate a route.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Route result</CardTitle>
        <CardDescription>
          {routeResult.distance_m}m · {routeResult.estimated_minutes} min · {routeResult.floors.join(", ")}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <Metric label="Stairs required" value={routeResult.requires_stairs ? "Yes" : "No"} />
          <Metric label="Uses elevator" value={routeResult.uses_elevator ? "Yes" : "No"} />
        </div>
        <ol className="flex flex-col gap-3">
          {routeResult.instructions.map((instruction, index) => (
            <li key={`${instruction.text}-${index}`} className="flex gap-3 rounded-md border p-3 text-sm">
              <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-secondary text-xs font-semibold">
                {index + 1}
              </span>
              <div>
                <div className="font-medium">{instruction.text}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {instruction.floor_id}
                  {instruction.to_floor_id ? ` to ${instruction.to_floor_id}` : ""}
                  {instruction.distance_m ? ` · ${instruction.distance_m}m` : ""}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 font-semibold">{value}</div>
    </div>
  );
}

function IndoorMapView() {
  const {
    stationMap,
    selectedFloorId,
    selectedDestinationPoiId,
    localizationResult,
    routeResult,
    setSelectedFloorId,
  } = useNukemichiStore();

  const nodesById = useMemo(() => {
    const map = new Map<string, Node>();
    stationMap?.nodes.forEach((node) => map.set(node.node_id, node));
    return map;
  }, [stationMap]);

  const routeNodeIds = new Set(routeResult?.path.map((node) => node.node_id) ?? []);
  const routePairs = new Set(
    routeResult?.path.slice(1).map((node, index) => {
      const previous = routeResult.path[index];
      return pairKey(previous.node_id, node.node_id);
    }) ?? [],
  );

  const floorNodes = stationMap?.nodes.filter((node) => node.floor_id === selectedFloorId) ?? [];
  const floorZones = stationMap?.zones.filter((zone) => zone.floor_id === selectedFloorId) ?? [];
  const floorPois = stationMap?.pois.filter((poi) => poi.floor_id === selectedFloorId) ?? [];
  const floorEdges =
    stationMap?.edges.filter((edge) => edge.from_floor_id === selectedFloorId && edge.to_floor_id === selectedFloorId) ??
    [];

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle>Indoor map</CardTitle>
            <CardDescription>Zone-first demo map with highlighted routes and Wi-Fi estimate.</CardDescription>
          </div>
          <div className="flex gap-2">
            {stationMap?.floors.map((floor) => (
              <Button
                key={floor.floor_id}
                variant={selectedFloorId === floor.floor_id ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedFloorId(floor.floor_id)}
              >
                {floor.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative h-[640px] bg-[linear-gradient(135deg,hsl(var(--muted))_0%,hsl(var(--background))_56%,hsl(var(--accent))_100%)]">
          <svg className="h-full w-full" viewBox="0 0 960 560" role="img" aria-label="Simplified Ikebukuro indoor map">
            <defs>
              <filter id="routeGlow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {floorZones.map((zone) => (
              <rect
                key={zone.zone_id}
                x={zone.bbox.x}
                y={zone.bbox.y}
                width={zone.bbox.width}
                height={zone.bbox.height}
                rx="10"
                className={
                  localizationResult?.estimated_zone_id === zone.zone_id
                    ? "fill-primary/20 stroke-primary"
                    : "fill-card/70 stroke-border"
                }
                strokeWidth={localizationResult?.estimated_zone_id === zone.zone_id ? 3 : 1.5}
              />
            ))}

            {floorEdges.map((edge) => {
              const fromNode = nodesById.get(edge.from_node_id);
              const toNode = nodesById.get(edge.to_node_id);
              if (!fromNode || !toNode) {
                return null;
              }
              const isRoute = routePairs.has(pairKey(edge.from_node_id, edge.to_node_id));
              return (
                <line
                  key={edge.edge_id}
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  className={isRoute ? "stroke-primary" : "stroke-muted-foreground/30"}
                  strokeWidth={isRoute ? 7 : 3}
                  strokeLinecap="round"
                  filter={isRoute ? "url(#routeGlow)" : undefined}
                />
              );
            })}

            {floorPois.map((poi) => {
              const anchor = nodesById.get(poi.anchor_node_id);
              if (!anchor) {
                return null;
              }
              const isSelected = poi.poi_id === selectedDestinationPoiId;
              return (
                <g key={poi.poi_id} transform={`translate(${anchor.x}, ${anchor.y})`}>
                  <circle r={isSelected ? 16 : 11} className={isSelected ? "fill-primary" : "fill-card stroke-primary"} strokeWidth="2" />
                  <text x="18" y="5" className="fill-foreground text-[15px] font-semibold">
                    {shortPoiLabel(poi)}
                  </text>
                </g>
              );
            })}

            {floorNodes.map((node) => {
              const isRoute = routeNodeIds.has(node.node_id);
              return (
                <g key={node.node_id} transform={`translate(${node.x}, ${node.y})`}>
                  <circle
                    r={isRoute ? 10 : 7}
                    className={isRoute ? "fill-primary stroke-primary-foreground" : nodeClassName(node.type)}
                    strokeWidth="2"
                  />
                  {["gate", "exit"].includes(node.type) ? (
                    <text x="12" y="-10" className="fill-muted-foreground text-[12px]">
                      {node.name}
                    </text>
                  ) : null}
                </g>
              );
            })}
          </svg>
          <div className="absolute bottom-4 left-4 flex flex-wrap gap-2 rounded-md border bg-card/95 p-3 text-xs shadow-panel">
            <Legend icon={<Ticket aria-hidden="true" />} label="Gate" />
            <Legend icon={<Landmark aria-hidden="true" />} label="Exit" />
            <Legend icon={<Store aria-hidden="true" />} label="POI" />
            <Legend icon={<Coffee aria-hidden="true" />} label="Route" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function pairKey(a: string, b: string) {
  return [a, b].sort().join("::");
}

function nodeClassName(type: Node["type"]) {
  if (type === "gate") {
    return "fill-sky-600 stroke-white";
  }
  if (type === "exit") {
    return "fill-emerald-600 stroke-white";
  }
  if (["stairs", "elevator", "escalator"].includes(type)) {
    return "fill-amber-500 stroke-white";
  }
  return "fill-slate-500 stroke-white";
}

function shortPoiLabel(poi: Poi) {
  if (poi.category === "restroom") {
    return "Restroom";
  }
  if (poi.category === "locker") {
    return "Locker";
  }
  if (poi.category === "coffee") {
    return "Coffee";
  }
  if (poi.category === "convenience") {
    return "Store";
  }
  return poi.name.replace(" near ", " ");
}

function Legend({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      {icon}
      {label}
    </span>
  );
}
