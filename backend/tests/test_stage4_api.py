import pytest


def test_auth_login_and_me(client):
    # Test doctor login
    res = client.post("/api/auth/login", json={"email": "dr.mehta@clinic.local", "password": "ClinicianDemo!2026"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["doctor"]["email"] == "dr.mehta@clinic.local"

    # Test me endpoint
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Dr. A. Mehta"

def test_list_patients_and_patient_detail(client):
    res = client.get("/api/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) >= 4
    
    # Check patient structure matches frontend expectations
    p = patients[0]
    assert "id" in p
    assert "syntheticCohortLabel" in p
    assert "visits" in p
    assert len(p["visits"]) >= 1

    # Check visit structure
    v = p["visits"][0]
    assert "domainScores" in v
    assert "Reproductive" in v["domainScores"]
    assert "deltas" in v
    assert "observations" in v

def test_get_patient_trends(client):
    res = client.get("/api/patients/P-0042/trends?parameter=weight")
    assert res.status_code == 200
    points = res.json()
    assert len(points) >= 4
    for pt in points:
        assert "value" in pt
        assert "visitDate" in pt
        assert "visitNumber" in pt

def test_get_deltas_endpoint(client):
    res = client.get("/api/v1/patients/P-0042/visits/v2-p-0042/deltas")
    assert res.status_code == 200
    data = res.json()
    assert data["decision_support"]["decision_support_only"] is True
    assert "deltas" in data
    assert data["total_deltas"] > 0
    assert data["meaningful_deltas_count"] > 0

def test_get_scores_endpoint_with_completeness_and_citations(client):
    res = client.get("/api/v1/patients/P-0042/visits/v2-p-0042/scores")
    assert res.status_code == 200
    data = res.json()
    assert data["decision_support"]["decision_support_only"] is True
    assert "domain_scores" in data
    assert "data_completeness" in data
    # Check Section 3B completeness object
    assert "Reproductive" in data["data_completeness"]
    rep_comp = data["data_completeness"]["Reproductive"]
    assert "completeness_ratio" in rep_comp
    assert "confidence" in rep_comp
    assert "missing_fields" in rep_comp

    # Check guideline citations are exposed
    assert "guideline_citations" in data
    assert "2023 International PCOS Guideline" in data["guideline_citations"]["Reproductive"]

def test_evidence_drilldown_endpoint(client):
    res = client.get("/api/v1/patients/P-0042/visits/v2-p-0042/evidence/Metabolic")
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "Metabolic"
    assert "evidence" in data
    assert len(data["evidence"]) > 0
    # Every evidence item contains parameter and value
    first_ev = data["evidence"][0]
    assert "parameter" in first_ev
    assert "value" in first_ev
