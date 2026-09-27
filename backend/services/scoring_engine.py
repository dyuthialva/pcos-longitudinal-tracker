import uuid
from typing import List, Dict, Any, Optional, Tuple
from backend.config.settings import load_scoring_config
from backend.models.observation import DomainObservation
from backend.models.delta import ClinicalDeltaModel
from backend.models.score import DomainScoreModel
from backend.schemas.common import DataCompletenessInfo, ConfidenceLevel, AttentionBand, DomainType

class ScoringEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_scoring_config()
        self.weights = self.config.get("weights", {"severity": 0.5, "trend": 0.3, "symptoms": 0.2})
        self.baseline_weights = self.config.get("baseline_weights_no_trend", {"severity": 0.714, "symptoms": 0.286})
        self.completeness_threshold = self.config.get("completeness", {}).get("threshold_ratio", 0.60)
        self.domains_config = self.config.get("domains", {})
        
        # Population profile for ethnicity-specific cutoffs (e.g. Asian vs WHO)
        pop_cfg = self.config.get("population_settings", {})
        active_prof = pop_cfg.get("active_profile", "asian_south_asian")
        self.pop_profile = pop_cfg.get("profiles", {}).get(active_prof, {
            "bmi_overweight": 23.0,
            "bmi_obese": 27.5,
            "waist_circumference_threshold_cm": 80.0
        })

    def get_guideline_citations(self) -> Dict[str, str]:
        citations = {}
        for d_name, d_cfg in self.domains_config.items():
            if "citation" in d_cfg:
                citations[d_name] = d_cfg["citation"]
        return citations

    def evaluate_completeness(
        self,
        domain: str,
        observations: List[DomainObservation]
    ) -> DataCompletenessInfo:
        expected = self.domains_config.get(domain, {}).get("expected_fields", [])
        if not expected:
            return DataCompletenessInfo(
                domain=DomainType(domain) if domain in DomainType.__members__ else DomainType.Other,
                completeness_ratio=1.0,
                confidence=ConfidenceLevel.Full,
                missing_fields=[],
                fields_present_count=0,
                fields_expected_count=0
            )

        present_params = {
            obs.parameter_name for obs in observations
            if obs.domain == domain and obs.measurement_status == "VALUE_PRESENT" and obs.numeric_value is not None
        }

        missing = [f for f in expected if f not in present_params]
        present_count = len(expected) - len(missing)
        ratio = round(present_count / len(expected), 3)

        if ratio < self.completeness_threshold:
            confidence = ConfidenceLevel.InsufficientData
        elif ratio < 1.0:
            confidence = ConfidenceLevel.Partial
        else:
            confidence = ConfidenceLevel.Full

        return DataCompletenessInfo(
            domain=DomainType(domain) if domain in DomainType.__members__ else DomainType.Other,
            completeness_ratio=ratio,
            confidence=confidence,
            missing_fields=missing,
            fields_present_count=present_count,
            fields_expected_count=len(expected)
        )

    def compute_reproductive_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "cycle_length" in data:
            cl = data["cycle_length"]
            if cl < 21:
                sev_components.append(70.0) # Polymonorrhea
            elif cl <= 35:
                sev_components.append(10.0) # Normal
            elif cl <= 45:
                sev_components.append(50.0) # Mild oligomenorrhea
            elif cl <= 90:
                sev_components.append(75.0) # Moderate oligomenorrhea
            else:
                sev_components.append(95.0) # Amenorrhea

        if "cycle_variability_sd" in data:
            sd = data["cycle_variability_sd"]
            if sd <= 3.0:
                sev_components.append(10.0)
            elif sd <= 7.0:
                sev_components.append(45.0)
            elif sd <= 12.0:
                sev_components.append(70.0)
            else:
                sev_components.append(90.0)

        if "missed_periods_count" in data:
            mp = data["missed_periods_count"]
            if mp <= 1:
                sev_components.append(10.0)
            elif mp <= 3:
                sev_components.append(50.0)
            else:
                sev_components.append(85.0)

        severity = sum(sev_components) / len(sev_components) if sev_components else 20.0
        
        # Symptoms: ovulation signs absent (0) indicates higher symptom burden
        symptoms = 20.0
        if "ovulation_signs" in data:
            ov = data["ovulation_signs"]
            symptoms = 75.0 if ov <= 0.0 else 15.0

        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_hyperandrogenism_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "total_testosterone" in data:
            tt = data["total_testosterone"]
            if tt <= 0.40:
                sev_components.append(15.0)
            elif tt <= 0.50:
                sev_components.append(40.0)
            elif tt <= 0.70:
                sev_components.append(70.0)
            else:
                sev_components.append(95.0)

        if "free_testosterone" in data:
            ft = data["free_testosterone"]
            if ft <= 3.0:
                sev_components.append(15.0)
            elif ft <= 5.0:
                sev_components.append(45.0)
            elif ft <= 7.0:
                sev_components.append(75.0)
            else:
                sev_components.append(95.0)

        if "dheas" in data:
            dh = data["dheas"]
            if dh <= 250:
                sev_components.append(15.0)
            elif dh <= 300:
                sev_components.append(50.0)
            else:
                sev_components.append(85.0)

        if "shbg" in data:
            shbg = data["shbg"]
            if shbg >= 35.0:
                sev_components.append(15.0)
            elif shbg >= 25.0:
                sev_components.append(50.0)
            else:
                sev_components.append(80.0)

        if "hirsutism_mfg_score" in data:
            mfg = data["hirsutism_mfg_score"]
            if mfg < 4.0:
                sev_components.append(10.0)
            elif mfg <= 8.0:
                sev_components.append(50.0)
            elif mfg <= 15.0:
                sev_components.append(75.0)
            else:
                sev_components.append(95.0)

        severity = sum(sev_components) / len(sev_components) if sev_components else 20.0

        # Symptoms: acne severity and hair loss
        sym_components = []
        if "acne_severity" in data:
            sym_components.append(data["acne_severity"] * 25.0) # 0-4 grade
        if "hair_loss_severity" in data:
            sym_components.append(data["hair_loss_severity"] * 33.3) # 0-3 grade
        symptoms = sum(sym_components) / len(sym_components) if sym_components else 20.0

        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_metabolic_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "fasting_glucose" in data:
            fg = data["fasting_glucose"]
            if fg < 100:
                sev_components.append(15.0)
            elif fg <= 125:
                sev_components.append(65.0)
            else:
                sev_components.append(95.0)

        if "fasting_insulin" in data:
            fi = data["fasting_insulin"]
            if fi < 10.0:
                sev_components.append(15.0)
            elif fi <= 15.0:
                sev_components.append(50.0)
            elif fi <= 20.0:
                sev_components.append(75.0)
            else:
                sev_components.append(95.0)

        if "homa_ir" in data:
            homa = data["homa_ir"]
            if homa < 2.0:
                sev_components.append(15.0)
            elif homa <= 2.5:
                sev_components.append(45.0)
            elif homa <= 3.8:
                sev_components.append(75.0)
            else:
                sev_components.append(95.0)

        if "hba1c" in data:
            a1c = data["hba1c"]
            if a1c < 5.7:
                sev_components.append(15.0)
            elif a1c <= 6.4:
                sev_components.append(65.0)
            else:
                sev_components.append(95.0)

        if "bmi" in data:
            bmi = data["bmi"]
            # Ethnicity-specific cutoff check (Asian vs WHO standard)
            overweight_cut = self.pop_profile.get("bmi_overweight", 23.0)
            obese_cut = self.pop_profile.get("bmi_obese", 27.5)
            if bmi < overweight_cut:
                sev_components.append(15.0)
            elif bmi < obese_cut:
                sev_components.append(55.0)
            else:
                sev_components.append(85.0)

        if "waist_circumference" in data:
            wc = data["waist_circumference"]
            wc_cut = self.pop_profile.get("waist_circumference_threshold_cm", 80.0)
            if wc < wc_cut:
                sev_components.append(15.0)
            elif wc <= (wc_cut + 8.0):
                sev_components.append(55.0)
            else:
                sev_components.append(85.0)

        if "systolic_bp" in data:
            sbp = data["systolic_bp"]
            if sbp < 120:
                sev_components.append(10.0)
            elif sbp <= 129:
                sev_components.append(35.0)
            elif sbp <= 139:
                sev_components.append(65.0)
            else:
                sev_components.append(90.0)

        if "triglycerides" in data:
            tg = data["triglycerides"]
            if tg < 150:
                sev_components.append(15.0)
            elif tg <= 200:
                sev_components.append(55.0)
            else:
                sev_components.append(85.0)

        if "hdl" in data:
            hdl = data["hdl"]
            if hdl >= 50.0:
                sev_components.append(10.0)
            else:
                sev_components.append(65.0)

        severity = sum(sev_components) / len(sev_components) if sev_components else 20.0
        
        # Symptoms: metabolic fatigue / appetite instability correlates with higher insulin/glucose
        symptoms = 30.0
        if "fasting_insulin" in data and data["fasting_insulin"] > 16.0:
            symptoms = 65.0

        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_lifestyle_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "activity_minutes_week" in data:
            act = data["activity_minutes_week"]
            if act >= 150:
                sev_components.append(10.0)
            elif act >= 90:
                sev_components.append(40.0)
            elif act >= 60:
                sev_components.append(65.0)
            else:
                sev_components.append(90.0)

        if "diet_quality_score" in data:
            diet = data["diet_quality_score"]
            if diet >= 8.0:
                sev_components.append(10.0)
            elif diet >= 5.0:
                sev_components.append(45.0)
            else:
                sev_components.append(85.0)

        if "smoking_status" in data:
            sm = data["smoking_status"]
            sev_components.append(10.0 if sm == 0 else (35.0 if sm == 1 else 75.0))

        if "alcohol_drinks_week" in data:
            alc = data["alcohol_drinks_week"]
            sev_components.append(10.0 if alc <= 2 else (40.0 if alc <= 6 else 80.0))

        severity = sum(sev_components) / len(sev_components) if sev_components else 20.0
        # Subjective difficulty adhering to diet/exercise
        symptoms = severity * 0.9
        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_psychological_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "phq9_score" in data:
            p = data["phq9_score"]
            if p < 5:
                sev_components.append(10.0)
            elif p <= 9:
                sev_components.append(35.0)
            elif p <= 14:
                sev_components.append(65.0)
            elif p <= 19:
                sev_components.append(85.0)
            else:
                sev_components.append(95.0)

        if "gad7_score" in data:
            g = data["gad7_score"]
            if g < 5:
                sev_components.append(10.0)
            elif g <= 9:
                sev_components.append(35.0)
            elif g <= 14:
                sev_components.append(65.0)
            else:
                sev_components.append(90.0)

        severity = sum(sev_components) / len(sev_components) if sev_components else 15.0
        # Symptoms match affective questionnaire scores directly
        symptoms = severity
        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_sleep_severity_and_symptoms(self, data: Dict[str, float]) -> Tuple[float, float]:
        sev_components = []
        if "sleep_hours" in data:
            sh = data["sleep_hours"]
            if sh >= 7.0:
                sev_components.append(10.0)
            elif sh >= 6.0:
                sev_components.append(45.0)
            else:
                sev_components.append(85.0)

        if "snoring_or_apnea_signs" in data:
            sn = data["snoring_or_apnea_signs"]
            if sn == 0:
                sev_components.append(10.0)
            elif sn == 1:
                sev_components.append(40.0)
            elif sn == 2:
                sev_components.append(70.0)
            else:
                sev_components.append(95.0)

        if "daytime_sleepiness_epworth" in data:
            ep = data["daytime_sleepiness_epworth"]
            if ep < 8:
                sev_components.append(10.0)
            elif ep <= 10:
                sev_components.append(40.0)
            else:
                sev_components.append(80.0)

        severity = sum(sev_components) / len(sev_components) if sev_components else 20.0
        
        # Symptoms: subjective sleep quality (1 poor to 10 optimal)
        symptoms = 30.0
        if "sleep_quality_score" in data:
            sq = data["sleep_quality_score"]
            symptoms = max(0.0, (10.0 - sq) * 10.0)

        return min(max(severity, 0.0), 100.0), min(max(symptoms, 0.0), 100.0)

    def compute_trend_from_deltas(self, domain: str, deltas: List[ClinicalDeltaModel]) -> float:
        """
        Computes trend score (0 to 100) based on deltas in this domain.
        50.0 is stable / neutral.
        Worsening shifts drive score toward 100 (high attention needed).
        Improving shifts drive score toward 0 (low attention needed).
        """
        domain_deltas = [d for d in deltas if d.domain == domain and d.numeric_delta is not None]
        if not domain_deltas:
            return 50.0 # Neutral trend

        trend_shifts = []
        for d in domain_deltas:
            nd = d.numeric_delta
            param = d.parameter

            # Beneficial when increasing: activity_minutes_week, diet_quality_score, shbg, hdl, sleep_hours, sleep_quality_score
            beneficial_increase = param in [
                "activity_minutes_week", "diet_quality_score", "shbg", "hdl",
                "sleep_hours", "sleep_quality_score"
            ]

            if abs(nd) < 0.001 or not d.is_significant:
                trend_shifts.append(50.0)
            elif (nd > 0 and beneficial_increase) or (nd < 0 and not beneficial_increase):
                # Clinically improving!
                shift = 30.0 if d.status_severity == "moderate" else 20.0
                trend_shifts.append(shift)
            else:
                # Clinically worsening!
                shift = 70.0 if d.status_severity == "moderate" else 85.0
                trend_shifts.append(shift)

        return sum(trend_shifts) / len(trend_shifts) if trend_shifts else 50.0

    def map_score_to_band(self, score: Optional[float], is_insufficient: bool) -> AttentionBand:
        if is_insufficient or score is None:
            return AttentionBand.InsufficientData
        if score < 30.0:
            return AttentionBand.Low
        elif score < 55.0:
            return AttentionBand.Moderate
        elif score < 75.0:
            return AttentionBand.ModerateHigh
        else:
            return AttentionBand.High

    def compute_domain_scores(
        self,
        visit_id: str,
        observations: List[DomainObservation],
        deltas: List[ClinicalDeltaModel],
        is_first_visit: bool = False
    ) -> Dict[str, DomainScoreModel]:
        """
        Computes attention scores across the 6 primary domains:
        Reproductive, Hyperandrogenism, Metabolic, Lifestyle, Psychological, Sleep.
        Strictly enforces Section 3B missing data handling.
        """
        results: Dict[str, DomainScoreModel] = {}
        target_domains = ["Reproductive", "Hyperandrogenism", "Metabolic", "Lifestyle", "Psychological", "Sleep"]

        obs_by_domain: Dict[str, Dict[str, float]] = {d: {} for d in target_domains}
        for o in observations:
            if o.domain in target_domains and o.measurement_status == "VALUE_PRESENT" and o.numeric_value is not None:
                obs_by_domain[o.domain][o.parameter_name] = o.numeric_value

        for domain in target_domains:
            # 1. Section 3B: Completeness Check
            completeness = self.evaluate_completeness(domain, observations)
            domain_obs_list = [o for o in observations if o.domain == domain]
            domain_deltas = [d for d in deltas if d.domain == domain]
            meaningful_count = sum(1 for d in domain_deltas if d.is_significant)
            data_dict = obs_by_domain[domain]

            # If completeness is below threshold, return 'Insufficient Data' and NO numeric score!
            if completeness.completeness_ratio < self.completeness_threshold:
                score_model = DomainScoreModel(
                    id=f"score-{uuid.uuid4().hex[:12]}",
                    visit_id=visit_id,
                    domain=domain,
                    score=None,
                    band=AttentionBand.InsufficientData.value,
                    severity_component=None,
                    trend_component=None,
                    symptoms_component=None,
                    completeness_ratio=completeness.completeness_ratio,
                    confidence=ConfidenceLevel.InsufficientData.value,
                    missing_fields=completeness.missing_fields,
                    is_insufficient_data=True,
                    insufficient_reason=(
                        f"Only {completeness.fields_present_count}/{completeness.fields_expected_count} "
                        f"({completeness.completeness_ratio*100:.0f}%) parameters measured. "
                        f"Minimum {self.completeness_threshold*100:.0f}% required."
                    ),
                    contributing_parameters=list(data_dict.keys()),
                    meaningful_deltas_count=meaningful_count,
                    observation_count=len(domain_obs_list),
                    weights_used={},
                    computed_without_trend=is_first_visit
                )
                results[domain] = score_model
                continue

            # 2. Compute Severity & Symptoms
            if domain == "Reproductive":
                sev, sym = self.compute_reproductive_severity_and_symptoms(data_dict)
            elif domain == "Hyperandrogenism":
                sev, sym = self.compute_hyperandrogenism_severity_and_symptoms(data_dict)
            elif domain == "Metabolic":
                sev, sym = self.compute_metabolic_severity_and_symptoms(data_dict)
            elif domain == "Lifestyle":
                sev, sym = self.compute_lifestyle_severity_and_symptoms(data_dict)
            elif domain == "Psychological":
                sev, sym = self.compute_psychological_severity_and_symptoms(data_dict)
            elif domain == "Sleep":
                sev, sym = self.compute_sleep_severity_and_symptoms(data_dict)
            else:
                sev, sym = (20.0, 20.0)

            # 3. Compute Trend & Weighted Score
            if is_first_visit:
                # First visit: No prior visit exists. Deltas don't exist.
                # Renormalize weights without trend term (Section 3B requirement)
                w_sev = self.baseline_weights.get("severity", 0.714)
                w_sym = self.baseline_weights.get("symptoms", 0.286)
                final_score = round((w_sev * sev) + (w_sym * sym), 1)
                trend_val = None
                weights_used = {"severity": w_sev, "symptoms": w_sym}
            else:
                trend_val = round(self.compute_trend_from_deltas(domain, domain_deltas), 1)
                w_sev = self.weights.get("severity", 0.5)
                w_tr = self.weights.get("trend", 0.3)
                w_sym = self.weights.get("symptoms", 0.2)
                final_score = round((w_sev * sev) + (w_tr * trend_val) + (w_sym * sym), 1)
                weights_used = {"severity": w_sev, "trend": w_tr, "symptoms": w_sym}

            band = self.map_score_to_band(final_score, is_insufficient=False)

            score_model = DomainScoreModel(
                id=f"score-{uuid.uuid4().hex[:12]}",
                visit_id=visit_id,
                domain=domain,
                score=final_score,
                band=band.value,
                severity_component=round(sev, 1),
                trend_component=trend_val,
                symptoms_component=round(sym, 1),
                completeness_ratio=completeness.completeness_ratio,
                confidence=completeness.confidence.value,
                missing_fields=completeness.missing_fields,
                is_insufficient_data=False,
                insufficient_reason=None,
                contributing_parameters=list(data_dict.keys()),
                meaningful_deltas_count=meaningful_count,
                observation_count=len(domain_obs_list),
                weights_used=weights_used,
                computed_without_trend=is_first_visit
            )
            results[domain] = score_model

        return results
