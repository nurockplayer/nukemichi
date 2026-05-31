# Ikebukuro Data Expansion Guide

This guide is for humans expanding Nukemichi beyond the first fictional demo graph. The MVP remains Ikebukuro-first, Wi-Fi-first, and zone-based.

## Product Principle

Nukemichi should not claim exact indoor coordinates in the MVP. Every new data point should improve one of these practical questions:

- Which station zone is the user probably near?
- Which gate, exit, underground passage, or landmark is closest?
- Which route is easier to follow, especially when avoiding stairs?

## Data Safety

Current demo data is hand-authored and fictional. Do not use it for real navigation, emergency guidance, accessibility guarantees, or official station directions.

When adding real survey-derived data:

- Keep source notes separate from graph nodes until reviewed.
- Prefer conservative labels such as `near`, `toward`, and `area`.
- Avoid precision claims below zone level.
- Mark uncertain observations as `needs_review`.
- Keep accessibility details explicit; never infer barrier-free access from distance alone.

## Survey Notes

Survey notes capture human observations before they become graph changes. A useful note should answer:

- where the observation was made
- which existing node or zone it relates to
- what was observed
- what graph/data action is suggested
- how confident the observer is

Suggested lifecycle:

1. `needs_review`: raw observation captured.
2. `accepted`: reviewed and ready to convert into graph or POI changes.
3. `applied`: graph/data has been updated.
4. `rejected`: not useful, duplicate, or unverifiable.

Example:

```json
{
  "note_id": "survey_ikebukuro_east_passage_001",
  "station_id": "ikebukuro",
  "floor_id": "B1",
  "related_node_ids": ["east_underground_passage"],
  "related_zone_ids": ["east_exit_underground_area"],
  "source_type": "manual_survey",
  "title": "East underground passage has elevator signage",
  "summary": "Observed signs pointing from the east underground passage toward the B1 to 1F elevator.",
  "observed_at": "2026-05-20T14:30:00+09:00",
  "confidence": "medium",
  "status": "needs_review",
  "action_items": ["Verify elevator route distance", "Confirm whether signage is visible from JR East Gate side"]
}
```

## Fingerprint Collection Points

Fingerprint collection points describe where future demo or real Wi-Fi samples should be collected. They are not live scans.

Each point should be tied to a zone and optionally to a nearby node. Collection instructions should help a human gather consistent samples later.

Minimum target for a zone before trusting it more than manual selection:

- 2 or more device types when possible
- 3 or more samples per collection point
- samples at different crowd/time conditions
- at least one negative/edge sample near adjacent zones

Example:

```json
{
  "collection_point_id": "cp_jr_east_gate_primary",
  "station_id": "ikebukuro",
  "zone_id": "jr_east_gate_area",
  "floor_id": "B1",
  "suggested_node_id": "jr_east_gate",
  "label": "JR East Gate primary sample point",
  "instructions": "Stand near the JR East Gate signage, face the central passage, and collect three Wi-Fi snapshots.",
  "min_samples": 3,
  "device_types": ["demo_android", "demo_ios"]
}
```

## Expansion Checklist

Before merging new graph data:

- Every ID is stable, lowercase, and descriptive.
- Every referenced floor, node, zone, POI, and collection point exists.
- Every new POI is reachable from primary gates in backend tests.
- Every accessibility claim is represented on edges, not only in prose.
- Demo localization still returns a zone, not a coordinate.
- README or this guide is updated when data collection rules change.
