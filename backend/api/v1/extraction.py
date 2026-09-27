import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.extraction_service import ExtractionService
from backend.schemas.extraction import (
    ExtractionResult,
    ExtractedValueReviewItem,
    UnmappedLabLine,
    FlaggedReviewItem,
    ExtractedObservationItem
)
from backend.schemas.common import DomainType, ObservationSource, SourceConfidence
from backend.schemas.observation import PLAUSIBLE_RANGES

router = APIRouter(tags=["Extraction"])

@router.post("/extraction/lab-pdf", response_model=ExtractionResult)
async def extract_from_lab_pdf(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Accepts a lab report file (PDF or scanned image) or raw clinical report text.
    Returns a structured, reviewable extraction payload without committing to a visit.
    
    Pipeline:
    1. Text extraction (pdfplumber -> pytesseract OCR fallback)
    2. Date detection & multiple date warning
    3. Parameter mapping via lab_parameter_aliases.yaml
    4. Canonical unit conversion
    5. Biological plausibility range verification
    6. Duplicate test detection & confidence scoring
    """
    extractor = ExtractionService()

    if file:
        file_bytes = await file.read()
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        try:
            return extractor.process_lab_pdf(file_bytes)
        except ValueError as val_err:
            raise HTTPException(status_code=422, detail=str(val_err))
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Lab report processing failed: {str(err)}")

    elif raw_text:
        cleaned_text = raw_text.strip()
        if len(cleaned_text) < 10:
            raise HTTPException(
                status_code=422,
                detail="Raw text is too short to extract clinical laboratory parameters."
            )

        detected_dates = extractor.detect_dates_in_text(cleaned_text)
        date_warning = None
        if len(detected_dates) > 1:
            date_warning = (
                f"Multiple distinct dates detected ({', '.join(detected_dates)}). "
                "Confirm which encounter date these results pertain to."
            )

        raw_extraction = extractor.extract_with_groq(cleaned_text, source_method="free_text")
        extracted_items = raw_extraction.get("extracted_items", [])
        raw_unmapped = raw_extraction.get("unmapped_lines", [])

        review_values = []
        flagged_items = []
        unmapped_lines = []
        seen_canonical = {}
        legacy_observations = []

        report_date = detected_dates[0] if detected_dates else "2026-09-20"

        for item in extracted_items:
            raw_label = str(item.get("raw_label", "")).strip()
            mapped = item.get("mapped_field")
            val_raw = item.get("value")
            unit_raw = str(item.get("unit", "")).strip()
            ref_range = item.get("report_reference_range")
            flag = item.get("flag")

            canon = mapped if mapped in extractor.canonical_params else extractor.map_parameter_label(raw_label)

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
                        reason="Non-numeric value reported",
                        suggested_action="Review value manually"
                    )
                )
                continue

            if num_val is None:
                continue

            converted_val, canon_unit, unit_ok = extractor.convert_to_canonical_unit(canon, num_val, unit_raw)

            param_key = canon.lower().replace(" ", "_")
            range_passed = True
            if param_key in PLAUSIBLE_RANGES:
                min_v, max_v, _ = PLAUSIBLE_RANGES[param_key]
                if converted_val < min_v or converted_val > max_v:
                    range_passed = False
                    flagged_items.append(
                        FlaggedReviewItem(
                            mapped_field=canon,
                            raw_label=raw_label,
                            reported_value=f"{num_val} {unit_raw}",
                            reason=f"Value {converted_val} {canon_unit} outside biological plausibility range [{min_v} - {max_v}]",
                            suggested_action="Verify digit extraction"
                        )
                    )

            if not unit_ok and unit_raw:
                flagged_items.append(
                    FlaggedReviewItem(
                        mapped_field=canon,
                        raw_label=raw_label,
                        reported_value=f"{num_val} {unit_raw}",
                        reason=f"Unrecognized unit '{unit_raw}'",
                        suggested_action="Verify unit conversion"
                    )
                )

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
                        suggested_action="Latest entry retained for review"
                    )
                )

            confidence = "high" if (range_passed and unit_ok) else "low"
            conf_reason = "Extracted from text" if confidence == "high" else "Review flagged anomalies"

            param_domain_str = extractor.canonical_params.get(canon, {}).get("domain", "Other")
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
                source_confidence_reason=conf_reason,
                report_reference_range=ref_range,
                domain=param_domain,
                flag=flag,
                is_duplicate=is_dup,
                range_check_passed=range_passed
            )

            if is_dup:
                prev_idx = seen_canonical[canon]
                review_values[prev_idx] = rev_item
            else:
                seen_canonical[canon] = len(review_values)
                review_values.append(rev_item)

            legacy_observations.append(
                ExtractedObservationItem(
                    domain=param_domain,
                    parameter=canon,
                    value=converted_val,
                    numeric_value=converted_val,
                    unit=canon_unit,
                    date=report_date,
                    source=ObservationSource.LabReport,
                    source_confidence=SourceConfidence.High if confidence == "high" else SourceConfidence.LowOcrReviewNeeded,
                    flag=flag or ("normal" if range_passed else "abnormal"),
                    reference_range=ref_range
                )
            )

        for unmap in raw_unmapped:
            unmapped_lines.append(
                UnmappedLabLine(
                    raw_label=str(unmap.get("raw_label", "")),
                    raw_value=str(unmap.get("raw_value", ""))
                )
            )

        overall_conf = "high" if (len(flagged_items) == 0 and len(unmapped_lines) == 0) else "medium"
        if any(v.confidence == "low" for v in review_values):
            overall_conf = "low"

        return ExtractionResult(
            extraction_id=str(uuid.uuid4()),
            source_method="free_text",
            extracted_text_preview=cleaned_text[:400] + ("..." if len(cleaned_text) > 400 else ""),
            confidence=overall_conf,
            needs_clinician_review=(len(flagged_items) > 0 or len(unmapped_lines) > 0),
            extracted_values=review_values,
            unmapped_lines=unmapped_lines,
            flagged_for_review=flagged_items,
            dates_detected=detected_dates,
            date_warning=date_warning,
            observations=legacy_observations,
            source_type="free_text",
            extraction_method="groq_text_parser"
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either a lab report file (PDF/image) or raw_text."
        )
