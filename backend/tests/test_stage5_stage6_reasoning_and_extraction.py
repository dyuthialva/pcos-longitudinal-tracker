import pytest
from backend.services.reasoning_service import ReasoningService
from backend.services.extraction_service import ExtractionService

def test_reasoning_number_validation_detects_hallucinations():
    svc = ReasoningService(api_key="") # offline mode for unit test

    input_payload = {
        "visit_id": "v2",
        "scores": {"Metabolic": {"score": 65.0}},
        "deltas": [
            {"parameter": "weight", "numeric_delta": 3.5, "current_value": "71.5 kg", "previous_value": "68.0 kg"}
        ],
        "evidence": {"Metabolic": [{"parameter": "hba1c", "value": 5.8}]}
    }

    # Narrative citing valid numbers (68.0, 71.5, 3.5, 5.8)
    valid_narrative = (
        "Weight increased from 68.0 kg to 71.5 kg (+3.5 kg), with HbA1c at 5.8%. "
        "These observations may be consistent with elevated metabolic attention."
    )
    is_valid, hallucinated = svc.validate_narrative_numbers(valid_narrative, input_payload)
    assert is_valid is True
    assert len(hallucinated) == 0

    # Narrative with a hallucinated laboratory value (e.g. invented testosterone 99.4)
    hallucinated_narrative = (
        "Weight increased to 71.5 kg and testosterone spiked to 99.4 ng/mL with fasting glucose of 188.0 mg/dL."
    )
    is_valid, hallucinated = svc.validate_narrative_numbers(hallucinated_narrative, input_payload)
    assert is_valid is False
    assert 99.4 in hallucinated
    assert 188.0 in hallucinated

def test_reasoning_deterministic_fallback():
    svc = ReasoningService(api_key="")
    payload = {
        "visit_id": "v2",
        "is_first_visit": False,
        "deltas": [
            {"parameter": "weight", "delta_display": "+3.5 kg", "is_meaningful": True}
        ],
        "data_completeness": {
            "Metabolic": {"confidence": "insufficient_data"}
        }
    }
    resp = svc.generate_reasoning(payload)
    assert resp.validation_passed is True
    assert "weight (+3.5 kg)" in resp.narrative
    assert "Insufficient data recorded for Metabolic" in resp.narrative
    # Check that tentative language was used
    assert "may be consistent with" in resp.narrative

def test_extraction_rule_based_parser():
    svc = ExtractionService(api_key="")
    sample_lab_text = """
    COMPREHENSIVE PCOS ENDOCRINE PANEL
    Patient: Synthetic Test
    Date: 2026-09-20
    
    Test Name                Result     Reference Range      Units
    Total Testosterone       0.72       0.10 - 0.50          ng/mL
    Free Testosterone        7.8        1.0 - 5.0            pg/mL
    DHEA-Sulfate             335        65 - 270             ug/dL
    SHBG                     22         25 - 120             nmol/L
    Fasting Glucose          104        70 - 99              mg/dL
    Fasting Insulin          19.0       2.0 - 12.0           uIU/mL
    Hemoglobin A1c           5.8        4.0 - 5.6            %
    Triglycerides            175        < 150                mg/dL
    HDL Cholesterol          44         > 50                 mg/dL
    """
    extracted = svc.rule_based_regex_extractor(sample_lab_text)
    params_found = {item.parameter: item.numeric_value for item in extracted}

    assert "total_testosterone" in params_found
    assert params_found["total_testosterone"] == 0.72
    assert "free_testosterone" in params_found
    assert params_found["free_testosterone"] == 7.8
    assert "fasting_glucose" in params_found
    assert params_found["fasting_glucose"] == 104.0
    assert "fasting_insulin" in params_found
    assert params_found["fasting_insulin"] == 19.0
    assert "hba1c" in params_found
    assert params_found["hba1c"] == 5.8
