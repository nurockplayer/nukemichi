# Nukemichi

[![CI](https://github.com/nurockplayer/nukemichi/actions/workflows/ci.yml/badge.svg)](https://github.com/nurockplayer/nukemichi/actions/workflows/ci.yml)

Nukemichi is an indoor navigation MVP for large Tokyo stations. The first target station is Ikebukuro. It helps users find the nearest gate, exit, POI, and route inside complex station buildings.

Product direction: Ikebukuro-first / Wi-Fi-first / iBeacon-as-supplement.

Nukemichi does not try to locate the user at an exact coordinate in the MVP. It estimates the user’s nearby station zone, such as a gate area, exit area, or underground passage, and uses that zone as a practical navigation starting point.

> Demo data warning: current Ikebukuro station data is fictional, hand-authored, and intended only for product and engineering demos. It is not yet suitable for real navigation.

## MVP scope

- Ikebukuro station graph
- Manual routing from a selected node or zone
- Zone-based localization
- Demo Wi-Fi fingerprint localization
- POI / gate / exit search
- Simplified indoor map
- Step-by-step route instructions

## What this MVP does not do

- no real-time GPS indoor positioning
- no real Android Wi-Fi scan yet
- no real iOS Wi-Fi scan yet
- no iBeacon scanning yet
- no AR navigation
- no 3D modeling
- no full Tokyo coverage yet

## Architecture

The backend owns the station graph, routing, localization, and demo data. The frontend fetches map data from the API and never hardcodes station content.

- `Station`, `Floor`, `Node`, and `Edge` model the station graph.
- `POI` records searchable destinations such as exits, gates, lockers, restrooms, shops, and landmarks.
- `LocationZone` is the main localization unit for the MVP.
- Demo Wi-Fi fingerprints map observed APs to nearby zones.
- iBeacon models are reserved as an optional supplement when Wi-Fi confidence is low. This MVP does not do pure iBeacon triangulation.
- `POST /route` runs Dijkstra on the backend.
- `POST /localize/wifi` runs demo fingerprint matching on the backend.
- Zustand stores selected station, floor, start node/zone, localization result, destination, route, preferences, and POI filters in the frontend.

## How to run

Docker Compose:

```bash
docker compose up
```

Docker Compose starts Postgres/PostGIS, the FastAPI backend, and an nginx-served frontend build. In Docker, the frontend calls `/api`; nginx proxies that path to the backend service at `http://backend:8000`. Local Vite development uses the same `/api` base path and proxies to `http://localhost:8000`.

Backend local dev:

```bash
cd apps/backend
uv sync
uv run fastapi dev app/main.py
```

Backend tests:

```bash
cd apps/backend
uv run pytest -q
```

Frontend local dev:

```bash
cd apps/frontend
pnpm install
pnpm dev
```

Frontend build:

```bash
cd apps/frontend
pnpm build
```

Root frontend build shortcut:

```bash
pnpm build:frontend
```

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## API examples

Health:

```bash
curl http://localhost:8000/health
```

Stations:

```bash
curl http://localhost:8000/stations
```

Ikebukuro map:

```bash
curl http://localhost:8000/stations/ikebukuro/map
```

Demo Wi-Fi localization:

```bash
curl -X POST http://localhost:8000/localize/wifi \
  -H "Content-Type: application/json" \
  -d '{
    "station_id": "ikebukuro",
    "observed_aps": [
      { "bssid": "ap_jr_east_01", "rssi": -53 },
      { "bssid": "ap_station_core_01", "rssi": -69 },
      { "bssid": "ap_jr_east_02", "rssi": -60 }
    ]
  }'
```

Route from a zone:

```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "station_id": "ikebukuro",
    "from_zone_id": "jr_east_gate_area",
    "to_poi_id": "sunshine_city_exit",
    "preferences": {
      "avoid_stairs": true,
      "prefer_elevator": false,
      "language": "zh-TW"
    }
  }'
```

## Roadmap

Phase 1:

- Ikebukuro station graph
- manual routing
- demo Wi-Fi fingerprint localization
- zone-based localization
- POI / gate / exit search

Phase 1.1:

- add CI
- add backend tests
- validate demo graph integrity
- improve Docker / frontend API proxy

Phase 1.2:

- expand Ikebukuro graph
- add real station survey notes
- add POI editor
- add fingerprint collection schema

Phase 2:

- real Wi-Fi scan support on Android
- iOS fallback using manual zone / QR code
- POI editor
- better station map data import
- crowd-sourced fingerprint collection

Phase 3:

- iBeacon optional supplement
- PDR / step-based correction
- Shinjuku support
- multilingual tourist mode

Phase 4:

- B2B indoor navigation SDK
- station / mall / airport expansion

## Current limitations

- The station graph is hand-authored demo data, not official GIS data.
- Wi-Fi localization uses simulated AP readings and simple fingerprint scoring.
- Postgres + PostGIS is provisioned for the target architecture, but the MVP reads JSON demo data.
- The map is a simplified SVG diagram, not a surveyed indoor map.
