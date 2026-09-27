import pytest
from backend.services.scoring_engine import ScoringEngine
from backend.models.observation import DomainObservation
from backend.models.delta import ClinicalDeltaModel
from backend.schemas.common import AttentionBand, ConfidenceLevel

@pytest.fixture
def scoring_engine():
    return ScoringEngine()

def make_obs(param: str, domain: str, val: float, unit: str = "", visit_id: str = "v1"):
    return DomainObservation(
        id=f"obs-{param}",
        visit_id=visit_id,
        domain=domain,
        parameter_name=param,
        numeric_value=val,
        text_value=str(val),
        unit=unit,
        date="2026-01-01",
        measurement_status="VALUE_PRESENT"
    )

def test_hand_calculated_scoring_formula(scoring_engine):
    """
    Validates hand-calculated scoring math directly:
    score = 0.5*severity + 0.3*trend + 0.2*symptoms
    """
    # Create complete psychological observations
    # PHQ-9 = 12 (Moderate -> severity 65.0)
    # GAD-7 = 11 (Moderate -> severity 65.0)
    # severity = 65.0, symptoms = 65.0
    obs = [
        make_obs("phq9_score", "Psychological", 12.0),
        make_obs("gad7_score", "Psychological", 11.0),
    ]

    # Neutral delta (no change -> trend = 50.0)
    deltas = [
        ClinicalDeltaModel(
            id="d1", visit_id="v2", domain="Psychological", parameter="phq9_score",
            previous_value="12.0", current_value="12.0", delta_display="0.0",
            numeric_delta=0.0, is_significant=False
        )
    ]

    # Hand calculation:
    # sev = 65.0, trend = 50.0, sym = 65.0
    # Expected score = 0.5 * 65.0 + 0.3 * 50.0 + 0.2 * 65.0
    # = 32.5 + 15.0 + 13.0 = 60.5
    scores = scoring_engine.compute_domain_scores("v2", obs, deltas, is_first_visit=False)
    psych_score = scores["Psychological"]
    
    assert psych_score.score is not None
    assert round(psych_score.score, 1) == 60.5
    assert psych_score.band == AttentionBand.ModerateHigh.value
    assert psych_score.severity_component == 65.0
    assert psych_score.trend_component == 50.0
    assert psych_score.symptoms_component == 65.0

def test_first_visit_renormalizes_weights_without_trend(scoring_engine):
    """
    Section 3B: Handle first-ever visit as distinct state.
    Trend term dropped, renormalized weights used, computed_without_trend = True.
    """
    obs = [
        make_obs("phq9_score", "Psychological", 12.0),
        make_obs("gad7_score", "Psychological", 11.0),
    ]
    # Hand calculation with baseline weights (0.714 sev + 0.286 sym):
    # sev = 65.0, sym = 65.0
    # Expected score = 0.714 * 65.0 + 0.286 * 65.0 = 65.0
    scores = scoring_engine.compute_domain_scores("v1", obs, deltas=[], is_first_visit=True)
    psych_score = scores["Psychological"]

    assert psych_score.score is not None
    assert round(psych_score.score, 1) == 65.0
    assert psych_score.trend_component is None
    assert psych_score.computed_without_trend is True

def test_section_3b_missing_data_completeness_rules(scoring_engine):
    """
    Section 3B Mandatory Tests:
    (a) domain with all fields present scores normally with confidence 'full'
    (b) domain just above threshold scores with confidence 'partial' and lists missing fields
    (c) domain below threshold returns 'insufficient_data' and no numeric score
    """
    # (a) Full completeness in Reproductive (all 4 expected fields present)
    full_reproductive_obs = [
        make_obs("cycle_length", "Reproductive", 32.0),
        make_obs("cycle_variability_sd", "Reproductive", 2.5),
        make_obs("missed_periods_count", "Reproductive", 0.0),
        make_obs("ovulation_signs", "Reproductive", 1.0),
    ]
    scores_full = scoring_engine.compute_domain_scores("v1", full_reproductive_obs, deltas=[], is_first_visit=True)
    rep_full = scores_full["Reproductive"]
    assert rep_full.completeness_ratio == 1.0
    assert rep_full.confidence == ConfidenceLevel.Full.value
    assert rep_full.missing_fields == []
    assert rep_full.is_insufficient_data is False
    assert rep_full.score is not None

    # (b) Partial completeness in Hyperandrogenism: 5 of 7 expected fields present (ratio = 5/7 = 0.714 >= 0.60)
    # Missing: dheas, shbg
    partial_hyper_obs = [
        make_obs("total_testosterone", "Hyperandrogenism", 0.65),
        make_obs("free_testosterone", "Hyperandrogenism", 6.2),
        make_obs("hirsutism_mfg_score", "Hyperandrogenism", 9.0),
        make_obs("acne_severity", "Hyperandrogenism", 2.0),
        make_obs("hair_loss_severity", "Hyperandrogenism", 1.0),
    ]
    scores_partial = scoring_engine.compute_domain_scores("v1", partial_hyper_obs, deltas=[], is_first_visit=True)
    hyper_part = scores_partial["Hyperandrogenism"]
    assert hyper_part.completeness_ratio >= 0.60
    assert hyper_part.confidence == ConfidenceLevel.Partial.value
    assert "dheas" in hyper_part.missing_fields
    assert "shbg" in hyper_part.missing_fields
    assert hyper_part.is_insufficient_data is False
    assert hyper_part.score is not None

    # (c) Insufficient Data in Metabolic: 2 of 12 fields present (ratio = 2/12 = 0.167 < 0.60 threshold)
    # Even if available values look completely normal!
    insufficient_metabolic_obs = [
        make_obs("weight", "Metabolic", 62.0),
        make_obs("waist_circumference", "Metabolic", 74.0),
    ]
    scores_insuff = scoring_engine.compute_domain_scores("v1", insufficient_metabolic_obs, deltas=[], is_first_visit=True)
    metab_insuff = scores_insuff["Metabolic"]
    assert metab_insuff.completeness_ratio < 0.60
    assert metab_insuff.confidence == ConfidenceLevel.InsufficientData.value
    assert metab_insuff.band == AttentionBand.InsufficientData.value
    assert metab_insuff.score is None
    assert metab_insuff.is_insufficient_data is True
    assert metab_insuff.insufficient_reason is not None
    assert "fasting_glucose" in metab_insuff.missing_fields

def test_guideline_citations_exposed(scoring_engine):
    citations = scoring_engine.get_guideline_citations()
    assert "Reproductive" in citations
    assert "2023 International PCOS Guideline" in citations["Reproductive"]
    assert "Hyperandrogenism" in citations
    assert "Metabolic" in citations
