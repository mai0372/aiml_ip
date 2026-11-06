"""
backend/tests/test_api.py
Test suite for ClauseLens FastAPI endpoints:
- Health and runtime mode check
- Indian statutory rules catalog
- Logic Lab conversion (9 steps) and resolution proof API
- Contract analysis lifecycle & What-If query answering
"""

import pytest
import os
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "offline" in data["mode"].lower() or "gemini" in data["mode"].lower()


def test_api_get_rules():
    res = client.get("/api/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) == 10
    rule_ids = {r["id"] for r in rules}
    assert "R01" in rule_ids
    assert "R02" in rule_ids
    assert "R05" in rule_ids

    # Assert Indian legal context attributes
    for r in rules:
        assert "statute_name" in r
        assert "source_url" in r
        assert "reviewed" in r
        assert r["reviewed"] is False


def test_api_logic_convert_wff():
    res = client.post("/api/logic/convert", json={"formula": "forall x: (Man(x) -> Mortal(x))"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["steps"]) == 10
    assert len(data["clauses"]) >= 1


def test_api_logic_prove():
    res = client.post("/api/logic/prove", json={
        "premises": ["Man(Socrates)", "forall x: (Man(x) -> Mortal(x))"],
        "goal": "Mortal(Socrates)"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "REFUTATION_FOUND"
    assert data["success"] is True
    assert data["empty_clause_id"] is not None


def test_api_analysis_and_what_if():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "samples", "sample_a_fair.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Create analysis
    create_res = client.post("/api/analyses", json={"text": text, "filename": "sample_a_fair.txt"})
    assert create_res.status_code == 200
    analysis_id = create_res.json()["id"]

    # 2. Consume events to finish analysis
    events_res = client.get(f"/api/analyses/{analysis_id}/events")
    assert events_res.status_code == 200
    assert "data:" in events_res.text

    # 3. Retrieve analysis from database
    get_res = client.get(f"/api/analyses/{analysis_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert len(data["clauses"]) > 0

    # 4. Ask What-If query
    ask_res = client.post(f"/api/analyses/{analysis_id}/ask", json={"question": "Can I terminate early?"})
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert ask_data["answered"] is True

