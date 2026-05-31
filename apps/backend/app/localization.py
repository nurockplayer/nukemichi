from __future__ import annotations

from collections import defaultdict

from app.schemas import StationBundle, WifiAccessPointObservation, WifiLocalizationResponse


MIN_COMMON_APS = 1


def _fingerprint_score(
    observed_aps: list[WifiAccessPointObservation],
    fingerprint_aps: dict[str, int],
) -> float | None:
    observed_by_bssid = {ap.bssid: ap.rssi for ap in observed_aps}
    common_bssids = set(observed_by_bssid).intersection(fingerprint_aps)
    if len(common_bssids) < MIN_COMMON_APS:
        return None

    average_abs_rssi_diff = sum(
        abs(observed_by_bssid[bssid] - fingerprint_aps[bssid]) for bssid in common_bssids
    ) / len(common_bssids)
    return len(common_bssids) * 10 - average_abs_rssi_diff


def estimate_wifi_zone(
    bundle: StationBundle,
    observed_aps: list[WifiAccessPointObservation],
) -> WifiLocalizationResponse:
    zone_scores: dict[str, list[float]] = defaultdict(list)

    for fingerprint in bundle.wifi_fingerprints:
        fingerprint_aps = {ap.bssid: ap.rssi for ap in fingerprint.observed_aps}
        score = _fingerprint_score(observed_aps, fingerprint_aps)
        if score is not None:
            zone_scores[fingerprint.zone_id].append(score)

    if not zone_scores:
        return WifiLocalizationResponse(
            station_id=bundle.station.station_id,
            estimated_zone_id=None,
            estimated_zone_name=None,
            confidence=0.0,
            nearest_start_node_ids=[],
            message="Not enough matching demo Wi-Fi access points. Please select your area manually.",
        )

    aggregated = {
        zone_id: sum(scores) / len(scores)
        for zone_id, scores in zone_scores.items()
    }
    best_zone_id, best_score = max(aggregated.items(), key=lambda item: item[1])
    zone = next(zone for zone in bundle.zones if zone.zone_id == best_zone_id)
    confidence = max(0.0, min(1.0, best_score / 30))

    message = (
        f"You seem to be near {zone.name}."
        if confidence >= 0.35
        else "Low Wi-Fi confidence. Please confirm or manually select your current area."
    )
    return WifiLocalizationResponse(
        station_id=bundle.station.station_id,
        estimated_zone_id=zone.zone_id,
        estimated_zone_name=zone.name,
        confidence=round(confidence, 2),
        nearest_start_node_ids=zone.nearby_node_ids[:3],
        message=message,
    )
