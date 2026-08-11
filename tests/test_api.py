from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "DiabetesTwin-AI" in response.text
    assert "Digital twin simulation" in response.text
    assert "Real CGM explorer" in response.text


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


def test_demo_cgmacros_endpoint():
    response = client.get("/demo/cgmacros", params={"participant_id": "001", "max_points": 300})
    assert response.status_code == 200
    body = response.json()
    assert body["participant_id"] == "001"
    assert body["license"] == "CC BY-NC-SA 4.0"
    assert 0 < len(body["points"]) <= 320
    assert 0 <= body["metrics"]["time_in_range_pct"] <= 100
