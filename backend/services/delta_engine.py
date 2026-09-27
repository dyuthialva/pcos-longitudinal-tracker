import uuid
from typing import List, Dict, Any, Optional
from backend.config.settings import load_scoring_config
from backend.models.observation import DomainObservation
from backend.models.delta import ClinicalDeltaModel

class DeltaEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_scoring_config()
        self.domains_config = self.config.get("domains", {})

    def get_parameter_delta_config(self, domain: str, parameter: str) -> Optional[Dict[str, Any]]:
        domain_cfg = self.domains_config.get(domain, {})
        deltas_cfg = domain_cfg.get("deltas", {})
        return deltas_cfg.get(parameter)

    def compute_deltas(
        self,
        current_visit_id: str,
        current_observations: List[DomainObservation],
        previous_observations: Optional[List[DomainObservation]] = None
    ) -> List[ClinicalDeltaModel]:
        """
        Computes deltas between current and previous visits.
        - If previous_observations is None or empty (first-ever visit), returns empty list (Section 3B).
        - If a parameter exists in current visit but is missing in previous visit,
          marks status_tag="insufficient_history" and previous_value=None (Section 3B).
        - Noise filtering: only marks is_significant=True and is_meaningful=True if change
          crosses the threshold defined in scoring_config.yaml.
        """
        if not previous_observations:
            # First visit: Deltas simply don't exist yet (Section 3B requirement)
            return []

        # Index previous observations by parameter_name
        prev_map: Dict[str, DomainObservation] = {
            obs.parameter_name: obs
            for obs in previous_observations
            if obs.measurement_status == "VALUE_PRESENT" and obs.numeric_value is not None
        }

        deltas: List[ClinicalDeltaModel] = []

        for curr_obs in current_observations:
            if curr_obs.measurement_status != "VALUE_PRESENT" or curr_obs.numeric_value is None:
                continue

            param = curr_obs.parameter_name
            domain = curr_obs.domain
            curr_val = curr_obs.numeric_value
            unit = curr_obs.unit or ""

            # Check if previous observation exists
            if param not in prev_map:
                # Section 3B: If previous visit lacks a given parameter, output as 'insufficient_history'
                delta = ClinicalDeltaModel(
                    id=f"delta-{uuid.uuid4().hex[:12]}",
                    visit_id=current_visit_id,
                    domain=domain,
                    parameter=param,
                    previous_value=None,
                    current_value=f"{curr_val} {unit}".strip(),
                    delta_display="No prior record",
                    numeric_delta=None,
                    unit=unit,
                    direction="neutral",
                    is_significant=False,
                    status_tag="insufficient_history",
                    status_severity="neutral",
                    clinical_note="Prior baseline not available for longitudinal delta comparison."
                )
                deltas.append(delta)
                continue

            prev_obs = prev_map[param]
            prev_val = prev_obs.numeric_value
            diff = curr_val - prev_val
            abs_diff = abs(diff)

            # Retrieve threshold from config
            param_cfg = self.get_parameter_delta_config(domain, param)
            threshold = param_cfg.get("meaningful_change", None) if param_cfg else None

            # Direction
            if diff > 0.0001:
                direction = "up"
                display_prefix = "+"
            elif diff < -0.0001:
                direction = "down"
                display_prefix = ""
            else:
                direction = "neutral"
                display_prefix = ""

            display_diff = f"{display_prefix}{diff:.1f} {unit}".strip() if abs_diff < 100 else f"{display_prefix}{diff:.0f} {unit}".strip()

            if threshold is not None and abs_diff >= threshold:
                # Meaningful change crossing guideline/clinical threshold!
                is_significant = True
                is_meaningful = True
                
                # Check for substantial shift (> 1.75x threshold)
                if abs_diff >= (1.75 * threshold):
                    status_tag = "Substantial shift"
                    status_severity = "high"
                else:
                    status_tag = "Threshold crossed"
                    status_severity = "moderate"

                clinical_note = (
                    f"Clinically meaningful change of {abs_diff:.1f} {unit} crossed the "
                    f"monitoring threshold of {threshold:.1f} {unit}."
                )
            else:
                # Noise / clinically stable change below threshold
                is_significant = False
                is_meaningful = False
                status_tag = "Stable"
                status_severity = "neutral"
                clinical_note = "Within expected intra-patient physiological variation."

            delta = ClinicalDeltaModel(
                id=f"delta-{uuid.uuid4().hex[:12]}",
                visit_id=current_visit_id,
                domain=domain,
                parameter=param,
                previous_value=f"{prev_val} {unit}".strip(),
                current_value=f"{curr_val} {unit}".strip(),
                delta_display=display_diff,
                numeric_delta=round(diff, 2),
                unit=unit,
                direction=direction,
                is_significant=is_significant,
                status_tag=status_tag,
                status_severity=status_severity,
                clinical_note=clinical_note
            )
            deltas.append(delta)

        return deltas
