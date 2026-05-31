# Nukemichi Seed Pipeline

The seed pipeline is a backend-first way to review Ikebukuro data additions before they are promoted into the main demo station JSON.

It is intentionally dry-run only in this phase. The goal is to make POI and graph edits reviewable without giving the app a write path that can silently mutate navigation data.

## What a Seed Draft Can Add

A seed draft may include:

- `nodes`
- `edges`
- `pois`
- `zones`
- `survey_notes`
- `fingerprint_collection_points`

The most common Phase 1.2 use case is adding a new POI with:

- one `poi_anchor` node
- one or more connecting `edges`
- one `poi`

## Dry-Run Command

From the backend directory:

```bash
uv run python -m app.seed_pipeline ikebukuro app/data/seeds/ikebukuro_east_locker_seed.example.json --dry-run
```

Expected output includes planned addition counts and any validation issues.

## Validation Rules

The dry-run validator checks:

- draft `station_id` matches the target station
- new IDs do not duplicate existing station data
- IDs are unique within the draft
- node, POI, zone, survey-note, and collection-point floor references exist
- edge node references point to existing nodes or nodes in the same draft
- POI anchors point to existing nodes or nodes in the same draft
- zone nearby node, gate, and exit references exist
- survey-note related nodes and zones exist
- fingerprint collection point zone and suggested node references exist

## Promotion Rules

For now, promotion is manual:

1. Create a seed draft JSON.
2. Run the dry-run command.
3. Review the output in a pull request or commit diff.
4. Copy accepted records into `apps/backend/app/data/ikebukuro_demo_station.json`.
5. Run backend tests and data validation.

This keeps the MVP honest: the current Ikebukuro data is still fictional and hand-authored, but every new data change has a repeatable review step before it affects routing.

## Current Limits

- The seed pipeline does not write to the main demo JSON.
- It does not import PostGIS data.
- It does not verify real-world station accuracy.
- It does not collect real Wi-Fi or iBeacon scans.
