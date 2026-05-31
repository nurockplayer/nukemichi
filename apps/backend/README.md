# Nukemichi Backend

FastAPI service for station map data, demo Wi-Fi zone localization, and Dijkstra routing.

```bash
uv sync
uv run fastapi dev app/main.py
uv run pytest -q
uv run python -m app.validate_data ikebukuro
uv run python -m app.seed_pipeline ikebukuro app/data/seeds/ikebukuro_east_locker_seed.example.json --dry-run
uv run python -m app.seed_pipeline ikebukuro app/data/seeds/ikebukuro_east_locker_seed.example.json --output /tmp/ikebukuro_promoted_station.json
```
