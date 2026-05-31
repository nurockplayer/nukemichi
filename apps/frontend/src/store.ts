import { create } from "zustand";

import type {
  LocalizationResult,
  PoiFilters,
  Preferences,
  RouteResult,
  StationMap,
} from "./types";

interface NukemichiState {
  selectedStationId: string;
  stationMap: StationMap | null;
  selectedFloorId: string;
  selectedStartNodeId: string | null;
  selectedStartZoneId: string | null;
  localizationResult: LocalizationResult | null;
  selectedDestinationPoiId: string | null;
  routeResult: RouteResult | null;
  preferences: Preferences;
  poiFilters: PoiFilters;
  setSelectedStationId: (selectedStationId: string) => void;
  setStationMap: (stationMap: StationMap) => void;
  setSelectedFloorId: (selectedFloorId: string) => void;
  setSelectedStartNodeId: (selectedStartNodeId: string | null) => void;
  setSelectedStartZoneId: (selectedStartZoneId: string | null) => void;
  setLocalizationResult: (localizationResult: LocalizationResult | null) => void;
  setSelectedDestinationPoiId: (selectedDestinationPoiId: string | null) => void;
  setRouteResult: (routeResult: RouteResult | null) => void;
  setPreferences: (preferences: Partial<Preferences>) => void;
  setPoiFilters: (poiFilters: Partial<PoiFilters>) => void;
}

export const useNukemichiStore = create<NukemichiState>((set) => ({
  selectedStationId: "ikebukuro",
  stationMap: null,
  selectedFloorId: "B1",
  selectedStartNodeId: null,
  selectedStartZoneId: null,
  localizationResult: null,
  selectedDestinationPoiId: null,
  routeResult: null,
  preferences: {
    avoid_stairs: true,
    prefer_elevator: false,
    language: "en",
  },
  poiFilters: {
    q: "",
    category: "all",
    floor_id: "all",
  },
  setSelectedStationId: (selectedStationId) => set({ selectedStationId }),
  setStationMap: (stationMap) => set({
    stationMap,
    selectedFloorId: stationMap.floors[0]?.floor_id ?? "B1",
    selectedStartZoneId: stationMap.zones[0]?.zone_id ?? null,
    selectedStartNodeId: stationMap.zones[0]?.nearby_node_ids[0] ?? null,
  }),
  setSelectedFloorId: (selectedFloorId) => set({ selectedFloorId }),
  setSelectedStartNodeId: (selectedStartNodeId) => set({ selectedStartNodeId }),
  setSelectedStartZoneId: (selectedStartZoneId) => set({ selectedStartZoneId }),
  setLocalizationResult: (localizationResult) => set({ localizationResult }),
  setSelectedDestinationPoiId: (selectedDestinationPoiId) => set({ selectedDestinationPoiId }),
  setRouteResult: (routeResult) => set({ routeResult }),
  setPreferences: (preferences) => set((state) => ({ preferences: { ...state.preferences, ...preferences } })),
  setPoiFilters: (poiFilters) => set((state) => ({ poiFilters: { ...state.poiFilters, ...poiFilters } })),
}));
