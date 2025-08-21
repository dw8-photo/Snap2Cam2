
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_parse_basic():
    body = {
        "text": "No School — Labor Day (Mon, Sept 1). Early Release 1:30pm on 9/18.",
        "timezone": "America/Detroit",
        "default_year": 2025
    }
    r = client.post("/parse_events", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) >= 1
