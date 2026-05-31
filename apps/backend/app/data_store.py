from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from app.schemas import StationBundle, StationMapResponse


DATA_DIR = Path(__file__).parent / "data"


@lru_cache(maxsize=8)
def load_station_bundle(station_id: str) -> StationBundle:
    path = DATA_DIR / f"{station_id}_demo_station.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' is not supported yet.")

    with path.open("r", encoding="utf-8") as file:
        return StationBundle.model_validate(json.load(file))


def get_station_map(station_id: str) -> StationMapResponse:
    bundle = load_station_bundle(station_id)
    return StationMapResponse(
        station=bundle.station,
        floors=bundle.floors,
        nodes=bundle.nodes,
        edges=bundle.edges,
        pois=bundle.pois,
        zones=bundle.zones,
    )
