# Nukemichi Backend

FastAPI service for station map data, demo Wi-Fi zone localization, and Dijkstra routing.

```bash
uv sync
uv run fastapi dev app/main.py
uv run pytest -q
uv run python -m app.validate_data ikebukuro
```
