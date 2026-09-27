import pytest

# ==============================================================================
# 1. POST /patients Tests
# ==============================================================================

def test_create_patient_success(client):
    payload = {
        "patient_id": "P-9001",
        "syntheticCohortLabel": "Phenotype A - Test Cohort",
        "age": 25,
        "populationEthnicityTag": "asian_south_asian",
        "notes": "Test patient registration"
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["patient_id"] == "P-9001"
    assert data["age"] == 25
    assert data["population_ethnicity_tag"] == "asian_south_asian"
    assert data["age_range_warning"] is None

def test_create_patient_duplicate_id_rejected(client):
    payload = {
        "patient_id": "P-9001", # Already created in previous test
        "age": 28
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"].lower()

def test_create_patient_age_warning_outside_typical_range(client):
    # Adolescent or peri-menopausal edge case
    payload = {
        "patient_id": "P-9002",
        "age": 10 # Below standard reproductive age 12-55
    }
    res = client.post("/api/v1/patients", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["age"] == 10
    assert data["age_range_warning"] is not None
    assert "outside standard reproductive age range" in data["age_range_warning"]

# ==============================================================================
# 2. POST /patients/{id}/visits Tests
# ==============================================================================

def test_create_visit_zero_clinical_fields_rejected(client):
    # Accidental empty submission
    payload = {
        "visit_date": "2026-10-01",
        "observations": []
    }
    res = client.post("/api/v1/patients/P-0042/visits", json=payload)
    assert res.status_code == 422
    assert "at least one clinical parameter must be provided" in res.json()["detail"].lower()

def test_create_visit_out_of_order_date_rejected(client):
    # Patient P-0042 latest visit is in 2026-09-18
    # Attempting to insert an out-of-order visit with earlier date 2025-01-01
    payload = {
        "visit_date": "2025-01-01",
        "observations": [
            {
                "domain": "Metabolic",
                "parameter": "weight",
                "numericValue": 68.0,
                "unit": "kg",
                "source": "Clinician entry",
                "measurementStatus": "VALUE_PRESENT"
            }
        ]
    }
    res = client.post("/api/v1/patients/P-0042/visits", json=payload)
    assert res.status_code == 400
    assert "out-of-order visit rejected" in res.json()["detail"].lower()

def test_create_visit_duplicate_same_date_warning(client):
    # Patient P-9001 has no visits yet. Create first visit.
    v1_payload = {
        "visit_date": "2026-05-10",
        "observations": [
            {
                "domain": "Metabolic",
                "parameter": "weight",
                "numericValue": 65.0,
                "unit": "kg"
            }
        ]
    }
    res1 = client.post("/api/v1/patients/P-9001/visits", json=v1_payload)
    assert res1.status_code == 201

    # Same-day follow-up encounter on 2026-05-10
    v2_same_day = {
        "visit_date": "2026-05-10",
        "observations": [
            {
                "domain": "Metabolic",
                "parameter": "fasting_glucose",
                "numericValue": 92.0,
                "unit": "mg/dL"
            }
        ]
    }
    res2 = client.post("/api/v1/patients/P-9001/visits", json=v2_same_day)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["warning"] is not None
    assert "already exists for patient" in data2["warning"]

def test_create_visit_plausible_range_check_validation(client):
    # Biological impossibility test: e.g. BMI = 150.0 (valid range 10-80)
    payload = {
        "visit_date": "2026-11-01",
        "observations": [
            {
                "domain": "Metabolic",
                "parameter": "bmi",
                "numericValue": 150.0,
                "unit": "kg/m2"
            }
        ]
    }
    res = client.post("/api/v1/patients/P-9001/visits", json=payload)
    assert res.status_code == 422
    assert "plausibility check failed" in str(res.json()).lower()

def test_create_visit_structured_with_domain_completeness(client):
    # Patient P-0042 next chronological visit
    payload = {
        "visit_date": "2026-12-15",
        "observations": [
            {
                "domain": "Reproductive",
                "parameter": "cycle_length",
                "numericValue": 33.0,
                "unit": "days",
                "source": "Self report"
            },
            {
                "domain": "Reproductive",
                "parameter": "ovulation_signs",
                "numericValue": 1.0,
                "unit": "binary",
                "source": "Self report"
            },
            {
                "domain": "Metabolic",
                "parameter": "weight",
                "numericValue": 66.5,
                "unit": "kg",
                "source": "Clinician entry"
            },
            # Explicit NOT_APPLICABLE with reason code (e.g. hormonal contraception)
            {
                "domain": "Reproductive",
                "parameter": "cycle_variability_sd",
                "numericValue": None,
                "unit": "days",
                "measurementStatus": "NOT_APPLICABLE",
                "reasonCode": "hormonal_contraception"
            }
        ]
    }
    res = client.post("/api/v1/patients/P-0042/visits", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["visit_id"] == "v5-p-0042"
    assert data["total_observations_recorded"] == 4
    
    # Check immediate Section 3B completeness object
    assert "domain_completeness" in data
    rep_comp = data["domain_completeness"]["Reproductive"]
    assert "completeness_ratio" in rep_comp
    assert "missing_fields" in rep_comp

def test_process_visit_downstream_endpoint(client):
    # Explicit downstream trigger step (Section 5B step 5)
    res = client.post("/api/v1/patients/P-0042/visits/v5-p-0042/process")
    assert res.status_code == 200
    data = res.json()
    assert "domainScores" in data
    assert "deltas" in data
    assert "reasoningNarrative" in data
    # Deltas computed against V4
    weight_delta = next((d for d in data["deltas"] if d["parameter"] == "weight"), None)
    assert weight_delta is not None
    # Previous weight was 67.2, current is 66.5 -> delta -0.7 kg
    assert weight_delta["numericDelta"] == -0.7
