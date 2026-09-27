import pytest
from backend.services.delta_engine import DeltaEngine
from backend.models.observation import DomainObservation

@pytest.fixture
def delta_engine():
    return DeltaEngine()

def make_obs(param: str, domain: str, val: float, unit: str = "", visit_id: str = "v1"):
    return DomainObservation(
        id=f"obs-{param}-{visit_id}",
        visit_id=visit_id,
        domain=domain,
        parameter_name=param,
        numeric_value=val,
        text_value=str(val),
        unit=unit,
        date="2026-01-01",
        measurement_status="VALUE_PRESENT"
    )

def test_first_visit_produces_no_deltas(delta_engine):
    curr = [make_obs("weight", "Metabolic", 70.0, "kg")]
    deltas = delta_engine.compute_deltas("v1", curr, previous_observations=None)
    assert deltas == []

def test_missing_prior_parameter_marks_insufficient_history(delta_engine):
    curr = [make_obs("hba1c", "Metabolic", 5.6, "%", visit_id="v2")]
    prev = [make_obs("weight", "Metabolic", 68.0, "kg", visit_id="v1")]
    
    deltas = delta_engine.compute_deltas("v2", curr, previous_observations=prev)
    assert len(deltas) == 1
    d = deltas[0]
    assert d.parameter == "hba1c"
    assert d.status_tag == "insufficient_history"
    assert d.previous_value is None
    assert d.is_significant is False
    assert d.is_meaningful is False

def test_metabolic_domain_noise_vs_meaningful(delta_engine):
    # Weight: threshold 2.0 kg. 1.2 kg change is noise; 3.0 kg change is meaningful.
    prev = [make_obs("weight", "Metabolic", 70.0, "kg", visit_id="v1")]
    
    # Noise test
    curr_noise = [make_obs("weight", "Metabolic", 71.2, "kg", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert len(deltas_noise) == 1
    assert deltas_noise[0].is_meaningful is False
    assert deltas_noise[0].status_tag == "Stable"

    # Meaningful test
    curr_meaningful = [make_obs("weight", "Metabolic", 73.5, "kg", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_meaningful, prev)
    assert len(deltas_sig) == 1
    assert deltas_sig[0].is_meaningful is True
    assert deltas_sig[0].direction == "up"
    assert deltas_sig[0].status_tag in ["Threshold crossed", "Substantial shift"]

def test_reproductive_domain_noise_vs_meaningful(delta_engine):
    # Cycle variability SD: threshold 3.0 days.
    prev = [make_obs("cycle_variability_sd", "Reproductive", 6.0, "days", visit_id="v1")]
    
    curr_noise = [make_obs("cycle_variability_sd", "Reproductive", 7.5, "days", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert deltas_noise[0].is_meaningful is False

    curr_sig = [make_obs("cycle_variability_sd", "Reproductive", 11.0, "days", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_sig, prev)
    assert deltas_sig[0].is_meaningful is True
    assert deltas_sig[0].direction == "up"

def test_hyperandrogenism_domain_noise_vs_meaningful(delta_engine):
    # Total testosterone: threshold 0.10 ng/mL.
    prev = [make_obs("total_testosterone", "Hyperandrogenism", 0.50, "ng/mL", visit_id="v1")]

    curr_noise = [make_obs("total_testosterone", "Hyperandrogenism", 0.56, "ng/mL", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert deltas_noise[0].is_meaningful is False

    curr_sig = [make_obs("total_testosterone", "Hyperandrogenism", 0.65, "ng/mL", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_sig, prev)
    assert deltas_sig[0].is_meaningful is True

def test_psychological_domain_noise_vs_meaningful(delta_engine):
    # PHQ-9: threshold 3.0 points.
    prev = [make_obs("phq9_score", "Psychological", 8.0, "score", visit_id="v1")]

    curr_noise = [make_obs("phq9_score", "Psychological", 10.0, "score", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert deltas_noise[0].is_meaningful is False

    curr_sig = [make_obs("phq9_score", "Psychological", 13.0, "score", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_sig, prev)
    assert deltas_sig[0].is_meaningful is True
    assert deltas_sig[0].status_tag in ["Threshold crossed", "Substantial shift"]

def test_sleep_domain_noise_vs_meaningful(delta_engine):
    # Sleep hours: threshold 1.0 hr.
    prev = [make_obs("sleep_hours", "Sleep", 7.0, "hours", visit_id="v1")]

    curr_noise = [make_obs("sleep_hours", "Sleep", 6.5, "hours", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert deltas_noise[0].is_meaningful is False

    curr_sig = [make_obs("sleep_hours", "Sleep", 5.2, "hours", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_sig, prev)
    assert deltas_sig[0].is_meaningful is True
    assert deltas_sig[0].direction == "down"

def test_lifestyle_domain_noise_vs_meaningful(delta_engine):
    # Activity minutes/week: threshold 30.0 min.
    prev = [make_obs("activity_minutes_week", "Lifestyle", 120.0, "min/week", visit_id="v1")]

    curr_noise = [make_obs("activity_minutes_week", "Lifestyle", 105.0, "min/week", visit_id="v2")]
    deltas_noise = delta_engine.compute_deltas("v2", curr_noise, prev)
    assert deltas_noise[0].is_meaningful is False

    curr_sig = [make_obs("activity_minutes_week", "Lifestyle", 60.0, "min/week", visit_id="v2")]
    deltas_sig = delta_engine.compute_deltas("v2", curr_sig, prev)
    assert deltas_sig[0].is_meaningful is True
    assert deltas_sig[0].direction == "down"
