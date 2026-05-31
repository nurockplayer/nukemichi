from app.data_store import load_station_bundle
from app.localization import estimate_wifi_zone
from app.schemas import WifiAccessPointObservation


def test_wifi_localization_estimates_jr_east_gate_area():
    bundle = load_station_bundle("ikebukuro")

    result = estimate_wifi_zone(
        bundle,
        [
            WifiAccessPointObservation(bssid="ap_jr_east_01", rssi=-53),
            WifiAccessPointObservation(bssid="ap_station_core_01", rssi=-69),
            WifiAccessPointObservation(bssid="ap_jr_east_02", rssi=-60),
        ],
    )

    assert result.estimated_zone_id == "jr_east_gate_area"
    assert result.confidence > 0


def test_wifi_localization_unknown_aps_returns_no_estimated_zone():
    bundle = load_station_bundle("ikebukuro")

    result = estimate_wifi_zone(
        bundle,
        [
            WifiAccessPointObservation(bssid="unknown_ap_001", rssi=-45),
            WifiAccessPointObservation(bssid="unknown_ap_002", rssi=-72),
        ],
    )

    assert result.estimated_zone_id is None
    assert result.confidence == 0


def test_wifi_localization_low_confidence_prompts_manual_confirmation():
    bundle = load_station_bundle("ikebukuro")

    result = estimate_wifi_zone(
        bundle,
        [
            WifiAccessPointObservation(bssid="ap_jr_east_01", rssi=-5),
        ],
    )

    assert result.confidence == 0
    assert "manual" in result.message.lower()
