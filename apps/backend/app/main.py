from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.data_store import get_station_map, load_station_bundle
from app.localization import estimate_wifi_zone
from app.routing import calculate_route
from app.schemas import (
    FingerprintCollectionPoint,
    LocationZone,
    Poi,
    RouteRequest,
    RouteResponse,
    Station,
    StationSurveyNote,
    StationMapResponse,
    WifiLocalizationRequest,
    WifiLocalizationResponse,
)


app = FastAPI(title="Nukemichi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stations", response_model=list[Station])
def stations() -> list[Station]:
    return [load_station_bundle("ikebukuro").station]


@app.get("/stations/{station_id}/map", response_model=StationMapResponse)
def station_map(station_id: str) -> StationMapResponse:
    return get_station_map(station_id)


@app.get("/stations/{station_id}/pois", response_model=list[Poi])
def station_pois(
    station_id: str,
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    floor_id: str | None = Query(default=None),
) -> list[Poi]:
    bundle = load_station_bundle(station_id)
    pois = bundle.pois
    if q:
        query = q.casefold()
        pois = [
            poi for poi in pois
            if query in " ".join([poi.name, poi.name_ja, poi.name_zh, poi.description, *poi.tags]).casefold()
        ]
    if category:
        pois = [poi for poi in pois if poi.category == category]
    if floor_id:
        pois = [poi for poi in pois if poi.floor_id == floor_id]
    return pois


@app.get("/stations/{station_id}/zones", response_model=list[LocationZone])
def station_zones(station_id: str) -> list[LocationZone]:
    return load_station_bundle(station_id).zones


@app.get("/stations/{station_id}/survey-notes", response_model=list[StationSurveyNote])
def station_survey_notes(station_id: str) -> list[StationSurveyNote]:
    return load_station_bundle(station_id).survey_notes


@app.get("/stations/{station_id}/fingerprint-collection-points", response_model=list[FingerprintCollectionPoint])
def station_fingerprint_collection_points(station_id: str) -> list[FingerprintCollectionPoint]:
    return load_station_bundle(station_id).fingerprint_collection_points


@app.post("/localize/wifi", response_model=WifiLocalizationResponse)
def localize_wifi(request: WifiLocalizationRequest) -> WifiLocalizationResponse:
    bundle = load_station_bundle(request.station_id)
    return estimate_wifi_zone(bundle, request.observed_aps)


@app.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    bundle = load_station_bundle(request.station_id)
    return calculate_route(
        bundle,
        from_node_id=request.from_node_id,
        from_zone_id=request.from_zone_id,
        to_poi_id=request.to_poi_id,
        preferences=request.preferences,
    )
