import os
import re
import json
import time
import uuid
import yaml
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import pdfplumber
from groq import Groq
from backend.config.settings import settings
from backend.schemas.common import DomainType, ObservationSource, SourceConfidence
from backend.schemas.observation import PLAUSIBLE_RANGES
from backend.schemas.extraction import (
    ExtractedObservationItem,
    ExtractedValueReviewItem,
    UnmappedLabLine,
    FlaggedReviewItem,
    ExtractionResult,
)

logger = logging.getLogger("extraction_service")
logger.setLevel(logging.INFO)

ALIAS_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "lab_parameter_aliases.yaml"
)

class RegexExtractionResult(list):
    def __init__(self, observation_items: List[ExtractedObservationItem], unmapped_lines: Optional[List[Dict[str, Any]]] = None):
        super().__init__(observation_items)
        self.unmapped_lines = unmapped_lines or []

    def get(self, key: str, default: Any = None) -> Any:
        if key == "extracted_items":
            return [
                {
                    "raw_label": getattr(item, "notes", None) or item.parameter,
                    "mapped_field": item.parameter,
                    "value": item.numeric_value if item.numeric_value is not None else item.value,
                    "unit": item.unit,
                    "report_reference_range": item.reference_range,
                    "flag": item.flag
                }
                for item in self
            ]
        elif key == "unmapped_lines":
            return self.unmapped_lines
        return default

class ExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = settings.GROQ_MODEL
        self._load_alias_config()

    def _load_alias_config(self):
        """Loads canonical parameter aliases, domains, and unit conversion factors from YAML."""
        self.canonical_params: Dict[str, Any] = {}
        self.alias_to_canonical: Dict[str, str] = {}

        if os.path.exists(ALIAS_CONFIG_PATH):
            try:
                with open(ALIAS_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    self.canonical_params = data.get("parameters", {})
                    for canon_name, info in self.canonical_params.items():
                        # Map canonical name itself
                        self.alias_to_canonical[canon_name.lower()] = canon_name
                        self.alias_to_canonical[canon_name.replace("_", " ").lower()] = canon_name
                        # Map all defined aliases
                        for alias in info.get("aliases", []):
                            self.alias_to_canonical[alias.strip().lower()] = canon_name
            except Exception as e:
                logger.error(f"Failed to load lab_parameter_aliases.yaml: {e}")
        else:
            logger.warning(f"Alias config file not found at {ALIAS_CONFIG_PATH}")

    def extract_text_from_pdf(self, file_bytes: bytes) -> Tuple[str, str, str]:
        """
        STEP 1: Text extraction from PDF.
        - Primary path: pdfplumber across all pages (merges multi-page reports)
        - Fallback path: pytesseract OCR on rasterized pages if text is near-empty
        Returns: (text, source_method ["text_pdf" | "ocr"], confidence ["high" | "medium"])
        """
        import io
        text_parts = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(f"--- Page {idx + 1} ---\n{page_text}")
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

        combined_text = "\n\n".join(text_parts).strip()

        # If text is sufficient (> 20 chars), native digital PDF succeeded
        if len(combined_text) >= 20:
            return combined_text, "text_pdf", "high"

        # Fallback to pytesseract OCR for scanned / photographed PDF pages
        logger.info("Native text extraction yielded < 20 characters. Falling back to OCR.")
        ocr_parts = []
        try:
            import pytesseract
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    im = page.to_image(resolution=200).original
                    page_ocr = pytesseract.image_to_string(im)
                    if page_ocr and page_ocr.strip():
                        ocr_parts.append(f"--- Page {idx + 1} (OCR) ---\n{page_ocr}")
        except Exception as ocr_err:
            logger.warning(f"pytesseract OCR fallback error: {ocr_err}")

        ocr_text = "\n\n".join(ocr_parts).strip()
        if len(ocr_text) >= 15:
            return ocr_text, "ocr", "medium"

        # If both methods returned unusable text, fail fast with clear error
        if len(combined_text) < 15 and len(ocr_text) < 15:
            raise ValueError(
                "Could not read or extract usable text from this file. "
                "The file may be blank, corrupted, or an unsupported image format."
            )

        return (combined_text or ocr_text), "text_pdf", "high"

    def detect_dates_in_text(self, text: str) -> List[str]:
        """Detects distinct clinical collection/report dates in the raw text."""
        date_patterns = [
            r"\b(202[0-9]-[0-1][0-9]-[0-3][0-9])\b",                  # YYYY-MM-DD
            r"\b([0-3]?[0-9]/[0-1]?[0-9]/202[0-9])\b",                # DD/MM/YYYY
            r"\b([0-3]?[0-9]-[0-1]?[0-9]-202[0-9])\b",                # DD-MM-YYYY
            r"\b([0-3]?[0-9]\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+202[0-9])\b", # DD Mon YYYY
        ]
        found: Set[str] = set()
        for pat in date_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                found.add(m)
        return sorted(list(found))

    def map_parameter_label(self, raw_label: str) -> Optional[str]:
        """Resolves a raw printed label from a lab report to its canonical schema field name."""
        cleaned = raw_label.strip().lower()
        cleaned = re.sub(r"[\(\):,]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Direct alias match
        if cleaned in self.alias_to_canonical:
            return self.alias_to_canonical[cleaned]

        # Partial substring match against alias dictionary
        for alias, canon in self.alias_to_canonical.items():
            if alias in cleaned or cleaned in alias:
                return canon

        return None

    def convert_to_canonical_unit(
        self, canon_param: str, value: float, reported_unit: str
    ) -> Tuple[float, str, bool]:
        """
        Converts reported value to canonical unit.
        Returns: (canonical_value, canonical_unit, is_unit_recognized)
        """
        param_info = self.canonical_params.get(canon_param, {})
        canonical_unit = param_info.get("canonical_unit", reported_unit)
        conversions = param_info.get("conversions", {})

        clean_unit = reported_unit.strip().lower()
        if not clean_unit or not conversions:
            return value, canonical_unit, True

        # Check conversion table
        if clean_unit in conversions:
            multiplier = conversions[clean_unit]
            return round(value * multiplier, 4), canonical_unit, True

        # Check if already canonical unit
        if clean_unit == canonical_unit.lower():
            return value, canonical_unit, True

        return value, canonical_unit, False

    def rule_based_regex_extractor(self, raw_text: str) -> RegexExtractionResult:
        """Deterministic clinical regex fallback matching parameters against alias config."""
        extracted: List[ExtractedObservationItem] = []
        unmapped: List[Dict[str, Any]] = []

        line_patterns = [
            r"([A-Za-z0-9\s,\-\(\)\/\.]+?)[:\t\s]{2,}([\d\.]+)\s*([a-zA-Z\%\/\^0-9\-_]*)(?:\s+([\d\.\-<\>\s]+))?",
        ]

        seen_params: Set[str] = set()

        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str or len(line_str) < 5:
                continue

            for pat in line_patterns:
                match = re.search(pat, line_str)
                if match:
                    raw_name = match.group(1).strip()
                    val_str = match.group(2).strip()
                    unit_str = match.group(3).strip() if match.group(3) else ""
                    ref_str = match.group(4).strip() if match.group(4) else ""

                    try:
                        num_val = float(val_str)
                    except ValueError:
                        continue

                    canon = self.map_parameter_label(raw_name)
                    if canon:
                        domain_str = self.canonical_params.get(canon, {}).get("domain", "Other")
                        try:
                            domain = DomainType(domain_str)
                        except ValueError:
                            domain = DomainType.Other

                        extracted.append(
                            ExtractedObservationItem(
                                domain=domain,
                                parameter=canon,
                                value=num_val,
                                numeric_value=num_val,
                                unit=unit_str,
                                date="2026-09-20",
                                source=ObservationSource.LabReport,
                                source_confidence=SourceConfidence.High,
                                flag="normal",
                                reference_range=ref_str or None,
                                notes=raw_name
                            )
                        )
                        seen_params.add(canon)
                    else:
                        if any(w in raw_name.lower() for w in ["serum", "blood", "total", "ratio", "level", "panel", "test"]):
                            unmapped.append({
                                "raw_label": raw_name,
                                "raw_value": f"{val_str} {unit_str}".strip()
                            })

        # Also search explicit patterns for primary PCOS biomarkers
        for canon, info in self.canonical_params.items():
            if canon in seen_params:
                continue
            for alias in info.get("aliases", []):
                esc_alias = re.escape(alias)
                pat = rf"(?:{esc_alias})[^\d\n]*([\d\.]+)\s*([a-zA-Z\%\/\^0-9\-_]*)"
                m = re.search(pat, raw_text, re.IGNORECASE)
                if m:
                    try:
                        v = float(m.group(1))
                        u = m.group(2) if m.group(2) else info.get("canonical_unit", "")
                        domain_str = info.get("domain", "Other")
                        try:
                            domain = DomainType(domain_str)
                        except ValueError:
                            domain = DomainType.Other

                        extracted.append(
                            ExtractedObservationItem(
                                domain=domain,
                                parameter=canon,
                                value=v,
                                numeric_value=v,
                                unit=u,
                                date="2026-09-20",
                                source=ObservationSource.LabReport,
                                source_confidence=SourceConfidence.High,
                                flag="normal",
                                reference_range=None,
                                notes=alias.title()
                            )
                        )
                        seen_params.add(canon)
                        break
                    except ValueError:
                        pass

        return RegexExtractionResult(extracted, unmapped)

    def extract_with_groq(
        self,
        raw_text: str,
        source_method: str = "text_pdf",
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        STEP 3: LLM Extraction with Groq JSON mode.
        Instructs Groq to extract only literally present values without diagnosis or hallucination.
        """
        if not self.client:
            logger.info("No Groq client configured. Using deterministic clinical regex parser.")
            return self.rule_based_regex_extractor(raw_text)

        canonical_list = list(self.canonical_params.keys())
        system_prompt = (
            "You are a clinical laboratory extraction parser for a PCOS decision-support tool. "
            "Extract laboratory tests, values, units, and stated reference ranges literally present on the report. "
            "CRITICAL INSTRUCTIONS:\n"
            "1. Extract ONLY what is literally printed. Do NOT infer, guess, or extrapolate missing values.\n"
            "2. Map each test to a mapped_field from this canonical list if matching: "
            f"{json.dumps(canonical_list)}. If it cannot be mapped with high certainty, set mapped_field to null.\n"
            "3. Do NOT diagnose, evaluate clinical status, or provide medical opinions.\n"
            "4. Return valid JSON matching this exact structure:\n"
            "{\n"
            '  "extracted_items": [\n'
            '    {\n'
            '      "raw_label": "<exact label on report>",\n'
            '      "mapped_field": "<canonical_field_name or null>",\n'
            '      "value": <numeric_value>,\n'
            '      "unit": "<reported_unit>",\n'
            '      "report_reference_range": "<reference range if printed or null>",\n'
            '      "flag": "<HIGH/LOW/NORMAL if printed or null>"\n'
            '    }\n'
            '  ],\n'
            '  "unmapped_lines": [\n'
            '    {"raw_label": "<label>", "raw_value": "<value and unit>"}\n'
            '  ]\n'
            "}"
        )

        user_content = f"Extract laboratory data from this report:\n\n{raw_text[:4500]}"

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                raw_json = response.choices[0].message.content
                parsed = json.loads(raw_json)
                if "extracted_items" in parsed:
                    return parsed
                elif "observations" in parsed:
                    # Normalize structure if model returned observations key
                    return {
                        "extracted_items": parsed["observations"],
                        "unmapped_lines": parsed.get("unmapped_lines", [])
                    }
            except Exception as e:
                logger.warning(f"Groq extraction attempt {attempt + 1} failed: {e}")
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    time.sleep(2.0 * (attempt + 1))
                else:
                    time.sleep(1.0)

        logger.error("Groq extraction exhausted retries. Falling back to regex parser.")
        return self.rule_based_regex_extractor(raw_text)

    def process_lab_pdf(self, file_bytes: bytes) -> ExtractionResult:
        """
        Full Section 5C pipeline:
        1. Extract text via pdfplumber with pytesseract OCR fallback
        2. Date detection & multiple date warning
        3. LLM/Regex extraction with alias context
        4. Code-level range validation, unit conversion, duplicate resolution & confidence scoring
        5. Return comprehensive reviewable payload (does NOT write to visit yet)
        """
        # Step 1: Text extraction
        text, source_method, base_confidence = self.extract_text_from_pdf(file_bytes)

        # Detect dates in report
        detected_dates = self.detect_dates_in_text(text)
        date_warning = None
        if len(detected_dates) > 1:
            date_warning = (
                f"Multiple distinct dates detected ({', '.join(detected_dates)}). "
                "Verify whether this document bundles multiple encounters or panels."
            )

        # Step 3: Raw extraction
        raw_extraction = self.extract_with_groq(text, source_method)
        extracted_items = raw_extraction.get("extracted_items", [])
        raw_unmapped = raw_extraction.get("unmapped_lines", [])

        # Step 4: Post-extraction validation & canonical mapping in code
        review_values: List[ExtractedValueReviewItem] = []
        flagged_items: List[FlaggedReviewItem] = []
        unmapped_lines: List[UnmappedLabLine] = []
        seen_canonical: Dict[str, int] = {} # canon_name -> index in review_values
        legacy_observations: List[ExtractedObservationItem] = []

        report_date = detected_dates[0] if detected_dates else "2026-09-20"

        for item in extracted_items:
            raw_label = str(item.get("raw_label", "")).strip()
            mapped = item.get("mapped_field")
            val_raw = item.get("value")
            unit_raw = str(item.get("unit", "")).strip()
            ref_range = item.get("report_reference_range")
            flag = item.get("flag")

            # Resolve canonical field
            canon = mapped if mapped in self.canonical_params else self.map_parameter_label(raw_label)

            if not canon:
                unmapped_lines.append(
                    UnmappedLabLine(raw_label=raw_label, raw_value=f"{val_raw} {unit_raw}".strip())
                )
                continue

            try:
                num_val = float(val_raw) if val_raw is not None else None
            except (ValueError, TypeError):
                flagged_items.append(
                    FlaggedReviewItem(
                        mapped_field=canon,
                        raw_label=raw_label,
                        reported_value=val_raw,
                        reason="Non-numeric value reported for quantitative parameter",
                        suggested_action="Review printed value manually"
                    )
                )
                continue

            if num_val is None:
                continue

            # Unit conversion
            converted_val, canon_unit, unit_ok = self.convert_to_canonical_unit(canon, num_val, unit_raw)

            # Plausibility check against clinical range
            param_key = canon.lower().replace(" ", "_")
            range_passed = True
            range_reason = ""
            if param_key in PLAUSIBLE_RANGES:
                min_v, max_v, _ = PLAUSIBLE_RANGES[param_key]
                if converted_val < min_v or converted_val > max_v:
                    range_passed = False
                    range_reason = f"Value {converted_val} {canon_unit} outside biological plausibility range [{min_v} - {max_v}]"
                    flagged_items.append(
                        FlaggedReviewItem(
                            mapped_field=canon,
                            raw_label=raw_label,
                            reported_value=f"{num_val} {unit_raw}",
                            reason=range_reason,
                            suggested_action="Verify digit extraction; OCR may have misread decimal point or numbers."
                        )
                    )

            if not unit_ok and unit_raw:
                flagged_items.append(
                    FlaggedReviewItem(
                        mapped_field=canon,
                        raw_label=raw_label,
                        reported_value=f"{num_val} {unit_raw}",
                        reason=f"Unrecognized unit '{unit_raw}'; expected '{canon_unit}'",
                        suggested_action="Confirm unit conversion before clinical calculation"
                    )
                )

            # Determine confidence score
            confidence = "high"
            confidence_reasons = []

            if source_method == "ocr":
                confidence = "medium"
                confidence_reasons.append("OCR-derived; verify digits and decimal points")
            else:
                confidence_reasons.append("Direct text match from digital report")

            if not range_passed or not unit_ok:
                confidence = "low"
                if not range_passed:
                    confidence_reasons.append("Failed biological range verification")
                if not unit_ok:
                    confidence_reasons.append("Unrecognized unit")

            # Duplicate resolution (edge case: parameter appears twice on report)
            is_dup = False
            if canon in seen_canonical:
                is_dup = True
                prev_idx = seen_canonical[canon]
                review_values[prev_idx].is_duplicate = True
                flagged_items.append(
                    FlaggedReviewItem(
                        mapped_field=canon,
                        raw_label=raw_label,
                        reported_value=f"{num_val} {unit_raw}",
                        reason=f"Duplicate test entry detected for '{canon}'.",
                        suggested_action="Final printed entry retained; verify if this was a repeat test."
                    )
                )

            param_domain_str = self.canonical_params.get(canon, {}).get("domain", "Other")
            try:
                param_domain = DomainType(param_domain_str)
            except ValueError:
                param_domain = DomainType.Other

            rev_item = ExtractedValueReviewItem(
                mapped_field=canon,
                raw_label=raw_label,
                value=converted_val,
                unit=unit_raw or canon_unit,
                canonical_unit=canon_unit,
                original_value=num_val,
                confidence=confidence,
                source_confidence_reason="; ".join(confidence_reasons),
                report_reference_range=ref_range,
                domain=param_domain,
                flag=flag,
                is_duplicate=is_dup,
                range_check_passed=range_passed
            )

            # If duplicate, update existing entry with latest/final, otherwise append
            if is_dup:
                prev_idx = seen_canonical[canon]
                review_values[prev_idx] = rev_item
            else:
                seen_canonical[canon] = len(review_values)
                review_values.append(rev_item)

            # Legacy compatibility item
            legacy_observations.append(
                ExtractedObservationItem(
                    domain=param_domain,
                    parameter=canon,
                    value=converted_val,
                    numeric_value=converted_val,
                    unit=canon_unit,
                    date=report_date,
                    source=ObservationSource.OcrExtracted if source_method == "ocr" else ObservationSource.LabReport,
                    source_confidence=SourceConfidence.LowOcrReviewNeeded if confidence != "high" else SourceConfidence.High,
                    flag=flag or ("normal" if range_passed else "abnormal"),
                    reference_range=ref_range
                )
            )

        # Append unmapped lines from raw extraction
        for unmap in raw_unmapped:
            unmapped_lines.append(
                UnmappedLabLine(
                    raw_label=str(unmap.get("raw_label", "")),
                    raw_value=str(unmap.get("raw_value", ""))
                )
            )

        overall_conf = "high"
        if source_method == "ocr" or any(v.confidence == "medium" for v in review_values):
            overall_conf = "medium"
        if any(v.confidence == "low" for v in review_values) or len(flagged_items) > 0:
            overall_conf = "low"

        needs_review = (overall_conf != "high" or len(flagged_items) > 0 or len(unmapped_lines) > 0)

        return ExtractionResult(
            extraction_id=str(uuid.uuid4()),
            source_method=source_method,
            extracted_text_preview=text[:400] + ("..." if len(text) > 400 else ""),
            confidence=overall_conf,
            needs_clinician_review=needs_review,
            extracted_values=review_values,
            unmapped_lines=unmapped_lines,
            flagged_for_review=flagged_items,
            dates_detected=detected_dates,
            date_warning=date_warning,
            observations=legacy_observations,
            source_type=source_method,
            extraction_method=f"pdfplumber_{source_method}"
        )
