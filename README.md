# PCOS Longitudinal Tracker

A clinician-facing decision-support prototype that tracks PCOS (Polycystic Ovary Syndrome) patients longitudinally across encounters and highlights which health domains require clinician attention, based on severity, longitudinal trends, and symptom burden.

> **CRITICAL CLINICAL NOTICE • SYNTHETIC DATA • DECISION SUPPORT ONLY**  
> This software is a clinical decision-support research prototype. It is **not a diagnostic tool** and does not provide medical advice, diagnosis, or treatment instructions. All clinical decisions remain solely the responsibility of licensed healthcare professionals.

---

## Architecture & Pipeline

```text
Inputs (Clinician Form / Lab PDF / Scanned Image / Free-Text Notes)
  → Extraction Layer (pdfplumber + pytesseract OCR + Groq JSON Mode + lab_parameter_aliases.yaml)
  → Post-Extraction Verification (Biological plausibility, unit normalization, duplicate resolution)
  → Patient & Visit Store (SQLite / PostgreSQL-ready SQLAlchemy models, Alembic migrations)
  → Delta Engine (Parameter-level threshold change classification & noise filtering)
  → Attention Scoring Engine (6 primary domains: 0–100 score + attention bands)
  → Defensive Reasoning Layer (Groq Llama 3.3 70B JSON generation + Code-level Number Validation)
  → REST Layer (FastAPI v1 mounted at /, /api, and /api/v1)
  → Clinician Dashboard (React 19, TypeScript, Tailwind CSS, Recharts)
```

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database**: SQLite (default), structured for seamless PostgreSQL migration
- **LLM & Reasoning**: Groq API (`llama-3.3-70b-versatile`) with structured JSON mode and automated numerical hallucination validation
- **Lab Extraction**: `pdfplumber` (native text) + `pytesseract` (OCR fallback for scanned/photographed records)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts
- **Testing**: `pytest` (38 automated unit & integration tests passing 100%)

---

## 6 Tracked Health Domains

1. **Reproductive**: Cycle length, cycle variability (SD), missed periods count, ovulation signs
2. **Hyperandrogenism**: Acne severity, hirsutism (modified Ferriman-Gallwey mFG score), hair loss, total/free testosterone, SHBG, DHEA-S
3. **Metabolic**: Weight, BMI, waist circumference, fasting glucose, fasting insulin, HOMA-IR (computed), HbA1c, lipids (TG, HDL, LDL), blood pressure
4. **Lifestyle**: Weekly physical activity minutes, diet quality score, smoking status, alcohol consumption
5. **Psychological**: PHQ-9 (depression screen) and GAD-7 (anxiety screen) validated questionnaires
6. **Sleep**: Sleep duration (hours), restorative quality, STOP-BANG / obstructive sleep apnea screening signs, Epworth sleepiness score
- *Differential / Exclusion Labs*: LH/FSH ratio, AMH, prolactin, TSH

---

## Attention Scoring Math & Guideline Thresholds

Per domain, three clinical signals are combined into a weighted composite score:

$$\text{Score} = 0.5 \times \text{Severity} + 0.3 \times \text{Trend} + 0.2 \times \text{Symptoms}$$

- **Severity (0–100)**: Measures current parameter abnormality against reference thresholds from the **2023 International Evidence-based PCOS Guideline** (Monash/ESHRE/ASRM) and Rotterdam criteria.
- **Trend (0–100)**: Direction and magnitude of longitudinal change computed by the Delta Engine. Worsening shifts elevate the score; improving shifts lower it.
- **Symptoms (0–100)**: Patient-reported symptom burden.
- **First-Visit Behavior**: When no prior visit exists, the trend component is omitted and weights are renormalized ($\approx 0.714 \times \text{Severity} + 0.286 \times \text{Symptoms}$) with `computed_without_trend: true`.

### Attention Bands
- **0.0 – 29.99**: Low
- **30.0 – 54.99**: Moderate
- **55.0 – 74.99**: Moderate-High
- **75.0 – 100.0**: High
- **Insufficient Data**: When completeness falls below 60%

---

## Missing Data Handling (Section 3B Guardrails)

Missing data is never silently treated as normal or assigned a falsely reassuring score:

1. **Tri-State Storage**: Every parameter record distinguishes:
   - `VALUE_PRESENT`: Measured value available.
   - `NOT_MEASURED`: Explicitly omitted during encounter, accompanied by a clinical `reason_code` (e.g. `lab_not_ordered`, `remote_telehealth_visit`).
   - `NOT_APPLICABLE`: Parameter not relevant to this patient.
2. **Missing History**: If a parameter was omitted in the previous visit, the Delta Engine assigns status `insufficient_history` rather than assuming zero change.
3. **Domain Completeness Threshold (60%)**:
   $$\text{Completeness Ratio} = \frac{\text{Fields Present}}{\text{Fields Expected}}$$
   - If ratio $< 0.60$: Score returns `null`, band returns `Insufficient Data`, and `is_insufficient_data: true`.
   - If $0.60 \le \text{ratio} < 1.0$: Score is computed with confidence `partial` and lists all `missing_fields`.
   - If $\text{ratio} = 1.0$: Score computed with confidence `full`.

---

## Patient & Visit Creation Guardrails (Section 5B)

- **POST /api/v1/patients**:
  - Accepts de-identified synthetic IDs (or auto-generates `P-XXXX`). Strictly no patient names or PII accepted.
  - Population ethnicity profiles: `asian_south_asian` (Asia-Pacific BMI cutoffs $\ge 23 \text{ kg/m}^2$, lower mFG thresholds) vs `standard_who`.
  - Age plausibility check (flags ages outside 12–55 for adolescent/perimenopausal tracking without hard-blocking).
  - Rejects duplicate patient IDs (`HTTP 409`).
- **POST /api/v1/patients/{id}/visits**:
  - Rejects visits with zero clinical fields (`HTTP 422`).
  - Rejects out-of-order/backdated visit dates (`HTTP 400`).
  - Warns on same-day repeat visits (`HTTP 201` with explicit warning banner).
  - Validates biological ranges via `PLAUSIBLE_RANGES`.
- **POST /api/v1/patients/{id}/visits/{visit_id}/process**:
  - Explicit trigger to run the Delta Engine, Domain Scoring Engine, and Groq reasoning narrative.

---

## Lab Report Extraction Pipeline (Section 5C)

Built for diverse clinical and diagnostic lab reports with variable formatting:

- **Endpoint**: `POST /extraction/lab-pdf` (also at `/api/v1/extraction/lab-pdf`)
  - Accepts PDF documents, scanned images, or raw text.
  - Returns a reviewable extraction payload (`extracted_values`, `unmapped_lines`, `flagged_for_review`, `dates_detected`) without writing to the database.
- **Text & OCR Extraction**:
  - Extracts text across all pages via `pdfplumber`.
  - Falls back to `pytesseract` OCR for scanned/photographed pages; tags extraction with `source_method: "ocr"` and medium confidence.
  - Fails fast (`HTTP 422`) on empty or unusable documents.
- **Canonical Alias Mapping (`backend/config/lab_parameter_aliases.yaml`)**:
  - Maps real-world aliases (e.g. `FBS`, `S. Testosterone`, `Glycated Hemoglobin`, `DHEA Sulfate`, `SHBG`).
  - Normalizes units (e.g. `mmol/L` $\rightarrow$ `mg/dL`, `nmol/L` $\rightarrow$ `ng/mL`, `pmol/L` $\rightarrow$ `uIU/mL`) while preserving original reported values and units for audit/trust.
- **Defensive LLM & Regex Extraction**:
  - Uses Groq JSON mode with canonical schema context, extracting strictly printed values.
  - Deterministic clinical regex parser fallback for offline or unconfigured environments.
- **Post-Extraction Validation**:
  - Biological range verification (catches OCR digit misreads like `HbA1c = 950`).
  - Duplicate resolution: preserves latest repeat test entry and flags for review.
  - Multi-date detection: emits warning when reports bundle tests from multiple dates.
- **Confirm to Visit**:
  - `POST /api/v1/patients/{id}/visits/{visit_id}/confirm-extraction` commits confirmed observations tagged `source="lab_report"` or `"ocr_extracted"` with preserved confidence scores.

---

## Defensive LLM Reasoning & Hallucination Mitigation

To guarantee clinical safety with LLM decision support:
1. **Restricted Payload**: The prompt receives strictly computed values (deltas, domain scores, evidence, completeness ratios).
2. **Mandatory Non-Diagnostic Phrasing**: Prompt enforces tentative language (*"may be consistent with"*) and forbids diagnosis or treatment directives.
3. **JSON Mode Output**: `response_format: {"type": "json_object"}`.
4. **Code-Level Numerical Validation**: An automated verification pass regex-extracts every number from the generated narrative and confirms it exists in the input JSON payload. If any hallucinated number is detected, regeneration is triggered; if validation fails twice, the system safely falls back to a deterministic summary.

---

## API Contract (FastAPI v1)

Mounted under `/api/v1`, `/api`, and `/`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Clinician authentication |
| `GET` | `/api/v1/auth/me` | Current session profile |
| `GET` | `/api/v1/patients` | List all longitudinal patient records |
| `POST` | `/api/v1/patients` | Register new patient (de-identified ID, phenotype, ethnicity profile) |
| `GET` | `/api/v1/patients/{id}` | Patient summary with all longitudinal visits |
| `GET` | `/api/v1/patients/{id}/trends?parameter={param}` | Longitudinal trend points for Recharts |
| `POST` | `/api/v1/patients/{id}/visits` | Create encounter snapshot (form observations / notes / file) |
| `POST` | `/api/v1/patients/{id}/visits/{visit_id}/process` | Trigger delta computation, domain scoring, and Groq narrative |
| `POST` | `/api/v1/patients/{id}/visits/{visit_id}/confirm-extraction` | Commit reviewed lab report observations to visit |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/deltas` | Clinical deltas vs previous visit |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/scores` | Domain scores, weights, citations, completeness |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/evidence/{domain}` | Raw observations backing domain score |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/reasoning` | Validated reasoning narrative |
| `POST` | `/api/v1/extraction/lab-pdf` | Upload lab PDF/OCR for reviewable extraction payload |

---

## Synthetic Personas (Rotterdam Phenotypes A–D)

Seed data includes 5 clinical personas with longitudinal encounters:
- **P-0042 (Phenotype A - Classic)**: Hyperandrogenism + Ovulatory dysfunction + PCO morphology. High metabolic risk, worsening in Visit 2, turnaround under lifestyle intervention in Visits 3–4.
- **P-0017 (Phenotype B - Metabolic-Dominant)**: Hyperandrogenism + Anovulation. Profound insulin resistance, rapid weight/HOMA-IR improvement on lifestyle + metformin.
- **P-0023 (Phenotype C - Ovulatory PCOS)**: Hyperandrogenism + PCO morphology with regular cycles, normal BMI, high anxiety/depression burden (PHQ-9 = 16, GAD-7 = 14) and sleep restriction.
- **P-0031 (Phenotype D - Non-Hyperandrogenic)**: Oligo-ovulation + PCO morphology, normal androgens, elevated LH:FSH ratio (3.1) and AMH (8.4 ng/mL).
- **P-0056 (Sparse / Missing Data Validation)**: Baseline visit complete; Visit 2 has $<60\%$ metabolic data (triggers `Insufficient Data` band); Visit 3 has partial hyperandrogenism data (triggers `partial` confidence with missing fields listed).

---

## Quickstart & Setup

### 1. Environment Configuration
Create a `.env` file in the project root (or copy from `.env.example`):
```env
# Frontend API Base URL
VITE_API_BASE_URL=http://127.0.0.1:8000

# SQLite Database URL (auto-created and seeded on first run)
DATABASE_URL=sqlite:///./backend/pcos_tracker.db

# Groq LLM API Configuration (get a free key at https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 2. Backend Setup & Test Suite
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run database migrations
alembic -c backend/alembic.ini upgrade head

# Run full pytest test suite (38 unit tests)
pytest backend/tests -v

# Start FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
In a separate terminal:
```bash
# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Visit **http://localhost:5173** to access the clinician dashboard.

**Clinician Demo Credentials:**
- Email: `dr.mehta@clinic.local`
- Password: `ClinicianDemo!2026`
- Or click **"Demo Mode"** on the login screen.

---

## Known Limitations & Ethical Considerations

1. **Ethnic Variations in Metabolic Risk**:
   - Standard WHO BMI ($\ge 25$ overweight, $\ge 30$ obese) and waist circumference ($\ge 88$ cm) cutoffs systematically underestimate metabolic and cardiovascular risks in South Asian and East Asian populations.
   - This prototype includes an ethnicity-configurable profile in `scoring_config.yaml` using IDF / Asia-Pacific cutoffs (BMI $\ge 23$ overweight, $\ge 27.5$ obese, waist $\ge 80$ cm). Clinicians should review the active population profile.
2. **LLM Hallucination Risk**:
   - Free-tier LLMs may occasionally invent numbers or assert diagnostic claims. Our dual-layer protection (defensive prompting + code-level numerical validation pass) prevents unverified outputs from reaching the clinician.
3. **Data Privacy**:
   - All patient records in this repository are strictly synthetic. No protected health information (PHI) should ever be entered or processed.
