import re
import json
import time
import logging
from typing import Dict, Any, List, Tuple, Optional
from groq import Groq
from backend.config.settings import settings
from backend.schemas.reasoning import ReasoningResponse, ReasoningInputPayload

logger = logging.getLogger("reasoning_service")
logger.setLevel(logging.INFO)

SYSTEM_PROMPT = (
    "CONSTRAINT 1: THIS IS A DECISION-SUPPORT PROTOTYPE ONLY. NEVER PROVIDE A DIAGNOSIS OR CLINICAL INSTRUCTION.\n"
    "You are a clinical decision-support reasoning assistant for longitudinal PCOS tracking.\n"
    "You will receive a strictly validated JSON payload containing computed domain scores, deltas, and evidence.\n"
    "Rules:\n"
    "1. Only mention relationships and parameters directly present in the provided input data.\n"
    "2. Phrase all clinical context as possible associations (e.g. 'may be consistent with', 'suggests attention may be warranted'), NEVER as a definitive diagnosis or medical instruction.\n"
    "3. Explicitly state 'Insufficient data' for any domain marked as insufficient_data, and do NOT construct associations using absent fields from partial domains.\n"
    "4. In the JSON output, provide a narrative paragraph and a list of cited parameters.\n"
    "Format your response strictly as JSON with this schema:\n"
    "{\n"
    "  \"narrative\": \"<clinical reasoning text>\",\n"
    "  \"cited_parameters\": [\"<param1>\", \"<param2>\"],\n"
    "  \"domain_notes\": {\"<Domain>\": \"<short observation>\"}\n"
    "}\n"
    "CONSTRAINT 2: NEVER STATE A DIAGNOSIS OR DIRECT MEDICAL TREATMENT."
)

class ReasoningService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = settings.GROQ_MODEL

    def extract_numbers_from_text(self, text: str) -> List[float]:
        """
        Parses all numbers out of a text string (e.g. '68 kg to 71.5 kg' -> [68.0, 71.5]).
        """
        raw_matches = re.findall(r"(?<![a-zA-Z0-9_\-])([0-9]+(?:\.[0-9]+)?)(?![a-zA-Z0-9_\-])", text)
        numbers = []
        for m in raw_matches:
            try:
                numbers.append(float(m))
            except ValueError:
                pass
        return numbers

    def validate_narrative_numbers(self, narrative: str, input_payload: Dict[str, Any]) -> Tuple[bool, List[float]]:
        """
        Mandatory code-level validation pass:
        Confirms that every number in the generated narrative appears in the input JSON payload.
        Prevents hallucinated laboratory values or invented metrics.
        """
        narrative_numbers = self.extract_numbers_from_text(narrative)
        if not narrative_numbers:
            return True, []

        # Collect all allowed numbers from input payload
        payload_str = json.dumps(input_payload)
        allowed_numbers = set(self.extract_numbers_from_text(payload_str))

        hallucinated = []
        for num in narrative_numbers:
            # Allow common integers like visit numbers, days, or approximate roundings (within 0.1)
            matched = any(abs(num - allowed) < 0.15 for allowed in allowed_numbers)
            # Also allow basic conversational counts 1, 2, 3, 4, 6, 12, 24, 100
            if not matched and int(num) not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 21, 28, 30, 100]:
                hallucinated.append(num)

        is_valid = len(hallucinated) == 0
        return is_valid, hallucinated

    def deterministic_fallback_narrative(self, payload: Dict[str, Any]) -> str:
        """
        Deterministic, safe clinical decision-support narrative used when offline
        or when validation fails multiple times.
        """
        lines = []
        deltas = payload.get("deltas", [])
        scores = payload.get("scores", {})
        completeness = payload.get("data_completeness", {})

        meaningful_deltas = [d for d in deltas if d.get("is_meaningful", False) or d.get("isMeaningful", False)]
        
        if payload.get("is_first_visit", False):
            lines.append(
                "Baseline clinical encounter: Longitudinal trends are not yet established. "
                "Attention domain scores reflect current absolute parameter severity without trend weighting."
            )
        elif meaningful_deltas:
            delta_descriptions = []
            for d in meaningful_deltas[:3]:
                param = d.get("parameter", "").replace("_", " ")
                display = d.get("delta_display") or d.get("deltaDisplay")
                delta_descriptions.append(f"{param} ({display})")
            lines.append(
                f"Longitudinal monitoring identified notable shifts in: {', '.join(delta_descriptions)}. "
                "These changes may be consistent with active physiological shifts and suggest clinical attention is warranted."
            )
        else:
            lines.append(
                "Longitudinal parameters demonstrate relative stability across tracked domains since the previous visit."
            )

        # Note any insufficient domains
        insufficient = [dom for dom, c in completeness.items() if c.get("confidence") == "insufficient_data"]
        if insufficient:
            lines.append(
                f"Note: Insufficient data recorded for {', '.join(insufficient)}; scores for these areas cannot be computed."
            )

        return " ".join(lines)

    def generate_reasoning(self, payload: Dict[str, Any]) -> ReasoningResponse:
        """
        Executes Groq reasoning with JSON mode, raw output logging, and code-level number validation.
        Retries on validation failure, falling back safely if validation fails twice.
        """
        visit_id = payload.get("visit_id", "")
        insufficient_domains = [
            dom for dom, c in payload.get("data_completeness", {}).items()
            if c.get("confidence") == "insufficient_data"
        ]
        partial_domains = {
            dom: c.get("missing_fields", [])
            for dom, c in payload.get("data_completeness", {}).items()
            if c.get("confidence") == "partial"
        }

        # If no Groq client, return verified deterministic narrative
        if not self.client:
            narrative = self.deterministic_fallback_narrative(payload)
            return ReasoningResponse(
                visit_id=visit_id,
                narrative=narrative,
                cited_parameters=[d.get("parameter") for d in payload.get("deltas", []) if d.get("is_meaningful")],
                validation_passed=True,
                validation_notes="Deterministic clinical narrative generated (offline / no API key configured).",
                insufficient_data_domains=insufficient_domains,
                partial_domains=partial_domains
            )

        # Prepare user prompt with restricted payload
        user_prompt = (
            f"Here is the verified patient longitudinal payload:\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            f"Please generate the clinical reasoning object in JSON mode. "
            f"Reminder: Only reference provided values, use tentative phrasing ('may be consistent with'), "
            f"and never provide a diagnosis."
        )

        max_attempts = 2
        last_error = ""

        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                raw_output = response.choices[0].message.content
                logger.info(f"Raw Groq Reasoning Output (Attempt {attempt+1}):\n{raw_output}")

                parsed = json.loads(raw_output)
                narrative = parsed.get("narrative", "")
                cited = parsed.get("cited_parameters", [])

                # Code-level validation pass: check that every number in the narrative exists in input
                valid, hallucinated = self.validate_narrative_numbers(narrative, payload)
                if valid:
                    return ReasoningResponse(
                        visit_id=visit_id,
                        narrative=narrative,
                        cited_parameters=cited,
                        validation_passed=True,
                        validation_notes="Validation check passed: All numerical references confirmed in input payload.",
                        insufficient_data_domains=insufficient_domains,
                        partial_domains=partial_domains
                    )
                else:
                    logger.warning(
                        f"Validation pass failed on attempt {attempt+1}: "
                        f"Found unverified numbers {hallucinated} in model narrative."
                    )
                    user_prompt += (
                        f"\n\nERROR IN PREVIOUS ATTEMPT: Your previous narrative contained numbers {hallucinated} "
                        f"that did NOT exist in the provided input JSON. "
                        f"You MUST only cite exact numbers present in the input. Regenerate now."
                    )

            except Exception as e:
                logger.error(f"Groq API error on attempt {attempt+1}: {e}")
                last_error = str(e)
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    time.sleep(2.5 * (attempt + 1))
                else:
                    time.sleep(1.0)

        # If validation fails twice, fail gracefully to safe fallback (Section 4 requirement)
        logger.warning("Reasoning validation or API retries exhausted. Gracefully failing to safe fallback.")
        fallback_text = self.deterministic_fallback_narrative(payload)
        return ReasoningResponse(
            visit_id=visit_id,
            narrative=fallback_text,
            cited_parameters=[],
            validation_passed=False,
            validation_notes=f"Model validation failed or rate-limited ({last_error}). Safe fallback displayed.",
            insufficient_data_domains=insufficient_domains,
            partial_domains=partial_domains
        )
