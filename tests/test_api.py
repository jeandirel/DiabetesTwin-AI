from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simulate_endpoint():
    payload = {
        "patient": {
            "name": "Test Twin",
            "age": 45,
            "phenotype": "balanced",
            "baseline_glucose": 112,
            "carb_sensitivity": 0.72,
            "activity_sensitivity": 18,
            "stress_sensitivity": 16,
            "circadian_amplitude": 7,
        },
        "scenario": {
            "meals": [{"hour": 12, "carbs_g": 60, "label": "Lunch"}],
            "exercise": [],
            "stress": 0.2,
            "sleep_hours": 7.5,
            "sleep_quality": 0.8,
        },
        "seed": 42,
        "step_minutes": 5,
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["points"]) == 288
    assert 0 <= body["metrics"]["time_in_range_pct"] <= 100
