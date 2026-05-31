from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stations_endpoint_returns_ikebukuro():
    response = client.get("/stations")

    assert response.status_code == 200
    assert response.json()[0]["station_id"] == "ikebukuro"


def test_station_map_endpoint_returns_graph_data():
    response = client.get("/stations/ikebukuro/map")
    body = response.json()

    assert response.status_code == 200
    assert body["station"]["station_id"] == "ikebukuro"
    assert body["nodes"]
    assert body["edges"]
    assert body["pois"]
    assert body["zones"]


def test_pois_endpoint_filters_by_category():
    response = client.get("/stations/ikebukuro/pois?category=restroom")
    body = response.json()

    assert response.status_code == 200
    assert body
    assert all(poi["category"] == "restroom" for poi in body)


def test_zones_endpoint_returns_location_zones():
    response = client.get("/stations/ikebukuro/zones")
    body = response.json()

    assert response.status_code == 200
    assert any(zone["zone_id"] == "jr_east_gate_area" for zone in body)


def test_localize_wifi_endpoint_returns_estimated_zone():
    response = client.post(
        "/localize/wifi",
        json={
            "station_id": "ikebukuro",
            "observed_aps": [
                {"bssid": "ap_jr_east_01", "rssi": -53},
                {"bssid": "ap_station_core_01", "rssi": -69},
                {"bssid": "ap_jr_east_02", "rssi": -60},
            ],
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["estimated_zone_id"] == "jr_east_gate_area"
    assert body["confidence"] > 0


def test_route_endpoint_returns_route_from_zone():
    response = client.post(
        "/route",
        json={
            "station_id": "ikebukuro",
            "from_zone_id": "jr_east_gate_area",
            "to_poi_id": "sunshine_city_exit",
            "preferences": {
                "avoid_stairs": True,
                "prefer_elevator": False,
                "language": "en",
            },
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["start_node_id"] == "jr_east_gate"
    assert body["destination_poi_id"] == "sunshine_city_exit"
    assert body["path"]
    assert body["instructions"]
