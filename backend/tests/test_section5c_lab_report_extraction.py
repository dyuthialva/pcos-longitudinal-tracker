import pytest
from backend.services.extraction_service import ExtractionService
from backend.schemas.observation import ObservationCreate
from backend.schemas.common import DomainType, MeasurementStatus

def test_alias_mapping_and_unit_conversion():
    extractor = ExtractionService()
    
    # 1. Alias resolution
    assert extractor.map_parameter_label("Total Testosterone") == "total_testosterone"
    assert extractor.map_parameter_label("S. Testosterone") == "total_testosterone"
    assert extractor.map_parameter_label("Glycated Hemoglobin") == "hba1c"
    assert extractor.map_parameter_label("Fasting Blood Sugar") == "fasting_glucose"
    assert extractor.map_parameter_label("FBS") == "fasting_glucose"
    assert extractor.map_parameter_label("DHEA Sulfate") == "dheas"

    # 2. Canonical unit conversion
    # Glucose: 6.0 mmol/L -> ~108.1 mg/dL
    val, unit, recognized = extractor.convert_to_canonical_unit("fasting_glucose", 6.0, "mmol/L")
    assert recognized is True
    assert unit == "mg/dL"
    assert 108.0 < val < 108.2

    # Testosterone: 2.5 nmol/L -> ~0.72 ng/mL
    val, unit, recognized = extractor.convert_to_canonical_unit("total_testosterone", 2.5, "nmol/L")
    assert recognized is True
    assert unit == "ng/mL"
    assert 0.70 < val < 0.75

def test_fail_fast_on_unusable_text(client):
    # Upload an empty/corrupted file
    resp = client.post(
        "/api/v1/extraction/lab-pdf",
        files={"file": ("empty.pdf", b"garbage", "application/pdf")}
    )
    # Should fail fast with 422 or 500 error rather than sending garbage
    assert resp.status_code in [422, 500]
    detail = resp.json().get("detail", "")
    assert "Could not read" in detail or "failed" in detail

def test_biological_range_flagging(client):
    # Pass text with an OCR misread producing biologically impossible HbA1c = 950
    raw_text = "Fasting Glucose: 95 mg/dL\nHbA1c: 950 %\nTotal Testosterone: 0.65 ng/mL\nDate: 2026-09-20"
    resp = client.post(
        "/api/v1/extraction/lab-pdf",
        data={"raw_text": raw_text}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_clinician_review"] is True
    
    # Check that HbA1c was flagged
    flagged = data["flagged_for_review"]
    hba1c_flags = [f for f in flagged if f.get("mapped_field") == "hba1c"]
    assert len(hba1c_flags) > 0
    assert "outside biological plausibility" in hba1c_flags[0]["reason"].lower()

def test_multiple_dates_warning(client):
    raw_text = (
        "Collection Date: 2025-06-15\n"
        "Report Date: 2026-09-20\n"
        "Fasting Glucose: 98 mg/dL\n"
        "HbA1c: 5.5 %"
    )
    resp = client.post(
        "/api/v1/extraction/lab-pdf",
        data={"raw_text": raw_text}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["dates_detected"]) >= 2
    assert data["date_warning"] is not None
    assert "Multiple distinct dates detected" in data["date_warning"]

def test_duplicate_parameter_detection(client):
    raw_text = (
        "Fasting Glucose: 110 mg/dL (Preliminary)\n"
        "Fasting Glucose: 104 mg/dL (Final Repeat)\n"
        "HbA1c: 5.7 %"
    )
    resp = client.post(
        "/api/v1/extraction/lab-pdf",
        data={"raw_text": raw_text}
    )
    assert resp.status_code == 200
    data = resp.json()
    # Check that duplicate was flagged and final value retained
    flagged = data["flagged_for_review"]
    glucose_dup = [f for f in flagged if "duplicate" in f.get("reason", "").lower()]
    assert len(glucose_dup) > 0
    
    # In extracted values, Fasting Glucose should be retained
    fg_values = [v for v in data["extracted_values"] if v["mapped_field"] == "fasting_glucose"]
    assert len(fg_values) == 1
    assert fg_values[0]["value"] == 104.0

def test_confirm_extraction_to_visit_endpoint(client):
    # 1. Create a patient
    p_resp = client.post("/api/v1/patients", json={
        "id": "P-TEST-LAB-01",
        "synthetic_cohort_label": "Phenotype A Test",
        "age": 29
    })
    assert p_resp.status_code == 201

    # 2. Create initial visit
    v_resp = client.post("/api/v1/patients/P-TEST-LAB-01/visits", json={
        "visit_date": "2026-09-20",
        "source_type": "Initial Intake",
        "observations": [
            {
                "domain": "Metabolic",
                "parameter": "BMI",
                "numeric_value": 26.5,
                "unit": "kg/m2",
                "measurement_status": "VALUE_PRESENT"
            }
        ]
    })
    assert v_resp.status_code == 201
    visit_id = v_resp.json()["visit_id"]

    # 3. Confirm lab extraction into this visit
    confirm_payload = {
        "extraction_id": "test-extr-123",
        "source_method": "text_pdf",
        "recompute_scores": True,
        "confirmed_observations": [
            {
                "domain": "Metabolic",
                "parameter": "Fasting Glucose",
                "numeric_value": 102.0,
                "unit": "mg/dL",
                "measurement_status": "VALUE_PRESENT",
                "flag": "HIGH"
            },
            {
                "domain": "Hyperandrogenism",
                "parameter": "Total Testosterone",
                "numeric_value": 0.74,
                "unit": "ng/mL",
                "measurement_status": "VALUE_PRESENT"
            }
        ]
    }

    c_resp = client.post(
        f"/api/v1/patients/P-TEST-LAB-01/visits/{visit_id}/confirm-extraction",
        json=confirm_payload
    )
    assert c_resp.status_code == 200
    res_data = c_resp.json()
    assert res_data["confirmed_observations_count"] == 2
    assert res_data["source_method"] == "text_pdf"
    
    # Verify observations committed in visit record
    obs_names = [o["parameter"] for o in res_data["visit"]["observations"]]
    assert "Fasting Glucose" in obs_names
    assert "Total Testosterone" in obs_names
