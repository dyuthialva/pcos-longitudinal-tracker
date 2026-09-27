# PCOS Longitudinal Tracker

A clinician-facing decision-support prototype that tracks PCOS (Polycystic Ovary Syndrome) patients longitudinally across visits and highlights which health domains need clinician attention, based on severity, trend, and symptom burden.

> **CRITICAL CLINICAL NOTICE • SYNTHETIC DATA • DECISION SUPPORT ONLY**  
> This software is a clinical decision-support research prototype. It is **not a diagnostic tool** and does not provide medical advice, diagnosis, or treatment instructions. All clinical decisions remain solely the responsibility of licensed healthcare professionals.

---

## Architecture & Pipeline

```text
Inputs (Form / Lab PDF / Free Text)
  → Extraction Layer (pdfplumber + pytesseract OCR + Groq JSON Mode)
  → Patient & Visit Store (SQLite / PostgreSQL-ready SQLAlchemy models)
  → Delta Engine (Parameter-level threshold change classification & noise filtering)
  → Attention Scoring Engine (6 primary domains: 0–100 score + attention bands)
  → Reasoning Layer (Defensive Groq LLM generation + Code-level Number Validation)
  → FastAPI REST Layer (Dual-mounted under /api/v1 and /api for frontend integration)
```

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database**: SQLite (default), structured for seamless PostgreSQL migration
- **LLM & Reasoning**: Groq API (`llama-3.3-70b-versatile`) with structured JSON mode and numerical validation
- **Lab Extraction**: `pdfplumber` (digital PDF text) + `pytesseract` (OCR fallback for scanned records)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts

---

## 6 Tracked Health Domains

1. **Reproductive**: Cycle length, cycle variability (SD), missed periods count, ovulation signs
2. **Hyperandrogenism**: Acne severity, hirsutism (modified Ferriman-Gallwey mFG score), hair loss, total/free testosterone, SHBG, DHEAS
3. **Metabolic**: Weight, BMI, waist circumference, fasting glucose, fasting insulin, HOMA-IR (computed), HbA1c, lipids (TG, HDL, LDL), blood pressure
4. **Lifestyle**: Weekly physical activity minutes, diet quality score, smoking status, alcohol consumption
5. **Psychological**: PHQ-9 (depression screen) and GAD-7 (anxiety screen) validated questionnaires
6. **Sleep**: Sleep duration (hours), restorative quality, STOP-BANG / obstructive sleep apnea screening signs, Epworth sleepiness score
- *Other Labs (Exclusions / Differentials)*: LH/FSH ratio, AMH, prolactin, TSH

---

## Attention Scoring Math & Guideline Thresholds

Per domain, three signals are combined into a weighted composite score:

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
- **Insufficient Data**: When completeness falls below threshold

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

## Defensive LLM Reasoning & Hallucination Mitigation

To guarantee clinical safety with smaller or free-tier models (Groq Llama 3.3 70B):
1. **Restricted Payload**: The LLM prompt receives strictly computed values (deltas, scores, evidence, completeness ratios).
2. **Mandatory Non-Diagnostic Phrasing**: Prompt enforces tentative language (*"may be consistent with"*) and forbids diagnosis or treatment directives.
3. **JSON Mode Output**: `response_format: {"type": "json_object"}`.
4. **Code-Level Numerical Validation**: An automated verification pass regex-extracts every number from the generated narrative and confirms it exists in the input JSON payload. If any hallucinated number is detected, regeneration is triggered; if validation fails twice, the system safely falls back to a deterministic summary.

---

## API Contract (FastAPI v1)

All endpoints are versioned under `/api/v1` (with `/api` aliases for direct frontend compatibility):

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Clinician authentication |
| `GET` | `/api/v1/auth/me` | Current session profile |
| `GET` | `/api/v1/patients` | List all longitudinal patient records |
| `POST` | `/api/v1/patients` | Register new synthetic patient |
| `GET` | `/api/v1/patients/{id}` | Patient summary with all visit snapshots |
| `GET` | `/api/v1/patients/{id}/trends?parameter={param}` | Longitudinal trend points for Recharts |
| `POST` | `/api/v1/patients/{id}/visits` | Add encounter (form observations / notes) |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/deltas` | Clinical deltas vs previous visit |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/scores` | Domain scores, weights, citations, completeness |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/evidence/{domain}` | Raw observations backing domain score |
| `GET` | `/api/v1/patients/{id}/visits/{visit_id}/reasoning` | Validated reasoning narrative |
| `POST` | `/api/v1/extraction/lab-pdf` | Upload lab PDF/OCR for structured confirmation |

---

## Synthetic Personas (Rotterdam Phenotypes A–D)

Seed data includes 5 clinical personas with 3–4 longitudinal visits each:
- **P-0042 (Phenotype A - Classic)**: Hyperandrogenism + Ovulatory dysfunction + PCO morphology. High metabolic risk, worsening in Visit 2, turnaround under lifestyle intervention in Visits 3–4.
- **P-0017 (Phenotype B - Metabolic-Dominant)**: Hyperandrogenism + Anovulation. Profound insulin resistance, rapid weight/HOMA-IR improvement on lifestyle + metformin.
- **P-0023 (Phenotype C - Ovulatory PCOS)**: Hyperandrogenism + PCO morphology with regular cycles, normal BMI, high anxiety/depression burden (PHQ-9 = 16, GAD-7 = 14) and sleep restriction.
- **P-0031 (Phenotype D - Non-Hyperandrogenic)**: Oligo-ovulation + PCO morphology, normal androgens, elevated LH:FSH ratio (3.1) and AMH (8.4 ng/mL).
- **P-0056 (Sparse / Missing Data Validation)**: Baseline visit complete; Visit 2 has $<60\%$ metabolic data (triggers `Insufficient Data` band); Visit 3 has partial hyperandrogenism data (triggers `partial` confidence with missing fields listed).

---

## Quickstart & Setup

### 1. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free-tier Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 2. Backend Setup & Test Suite
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
alembic upgrade head
cd ..

# Run full pytest suite (23 unit tests)
pytest backend/tests -v

# Start FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation will be available at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
In a separate terminal:
```bash
npm install
npm run dev
```

Visit `http://localhost:5173` to access the clinician dashboard.

**Clinician Demo Credentials:**
- Email: `dr.mehta@clinic.local`
- Password: `ClinicianDemo!2026`

---

## Known Limitations & Ethical Considerations

1. **Ethnic Variations in Metabolic Risk**:
   - Standard WHO BMI ($\ge 25$ overweight, $\ge 30$ obese) and waist circumference ($\ge 88$ cm) cutoffs systematically underestimate metabolic and cardiovascular risks in South Asian and East Asian populations.
   - This prototype includes an ethnicity-configurable profile in `scoring_config.yaml` using IDF / Asia-Pacific cutoffs (BMI $\ge 23$ overweight, $\ge 27.5$ obese, waist $\ge 80$ cm). Clinicians should review the active population profile.
2. **LLM Hallucination Risk**:
   - Free-tier LLMs may occasionally invent numbers or assert diagnostic claims. Our dual-layer protection (defensive prompting + code-level numerical validation pass) prevents unverified outputs from reaching the clinician.
3. **Data Privacy**:
   - All patient records in this repository are strictly synthetic. No protected health information (PHI) should ever be entered or processed.
