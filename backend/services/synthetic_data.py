import math
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models.patient import Patient
from backend.models.visit import Visit
from backend.models.observation import DomainObservation
from backend.models.delta import ClinicalDeltaModel
from backend.models.score import DomainScoreModel

# Rotterdam Phenotype Definitions:
# Phenotype A: Hyperandrogenism + Ovulatory dysfunction + Polycystic ovaries (Classic PCOS)
# Phenotype B: Hyperandrogenism + Ovulatory dysfunction (Non-PCO PCOS)
# Phenotype C: Hyperandrogenism + Polycystic ovaries (Ovulatory PCOS)
# Phenotype D: Ovulatory dysfunction + Polycystic ovaries (Non-hyperandrogenic PCOS)

SYNTHETIC_PERSONAS = [
    {
        "id": "P-0042",
        "synthetic_cohort_label": "Phenotype A (Classic PCOS - Hyperandrogenic, Anovulatory, High Metabolic Risk)",
        "age": 27,
        "notes": "Classic Rotterdam Phenotype A. Longitudinal follow-up across 4 visits. Shows worsening cardiometabolic markers in V2, then stabilizing after clinical lifestyle counsel in V3-V4.",
        "height_m": 1.63,
        "visits": [
            {
                "visit_number": 1,
                "visit_date": "2025-06-15",
                "source_type": "Comprehensive Intake",
                "data": {
                    # Reproductive
                    "cycle_length": (36.0, "days"),
                    "cycle_variability_sd": (8.5, "days"),
                    "missed_periods_count": (3.0, "periods"),
                    "ovulation_signs": (0.0, "binary"), # 0 = absent / infrequent
                    # Hyperandrogenism
                    "total_testosterone": (0.62, "ng/mL"),
                    "free_testosterone": (6.4, "pg/mL"),
                    "dheas": (310.0, "ug/dL"),
                    "shbg": (26.0, "nmol/L"),
                    "hirsutism_mfg_score": (9.0, "score"),
                    "acne_severity": (2.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    # Metabolic
                    "weight": (68.0, "kg"),
                    "waist_circumference": (82.0, "cm"),
                    "fasting_glucose": (94.0, "mg/dL"),
                    "fasting_insulin": (14.0, "uIU/mL"),
                    "hba1c": (5.4, "%"),
                    "systolic_bp": (118.0, "mmHg"),
                    "diastolic_bp": (76.0, "mmHg"),
                    "triglycerides": (142.0, "mg/dL"),
                    "hdl": (48.0, "mg/dL"),
                    "ldl": (122.0, "mg/dL"),
                    # Lifestyle
                    "activity_minutes_week": (120.0, "min/week"),
                    "diet_quality_score": (6.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (2.0, "drinks/week"),
                    # Psychological
                    "phq9_score": (7.0, "score"),
                    "gad7_score": (6.0, "score"),
                    # Sleep
                    "sleep_hours": (6.8, "hours"),
                    "sleep_quality_score": (6.0, "score"),
                    "snoring_or_apnea_signs": (1.0, "score"),
                    "daytime_sleepiness_epworth": (8.0, "score"),
                    # Other Labs
                    "lh_fsh_ratio": (2.4, "ratio"),
                    "amh": (6.8, "ng/mL"),
                    "prolactin": (14.2, "ng/mL"),
                    "tsh": (1.8, "uIU/mL"),
                }
            },
            {
                "visit_number": 2,
                "visit_date": "2025-10-18",
                "source_type": "Longitudinal Follow-up & Lab Encounter",
                "data": {
                    # Worsening weight, cycle length, HOMA-IR
                    "cycle_length": (44.0, "days"),
                    "cycle_variability_sd": (13.0, "days"),
                    "missed_periods_count": (5.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.74, "ng/mL"),
                    "free_testosterone": (7.8, "pg/mL"),
                    "dheas": (335.0, "ug/dL"),
                    "shbg": (22.0, "nmol/L"),
                    "hirsutism_mfg_score": (11.0, "score"),
                    "acne_severity": (3.0, "grade"),
                    "hair_loss_severity": (2.0, "grade"),
                    "weight": (71.5, "kg"), # +3.5 kg -> meaningful delta!
                    "waist_circumference": (85.5, "cm"),
                    "fasting_glucose": (104.0, "mg/dL"), # +10 mg/dL -> meaningful delta!
                    "fasting_insulin": (19.0, "uIU/mL"), # +5 uIU/mL -> meaningful delta!
                    "hba1c": (5.8, "%"), # +0.4% -> meaningful delta!
                    "systolic_bp": (126.0, "mmHg"),
                    "diastolic_bp": (82.0, "mmHg"),
                    "triglycerides": (175.0, "mg/dL"),
                    "hdl": (44.0, "mg/dL"),
                    "ldl": (138.0, "mg/dL"),
                    "activity_minutes_week": (60.0, "min/week"),
                    "diet_quality_score": (4.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (3.0, "drinks/week"),
                    "phq9_score": (11.0, "score"), # moderate depressive screen
                    "gad7_score": (9.0, "score"),
                    "sleep_hours": (5.8, "hours"),
                    "sleep_quality_score": (4.0, "score"),
                    "snoring_or_apnea_signs": (2.0, "score"),
                    "daytime_sleepiness_epworth": (11.0, "score"),
                    "lh_fsh_ratio": (2.6, "ratio"),
                    "amh": (7.2, "ng/mL"),
                    "prolactin": (15.0, "ng/mL"),
                    "tsh": (1.9, "uIU/mL"),
                }
            },
            {
                "visit_number": 3,
                "visit_date": "2026-03-10",
                "source_type": "Progress Review",
                "data": {
                    # Beginning of turnaround with lifestyle interventions
                    "cycle_length": (39.0, "days"),
                    "cycle_variability_sd": (9.0, "days"),
                    "missed_periods_count": (4.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.68, "ng/mL"),
                    "free_testosterone": (6.9, "pg/mL"),
                    "dheas": (315.0, "ug/dL"),
                    "shbg": (25.0, "nmol/L"),
                    "hirsutism_mfg_score": (10.0, "score"),
                    "acne_severity": (2.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    "weight": (69.8, "kg"), # -1.7 kg
                    "waist_circumference": (83.5, "cm"),
                    "fasting_glucose": (98.0, "mg/dL"),
                    "fasting_insulin": (16.0, "uIU/mL"),
                    "hba1c": (5.6, "%"),
                    "systolic_bp": (122.0, "mmHg"),
                    "diastolic_bp": (78.0, "mmHg"),
                    "triglycerides": (155.0, "mg/dL"),
                    "hdl": (46.0, "mg/dL"),
                    "ldl": (130.0, "mg/dL"),
                    "activity_minutes_week": (140.0, "min/week"),
                    "diet_quality_score": (6.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (8.0, "score"),
                    "gad7_score": (7.0, "score"),
                    "sleep_hours": (6.5, "hours"),
                    "sleep_quality_score": (6.0, "score"),
                    "snoring_or_apnea_signs": (1.0, "score"),
                    "daytime_sleepiness_epworth": (9.0, "score"),
                    "lh_fsh_ratio": (2.2, "ratio"),
                    "amh": (6.5, "ng/mL"),
                    "prolactin": (13.8, "ng/mL"),
                    "tsh": (1.7, "uIU/mL"),
                }
            },
            {
                "visit_number": 4,
                "visit_date": "2026-09-18",
                "source_type": "Annual Comprehensive Evaluation",
                "data": {
                    "cycle_length": (34.0, "days"),
                    "cycle_variability_sd": (5.0, "days"),
                    "missed_periods_count": (2.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.54, "ng/mL"),
                    "free_testosterone": (5.2, "pg/mL"),
                    "dheas": (280.0, "ug/dL"),
                    "shbg": (32.0, "nmol/L"),
                    "hirsutism_mfg_score": (8.0, "score"),
                    "acne_severity": (1.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    "weight": (67.2, "kg"), # -2.6 kg -> meaningful delta!
                    "waist_circumference": (81.0, "cm"),
                    "fasting_glucose": (91.0, "mg/dL"),
                    "fasting_insulin": (11.5, "uIU/mL"),
                    "hba1c": (5.3, "%"),
                    "systolic_bp": (116.0, "mmHg"),
                    "diastolic_bp": (74.0, "mmHg"),
                    "triglycerides": (128.0, "mg/dL"),
                    "hdl": (52.0, "mg/dL"),
                    "ldl": (115.0, "mg/dL"),
                    "activity_minutes_week": (180.0, "min/week"),
                    "diet_quality_score": (8.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (4.0, "score"),
                    "gad7_score": (4.0, "score"),
                    "sleep_hours": (7.4, "hours"),
                    "sleep_quality_score": (8.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                    "lh_fsh_ratio": (1.7, "ratio"),
                    "amh": (5.4, "ng/mL"),
                    "prolactin": (12.5, "ng/mL"),
                    "tsh": (1.6, "uIU/mL"),
                }
            }
        ]
    },
    {
        "id": "P-0017",
        "synthetic_cohort_label": "Phenotype B (Metabolic-Dominant PCOS - Anovulatory & Hyperandrogenic)",
        "age": 24,
        "notes": "Rotterdam Phenotype B without polycystic ovarian morphology on ultrasound. Characterized by profound insulin resistance, elevated BMI, and prominent acanthosis nigricans. Rapid improvement under combined lifestyle and insulin-sensitizing therapy.",
        "height_m": 1.60,
        "visits": [
            {
                "visit_number": 1,
                "visit_date": "2025-08-01",
                "source_type": "Initial Assessment",
                "data": {
                    "cycle_length": (62.0, "days"),
                    "cycle_variability_sd": (18.0, "days"),
                    "missed_periods_count": (7.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.69, "ng/mL"),
                    "free_testosterone": (7.5, "pg/mL"),
                    "dheas": (340.0, "ug/dL"),
                    "shbg": (18.0, "nmol/L"),
                    "hirsutism_mfg_score": (12.0, "score"),
                    "acne_severity": (3.0, "grade"),
                    "hair_loss_severity": (2.0, "grade"),
                    "weight": (84.0, "kg"),
                    "waist_circumference": (94.0, "cm"),
                    "fasting_glucose": (112.0, "mg/dL"),
                    "fasting_insulin": (24.0, "uIU/mL"),
                    "hba1c": (6.1, "%"),
                    "systolic_bp": (134.0, "mmHg"),
                    "diastolic_bp": (86.0, "mmHg"),
                    "triglycerides": (210.0, "mg/dL"),
                    "hdl": (38.0, "mg/dL"),
                    "ldl": (148.0, "mg/dL"),
                    "activity_minutes_week": (30.0, "min/week"),
                    "diet_quality_score": (3.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (14.0, "score"),
                    "gad7_score": (11.0, "score"),
                    "sleep_hours": (5.5, "hours"),
                    "sleep_quality_score": (3.0, "score"),
                    "snoring_or_apnea_signs": (2.0, "score"),
                    "daytime_sleepiness_epworth": (13.0, "score"),
                    "lh_fsh_ratio": (1.9, "ratio"),
                    "amh": (4.8, "ng/mL"),
                    "prolactin": (16.0, "ng/mL"),
                    "tsh": (2.1, "uIU/mL"),
                }
            },
            {
                "visit_number": 2,
                "visit_date": "2025-12-10",
                "source_type": "Follow-up",
                "data": {
                    "cycle_length": (50.0, "days"),
                    "cycle_variability_sd": (12.0, "days"),
                    "missed_periods_count": (5.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.58, "ng/mL"),
                    "free_testosterone": (5.9, "pg/mL"),
                    "dheas": (295.0, "ug/dL"),
                    "shbg": (24.0, "nmol/L"),
                    "hirsutism_mfg_score": (10.0, "score"),
                    "acne_severity": (2.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    "weight": (80.5, "kg"), # -3.5 kg -> clinically meaningful!
                    "waist_circumference": (89.5, "cm"),
                    "fasting_glucose": (101.0, "mg/dL"),
                    "fasting_insulin": (17.5, "uIU/mL"),
                    "hba1c": (5.8, "%"),
                    "systolic_bp": (126.0, "mmHg"),
                    "diastolic_bp": (80.0, "mmHg"),
                    "triglycerides": (172.0, "mg/dL"),
                    "hdl": (42.0, "mg/dL"),
                    "ldl": (132.0, "mg/dL"),
                    "activity_minutes_week": (110.0, "min/week"),
                    "diet_quality_score": (5.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (0.0, "drinks/week"),
                    "phq9_score": (10.0, "score"),
                    "gad7_score": (8.0, "score"),
                    "sleep_hours": (6.5, "hours"),
                    "sleep_quality_score": (5.0, "score"),
                    "snoring_or_apnea_signs": (1.0, "score"),
                    "daytime_sleepiness_epworth": (9.0, "score"),
                    "lh_fsh_ratio": (1.6, "ratio"),
                    "amh": (4.2, "ng/mL"),
                    "prolactin": (14.5, "ng/mL"),
                    "tsh": (1.9, "uIU/mL"),
                }
            },
            {
                "visit_number": 3,
                "visit_date": "2026-05-15",
                "source_type": "Progress Review",
                "data": {
                    "cycle_length": (38.0, "days"),
                    "cycle_variability_sd": (6.5, "days"),
                    "missed_periods_count": (2.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.46, "ng/mL"),
                    "free_testosterone": (4.4, "pg/mL"),
                    "dheas": (255.0, "ug/dL"),
                    "shbg": (32.0, "nmol/L"),
                    "hirsutism_mfg_score": (7.0, "score"),
                    "acne_severity": (1.0, "grade"),
                    "hair_loss_severity": (0.0, "grade"),
                    "weight": (76.8, "kg"), # -3.7 kg
                    "waist_circumference": (84.0, "cm"),
                    "fasting_glucose": (92.0, "mg/dL"),
                    "fasting_insulin": (12.0, "uIU/mL"),
                    "hba1c": (5.4, "%"),
                    "systolic_bp": (118.0, "mmHg"),
                    "diastolic_bp": (76.0, "mmHg"),
                    "triglycerides": (135.0, "mg/dL"),
                    "hdl": (48.0, "mg/dL"),
                    "ldl": (118.0, "mg/dL"),
                    "activity_minutes_week": (160.0, "min/week"),
                    "diet_quality_score": (7.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (0.0, "drinks/week"),
                    "phq9_score": (6.0, "score"),
                    "gad7_score": (5.0, "score"),
                    "sleep_hours": (7.2, "hours"),
                    "sleep_quality_score": (7.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                    "lh_fsh_ratio": (1.4, "ratio"),
                    "amh": (3.8, "ng/mL"),
                    "prolactin": (13.0, "ng/mL"),
                    "tsh": (1.8, "uIU/mL"),
                }
            }
        ]
    },
    {
        "id": "P-0023",
        "synthetic_cohort_label": "Phenotype C (Ovulatory PCOS - Hyperandrogenic, PCO Morphology, High Psychological Burden)",
        "age": 30,
        "notes": "Rotterdam Phenotype C with regular/borderline ovulatory cycles but marked hyperandrogenemia, hirsutism, cystic acne, and severe psychological distress (anxiety/depression) exacerbated by sleep disturbances.",
        "height_m": 1.68,
        "visits": [
            {
                "visit_number": 1,
                "visit_date": "2025-07-20",
                "source_type": "Initial Assessment",
                "data": {
                    "cycle_length": (31.0, "days"),
                    "cycle_variability_sd": (2.5, "days"),
                    "missed_periods_count": (0.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.64, "ng/mL"),
                    "free_testosterone": (6.0, "pg/mL"),
                    "dheas": (310.0, "ug/dL"),
                    "shbg": (35.0, "nmol/L"),
                    "hirsutism_mfg_score": (8.0, "score"),
                    "acne_severity": (3.0, "grade"),
                    "hair_loss_severity": (2.0, "grade"),
                    "weight": (61.5, "kg"),
                    "waist_circumference": (73.0, "cm"),
                    "fasting_glucose": (88.0, "mg/dL"),
                    "fasting_insulin": (8.5, "uIU/mL"),
                    "hba1c": (5.1, "%"),
                    "systolic_bp": (112.0, "mmHg"),
                    "diastolic_bp": (70.0, "mmHg"),
                    "triglycerides": (98.0, "mg/dL"),
                    "hdl": (58.0, "mg/dL"),
                    "ldl": (102.0, "mg/dL"),
                    "activity_minutes_week": (100.0, "min/week"),
                    "diet_quality_score": (6.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (3.0, "drinks/week"),
                    "phq9_score": (16.0, "score"), # Moderately severe depression screen!
                    "gad7_score": (14.0, "score"), # Moderate-to-severe anxiety screen!
                    "sleep_hours": (5.0, "hours"), # Severe sleep restriction
                    "sleep_quality_score": (3.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (12.0, "score"),
                    "lh_fsh_ratio": (1.8, "ratio"),
                    "amh": (5.8, "ng/mL"),
                    "prolactin": (15.5, "ng/mL"),
                    "tsh": (1.5, "uIU/mL"),
                }
            },
            {
                "visit_number": 2,
                "visit_date": "2025-11-25",
                "source_type": "Mental Health & Clinical Check-in",
                "data": {
                    "cycle_length": (32.0, "days"),
                    "cycle_variability_sd": (2.0, "days"),
                    "missed_periods_count": (0.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.61, "ng/mL"),
                    "free_testosterone": (5.8, "pg/mL"),
                    "dheas": (295.0, "ug/dL"),
                    "shbg": (36.0, "nmol/L"),
                    "hirsutism_mfg_score": (8.0, "score"),
                    "acne_severity": (2.0, "grade"),
                    "hair_loss_severity": (2.0, "grade"),
                    "weight": (61.0, "kg"),
                    "waist_circumference": (72.5, "cm"),
                    "fasting_glucose": (89.0, "mg/dL"),
                    "fasting_insulin": (8.0, "uIU/mL"),
                    "hba1c": (5.1, "%"),
                    "systolic_bp": (110.0, "mmHg"),
                    "diastolic_bp": (68.0, "mmHg"),
                    "triglycerides": (95.0, "mg/dL"),
                    "hdl": (60.0, "mg/dL"),
                    "ldl": (98.0, "mg/dL"),
                    "activity_minutes_week": (120.0, "min/week"),
                    "diet_quality_score": (6.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (11.0, "score"), # -5 points improvement under counseling
                    "gad7_score": (9.0, "score"),  # -5 points improvement
                    "sleep_hours": (6.2, "hours"),
                    "sleep_quality_score": (5.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (9.0, "score"),
                    "lh_fsh_ratio": (1.7, "ratio"),
                    "amh": (5.5, "ng/mL"),
                    "prolactin": (14.0, "ng/mL"),
                    "tsh": (1.6, "uIU/mL"),
                }
            },
            {
                "visit_number": 3,
                "visit_date": "2026-04-12",
                "source_type": "Comprehensive Follow-up",
                "data": {
                    "cycle_length": (30.0, "days"),
                    "cycle_variability_sd": (1.5, "days"),
                    "missed_periods_count": (0.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.50, "ng/mL"),
                    "free_testosterone": (4.6, "pg/mL"),
                    "dheas": (265.0, "ug/dL"),
                    "shbg": (42.0, "nmol/L"),
                    "hirsutism_mfg_score": (6.0, "score"),
                    "acne_severity": (1.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    "weight": (60.8, "kg"),
                    "waist_circumference": (71.5, "cm"),
                    "fasting_glucose": (86.0, "mg/dL"),
                    "fasting_insulin": (7.0, "uIU/mL"),
                    "hba1c": (5.0, "%"),
                    "systolic_bp": (108.0, "mmHg"),
                    "diastolic_bp": (68.0, "mmHg"),
                    "triglycerides": (90.0, "mg/dL"),
                    "hdl": (62.0, "mg/dL"),
                    "ldl": (95.0, "mg/dL"),
                    "activity_minutes_week": (150.0, "min/week"),
                    "diet_quality_score": (7.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (6.0, "score"),
                    "gad7_score": (5.0, "score"),
                    "sleep_hours": (7.0, "hours"),
                    "sleep_quality_score": (7.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                    "lh_fsh_ratio": (1.5, "ratio"),
                    "amh": (5.1, "ng/mL"),
                    "prolactin": (13.0, "ng/mL"),
                    "tsh": (1.5, "uIU/mL"),
                }
            }
        ]
    },
    {
        "id": "P-0031",
        "synthetic_cohort_label": "Phenotype D (Non-Hyperandrogenic PCOS - Anovulatory & PCO Morphology)",
        "age": 29,
        "notes": "Rotterdam Phenotype D without biochemical or clinical hyperandrogenism. Normal androgens, but marked oligomenorrhea, elevated AMH, high LH:FSH ratio, and high cycle variability.",
        "height_m": 1.65,
        "visits": [
            {
                "visit_number": 1,
                "visit_date": "2025-09-01",
                "source_type": "Gynecology Consultation",
                "data": {
                    "cycle_length": (54.0, "days"),
                    "cycle_variability_sd": (16.0, "days"),
                    "missed_periods_count": (6.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.32, "ng/mL"), # Normal female range
                    "free_testosterone": (2.4, "pg/mL"),  # Normal female range
                    "dheas": (160.0, "ug/dL"),           # Normal
                    "shbg": (48.0, "nmol/L"),            # Normal
                    "hirsutism_mfg_score": (2.0, "score"), # Normal (no hirsutism)
                    "acne_severity": (0.0, "grade"),
                    "hair_loss_severity": (0.0, "grade"),
                    "weight": (63.0, "kg"),
                    "waist_circumference": (75.0, "cm"),
                    "fasting_glucose": (89.0, "mg/dL"),
                    "fasting_insulin": (8.0, "uIU/mL"),
                    "hba1c": (5.1, "%"),
                    "systolic_bp": (114.0, "mmHg"),
                    "diastolic_bp": (72.0, "mmHg"),
                    "triglycerides": (105.0, "mg/dL"),
                    "hdl": (55.0, "mg/dL"),
                    "ldl": (110.0, "mg/dL"),
                    "activity_minutes_week": (130.0, "min/week"),
                    "diet_quality_score": (7.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (6.0, "score"),
                    "gad7_score": (5.0, "score"),
                    "sleep_hours": (7.0, "hours"),
                    "sleep_quality_score": (6.5, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                    "lh_fsh_ratio": (3.1, "ratio"), # High LH:FSH characteristic of non-androgenic PCOS
                    "amh": (8.4, "ng/mL"),          # Elevated
                    "prolactin": (14.0, "ng/mL"),
                    "tsh": (1.8, "uIU/mL"),
                }
            },
            {
                "visit_number": 2,
                "visit_date": "2026-02-14",
                "source_type": "Ovulation Induction Planning",
                "data": {
                    "cycle_length": (52.0, "days"),
                    "cycle_variability_sd": (14.0, "days"),
                    "missed_periods_count": (5.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.34, "ng/mL"),
                    "free_testosterone": (2.6, "pg/mL"),
                    "dheas": (165.0, "ug/dL"),
                    "shbg": (46.0, "nmol/L"),
                    "hirsutism_mfg_score": (2.0, "score"),
                    "acne_severity": (0.0, "grade"),
                    "hair_loss_severity": (0.0, "grade"),
                    "weight": (63.2, "kg"),
                    "waist_circumference": (75.0, "cm"),
                    "fasting_glucose": (90.0, "mg/dL"),
                    "fasting_insulin": (8.2, "uIU/mL"),
                    "hba1c": (5.1, "%"),
                    "systolic_bp": (115.0, "mmHg"),
                    "diastolic_bp": (72.0, "mmHg"),
                    "triglycerides": (108.0, "mg/dL"),
                    "hdl": (54.0, "mg/dL"),
                    "ldl": (112.0, "mg/dL"),
                    "activity_minutes_week": (140.0, "min/week"),
                    "diet_quality_score": (7.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (7.0, "score"),
                    "gad7_score": (6.0, "score"),
                    "sleep_hours": (7.1, "hours"),
                    "sleep_quality_score": (6.5, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                    "lh_fsh_ratio": (2.9, "ratio"),
                    "amh": (8.1, "ng/mL"),
                    "prolactin": (13.5, "ng/mL"),
                    "tsh": (1.7, "uIU/mL"),
                }
            },
            {
                "visit_number": 3,
                "visit_date": "2026-08-20",
                "source_type": "Cycle Tracking Encounter",
                "data": {
                    "cycle_length": (42.0, "days"),
                    "cycle_variability_sd": (8.0, "days"),
                    "missed_periods_count": (3.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    "total_testosterone": (0.30, "ng/mL"),
                    "free_testosterone": (2.2, "pg/mL"),
                    "dheas": (155.0, "ug/dL"),
                    "shbg": (50.0, "nmol/L"),
                    "hirsutism_mfg_score": (2.0, "score"),
                    "acne_severity": (0.0, "grade"),
                    "hair_loss_severity": (0.0, "grade"),
                    "weight": (62.8, "kg"),
                    "waist_circumference": (74.0, "cm"),
                    "fasting_glucose": (88.0, "mg/dL"),
                    "fasting_insulin": (7.5, "uIU/mL"),
                    "hba1c": (5.0, "%"),
                    "systolic_bp": (112.0, "mmHg"),
                    "diastolic_bp": (70.0, "mmHg"),
                    "triglycerides": (100.0, "mg/dL"),
                    "hdl": (56.0, "mg/dL"),
                    "ldl": (108.0, "mg/dL"),
                    "activity_minutes_week": (150.0, "min/week"),
                    "diet_quality_score": (7.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (5.0, "score"),
                    "gad7_score": (4.0, "score"),
                    "sleep_hours": (7.3, "hours"),
                    "sleep_quality_score": (7.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (5.0, "score"),
                    "lh_fsh_ratio": (2.2, "ratio"),
                    "amh": (7.4, "ng/mL"),
                    "prolactin": (13.0, "ng/mL"),
                    "tsh": (1.7, "uIU/mL"),
                }
            }
        ]
    },
    {
        "id": "P-0056",
        "synthetic_cohort_label": "Sparse / Missing Data Cohort (Validation for Section 3B Guardrails)",
        "age": 26,
        "notes": "Special validation persona designed to test Section 3B missing data handling: Visit 1 has complete baseline data; Visit 2 has severe missingness in Metabolic domain (<60% fields measured -> Insufficient Data band); Visit 3 has partial missingness in Hyperandrogenism domain (75% fields measured -> partial confidence with listed missing fields).",
        "height_m": 1.62,
        "visits": [
            {
                "visit_number": 1,
                "visit_date": "2025-10-05",
                "source_type": "Baseline Assessment",
                "data": {
                    "cycle_length": (42.0, "days"),
                    "cycle_variability_sd": (9.0, "days"),
                    "missed_periods_count": (4.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    "total_testosterone": (0.58, "ng/mL"),
                    "free_testosterone": (5.5, "pg/mL"),
                    "dheas": (280.0, "ug/dL"),
                    "shbg": (28.0, "nmol/L"),
                    "hirsutism_mfg_score": (8.0, "score"),
                    "acne_severity": (2.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    "weight": (70.0, "kg"),
                    "waist_circumference": (84.0, "cm"),
                    "fasting_glucose": (95.0, "mg/dL"),
                    "fasting_insulin": (14.0, "uIU/mL"),
                    "hba1c": (5.5, "%"),
                    "systolic_bp": (120.0, "mmHg"),
                    "diastolic_bp": (78.0, "mmHg"),
                    "triglycerides": (150.0, "mg/dL"),
                    "hdl": (48.0, "mg/dL"),
                    "ldl": (125.0, "mg/dL"),
                    "activity_minutes_week": (100.0, "min/week"),
                    "diet_quality_score": (5.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (2.0, "drinks/week"),
                    "phq9_score": (8.0, "score"),
                    "gad7_score": (7.0, "score"),
                    "sleep_hours": (6.5, "hours"),
                    "sleep_quality_score": (6.0, "score"),
                    "snoring_or_apnea_signs": (1.0, "score"),
                    "daytime_sleepiness_epworth": (8.0, "score"),
                }
            },
            {
                "visit_number": 2,
                "visit_date": "2026-03-12",
                "source_type": "Self-Report Check-in (Labs Omitted)",
                "data": {
                    # Complete reproductive
                    "cycle_length": (45.0, "days"),
                    "cycle_variability_sd": (10.0, "days"),
                    "missed_periods_count": (4.0, "periods"),
                    "ovulation_signs": (0.0, "binary"),
                    # Complete lifestyle & psychological & sleep
                    "activity_minutes_week": (90.0, "min/week"),
                    "diet_quality_score": (5.0, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (2.0, "drinks/week"),
                    "phq9_score": (9.0, "score"),
                    "gad7_score": (8.0, "score"),
                    "sleep_hours": (6.0, "hours"),
                    "sleep_quality_score": (5.0, "score"),
                    "snoring_or_apnea_signs": (1.0, "score"),
                    "daytime_sleepiness_epworth": (8.0, "score"),
                    # METABOLIC: Only weight and waist measured. Fasting glucose, insulin, lipids NOT MEASURED!
                    # Total expected = 12 fields. Only 2 present -> ratio = 2/12 = 16.7% (<60% threshold!)
                    "weight": (71.0, "kg"),
                    "waist_circumference": (85.0, "cm"),
                },
                "unmeasured_reasons": {
                    "fasting_glucose": "lab_not_ordered",
                    "fasting_insulin": "lab_not_ordered",
                    "hba1c": "lab_not_ordered",
                    "triglycerides": "lab_not_ordered",
                    "hdl": "lab_not_ordered",
                    "ldl": "lab_not_ordered",
                    "systolic_bp": "remote_telehealth_visit",
                    "diastolic_bp": "remote_telehealth_visit",
                    "total_testosterone": "lab_not_ordered",
                    "free_testosterone": "lab_not_ordered",
                    "dheas": "lab_not_ordered",
                    "shbg": "lab_not_ordered",
                }
            },
            {
                "visit_number": 3,
                "visit_date": "2026-08-30",
                "source_type": "Partial Lab Encounter",
                "data": {
                    "cycle_length": (40.0, "days"),
                    "cycle_variability_sd": (7.0, "days"),
                    "missed_periods_count": (3.0, "periods"),
                    "ovulation_signs": (1.0, "binary"),
                    # Hyperandrogenism: 5 of 7 fields present (71% > 60% threshold -> partial confidence!)
                    # Missing: dheas, shbg
                    "total_testosterone": (0.52, "ng/mL"),
                    "free_testosterone": (5.0, "pg/mL"),
                    "hirsutism_mfg_score": (7.0, "score"),
                    "acne_severity": (1.0, "grade"),
                    "hair_loss_severity": (1.0, "grade"),
                    # Complete metabolic labs
                    "weight": (69.0, "kg"),
                    "waist_circumference": (83.0, "cm"),
                    "fasting_glucose": (92.0, "mg/dL"),
                    "fasting_insulin": (12.0, "uIU/mL"),
                    "hba1c": (5.3, "%"),
                    "systolic_bp": (118.0, "mmHg"),
                    "diastolic_bp": (76.0, "mmHg"),
                    "triglycerides": (138.0, "mg/dL"),
                    "hdl": (50.0, "mg/dL"),
                    "ldl": (118.0, "mg/dL"),
                    "activity_minutes_week": (130.0, "min/week"),
                    "diet_quality_score": (6.5, "score"),
                    "smoking_status": (0.0, "status"),
                    "alcohol_drinks_week": (1.0, "drinks/week"),
                    "phq9_score": (6.0, "score"),
                    "gad7_score": (5.0, "score"),
                    "sleep_hours": (7.0, "hours"),
                    "sleep_quality_score": (7.0, "score"),
                    "snoring_or_apnea_signs": (0.0, "score"),
                    "daytime_sleepiness_epworth": (6.0, "score"),
                },
                "unmeasured_reasons": {
                    "dheas": "reagent_shortage",
                    "shbg": "sample_hemolyzed"
                }
            }
        ]
    }
]

DOMAIN_MAPPING = {
    # Reproductive
    "cycle_length": "Reproductive",
    "cycle_variability_sd": "Reproductive",
    "missed_periods_count": "Reproductive",
    "ovulation_signs": "Reproductive",
    # Hyperandrogenism
    "total_testosterone": "Hyperandrogenism",
    "free_testosterone": "Hyperandrogenism",
    "dheas": "Hyperandrogenism",
    "shbg": "Hyperandrogenism",
    "hirsutism_mfg_score": "Hyperandrogenism",
    "acne_severity": "Hyperandrogenism",
    "hair_loss_severity": "Hyperandrogenism",
    # Metabolic
    "weight": "Metabolic",
    "bmi": "Metabolic",
    "waist_circumference": "Metabolic",
    "fasting_glucose": "Metabolic",
    "fasting_insulin": "Metabolic",
    "homa_ir": "Metabolic",
    "hba1c": "Metabolic",
    "systolic_bp": "Metabolic",
    "diastolic_bp": "Metabolic",
    "triglycerides": "Metabolic",
    "hdl": "Metabolic",
    "ldl": "Metabolic",
    # Lifestyle
    "activity_minutes_week": "Lifestyle",
    "diet_quality_score": "Lifestyle",
    "smoking_status": "Lifestyle",
    "alcohol_drinks_week": "Lifestyle",
    # Psychological
    "phq9_score": "Psychological",
    "gad7_score": "Psychological",
    # Sleep
    "sleep_hours": "Sleep",
    "sleep_quality_score": "Sleep",
    "snoring_or_apnea_signs": "Sleep",
    "daytime_sleepiness_epworth": "Sleep",
    # Other
    "lh_fsh_ratio": "Other",
    "amh": "Other",
    "prolactin": "Other",
    "tsh": "Other",
}

def seed_synthetic_patients(db: Session, force_recreate: bool = True) -> List[Patient]:
    """
    Seeds the SQLite database with 5 distinct synthetic personas:
    Phenotypes A, B, C, D, and a sparse/missing data persona for testing guardrails.
    """
    if force_recreate:
        # Clear existing synthetic records
        db.query(DomainScoreModel).delete()
        db.query(ClinicalDeltaModel).delete()
        db.query(DomainObservation).delete()
        db.query(Visit).delete()
        db.query(Patient).delete()
        db.commit()

    created_patients = []

    for persona in SYNTHETIC_PERSONAS:
        patient = Patient(
            id=persona["id"],
            synthetic_cohort_label=persona["synthetic_cohort_label"],
            age=persona["age"],
            notes=persona["notes"]
        )
        db.add(patient)
        db.flush()

        height_m = persona.get("height_m", 1.65)

        for visit_data in persona["visits"]:
            visit_id = f"v{visit_data['visit_number']}-{patient.id.lower()}"
            visit = Visit(
                id=visit_id,
                patient_id=patient.id,
                visit_number=visit_data["visit_number"],
                visit_date=visit_data["visit_date"],
                source_type=visit_data["source_type"],
                data_completeness=100.0,
                reasoning_narrative=""
            )
            db.add(visit)
            db.flush()

            data_dict = visit_data["data"]
            unmeasured_dict = visit_data.get("unmeasured_reasons", {})

            # Calculate computed fields: BMI, HOMA-IR
            if "weight" in data_dict and height_m > 0:
                wt_val = data_dict["weight"][0]
                bmi_val = round(wt_val / (height_m ** 2), 1)
                data_dict["bmi"] = (bmi_val, "kg/m2")

            if "fasting_glucose" in data_dict and "fasting_insulin" in data_dict:
                fg = data_dict["fasting_glucose"][0]
                fi = data_dict["fasting_insulin"][0]
                homa_ir_val = round((fg * fi) / 405.0, 2)
                data_dict["homa_ir"] = (homa_ir_val, "index")

            # Store observations
            for param, (val, unit) in data_dict.items():
                domain = DOMAIN_MAPPING.get(param, "Other")
                obs = DomainObservation(
                    id=f"obs-{uuid.uuid4().hex[:12]}",
                    visit_id=visit.id,
                    domain=domain,
                    parameter_name=param,
                    numeric_value=float(val),
                    text_value=str(val),
                    unit=unit,
                    date=visit.visit_date,
                    source="Lab report" if domain in ["Hyperandrogenism", "Other"] or param in ["fasting_glucose", "fasting_insulin", "hba1c", "triglycerides", "hdl", "ldl"] else ("Self report" if domain in ["Lifestyle", "Sleep", "Psychological"] else "Clinician entry"),
                    source_confidence="high",
                    measurement_status="VALUE_PRESENT",
                    reason_code=None,
                    flag="normal"
                )
                db.add(obs)

            # Store unmeasured parameters explicitly (Section 3B requirement!)
            for param, reason in unmeasured_dict.items():
                domain = DOMAIN_MAPPING.get(param, "Other")
                obs = DomainObservation(
                    id=f"obs-{uuid.uuid4().hex[:12]}",
                    visit_id=visit.id,
                    domain=domain,
                    parameter_name=param,
                    numeric_value=None,
                    text_value=None,
                    unit="",
                    date=visit.visit_date,
                    source="Clinician entry",
                    source_confidence="high",
                    measurement_status="NOT_MEASURED",
                    reason_code=reason,
                    flag=None
                )
                db.add(obs)

        created_patients.append(patient)

    db.commit()
    return created_patients
