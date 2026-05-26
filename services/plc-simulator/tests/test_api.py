from fastapi.testclient import TestClient

from app.main import app


def test_set_high_tank_scenario_returns_alarmed_state():
    with TestClient(app) as client:
        response = client.post("/api/sim/scenario", json={"scenario": "high_tank"})

    assert response.status_code == 200
    body = response.json()
    assert body["tank_level"] > 95.0
    assert body["alarm"] is True
    assert body["pump_running"] is True


def test_set_normal_scenario_returns_reset_state():
    with TestClient(app) as client:
        client.post("/api/sim/scenario", json={"scenario": "high_tank"})
        response = client.post("/api/sim/scenario", json={"scenario": "normal"})

    assert response.status_code == 200
    body = response.json()
    assert body["tank_level"] == 50.0
    assert body["alarm"] is False
    assert body["pump_running"] is True


def test_invalid_scenario_is_rejected():
    with TestClient(app) as client:
        response = client.post("/api/sim/scenario", json={"scenario": "unsupported"})

    assert response.status_code == 422
