import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.models.patient import Patient
from backend.models.visit import Visit
from backend.models.observation import DomainObservation
from backend.services.synthetic_data import seed_synthetic_patients

@pytest.fixture
def db_session():
    # In-memory SQLite for test isolation
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

def test_models_and_synthetic_seeding(db_session):
    patients = seed_synthetic_patients(db_session, force_recreate=True)
    assert len(patients) == 5
    
    # Check Phenotype A patient (P-0042)
    p0042 = db_session.query(Patient).filter(Patient.id == "P-0042").first()
    assert p0042 is not None
    assert "Phenotype A" in p0042.synthetic_cohort_label
    assert len(p0042.visits) == 4

    # Verify visit ordering
    visit_numbers = [v.visit_number for v in p0042.visits]
    assert visit_numbers == [1, 2, 3, 4]

    # Verify observations in visit 1
    v1 = p0042.visits[0]
    obs = db_session.query(DomainObservation).filter(DomainObservation.visit_id == v1.id).all()
    assert len(obs) > 20
    
    # Check that computed HOMA-IR was created
    homa_obs = next((o for o in obs if o.parameter_name == "homa_ir"), None)
    assert homa_obs is not None
    assert homa_obs.numeric_value > 0.0
    assert homa_obs.domain == "Metabolic"

def test_tri_state_missing_data_storage(db_session):
    seed_synthetic_patients(db_session, force_recreate=True)
    
    # Check P-0056 (Sparse / Missing Data Cohort)
    p0056 = db_session.query(Patient).filter(Patient.id == "P-0056").first()
    assert p0056 is not None
    assert len(p0056.visits) == 3

    # Visit 2 has unmeasured fields explicitly stored with reason codes
    v2 = p0056.visits[1]
    unmeasured_obs = db_session.query(DomainObservation).filter(
        DomainObservation.visit_id == v2.id,
        DomainObservation.measurement_status == "NOT_MEASURED"
    ).all()
    
    assert len(unmeasured_obs) > 0
    # Check reason code
    fg_obs = next((o for o in unmeasured_obs if o.parameter_name == "fasting_glucose"), None)
    assert fg_obs is not None
    assert fg_obs.reason_code == "lab_not_ordered"
    assert fg_obs.numeric_value is None

    # Visit 3 has partial missingness with reason code
    v3 = p0056.visits[2]
    dheas_obs = db_session.query(DomainObservation).filter(
        DomainObservation.visit_id == v3.id,
        DomainObservation.parameter_name == "dheas"
    ).first()
    assert dheas_obs is not None
    assert dheas_obs.measurement_status == "NOT_MEASURED"
    assert dheas_obs.reason_code == "reagent_shortage"
