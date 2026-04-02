from flask import Blueprint, request, jsonify
from database import db
from models import MedicalHistory

medical_bp = Blueprint("medical", __name__)

# ── Field names MUST match MedicalHistory model columns exactly ──────────────
ALLOWED_FIELDS = [
    "aids",
    "asthma",
    "arthritis_rheumatism",
    "blood_disease",
    "bp_high",
    "bp_low",
    "corticosteroid_treatment",
    "cancer",
    "diabetes",
    "epilepsy",
    "heart_problems",
    "hepatitis",
    "herpes",
    "jaundice",
    "liver_disease",
    "kidney_disease",
    "psychiatric_treatment",
    "radiation_treatment",
    "respiratory_disease",
    "rheumatic_fever",
    "tb",
    "thyroid_problems",
    "ulcer",
    "venereal_disease",
    "other",
]

# ── Aliases: map any reception-form key → DB column name ─────────────────────
ALIASES = {
    "Blood_Pressure_High":      "bp_high",
    "Blood_Pressure_Low":       "bp_low",
    "Blood_Disease":            "blood_disease",
    "Arthritis_Rheumatism":     "arthritis_rheumatism",
    "Corticosteroid_Treatment": "corticosteroid_treatment",
    "Heart_Problems":           "heart_problems",
    "Kidney_Disease":           "kidney_disease",
    "Liver_Disease":            "liver_disease",
    "Psychiatric_Treatment":    "psychiatric_treatment",
    "Radiation_Treatment":      "radiation_treatment",
    "Respiratory_Disease":      "respiratory_disease",
    "Rheumatic_Fever":          "rheumatic_fever",
    "Thyroid_Problems":         "thyroid_problems",
    "Venereal_Disease":         "venereal_disease",
    "Aids":       "aids",
    "Asthma":     "asthma",
    "Cancer":     "cancer",
    "Diabetes":   "diabetes",
    "Epilepsy":   "epilepsy",
    "Hepatitis":  "hepatitis",
    "Herpes":     "herpes",
    "Jaundice":   "jaundice",
    "Tb":         "tb",
    "Ulcer":      "ulcer",
    # Old route aliases (in case old data still comes in)
    "aids_hiv":               "aids",
    "cardiac_problem":        "heart_problems",
    "bp_high_low":            "bp_high",
    "hypertension":           "bp_high",
    "other_conditions":       "other",
    "corticosteroid_therapy": "corticosteroid_treatment",
    "radiation_therapy":      "radiation_treatment",
    "tuberculosis":           "tb",
}

def to_bool(val):
    """Convert YES/NO/1/0/True/False → Python bool."""
    if isinstance(val, bool):  return val
    if isinstance(val, int):   return bool(val)
    if isinstance(val, str):   return val.strip().upper() in ("YES", "TRUE", "1")
    return False


# ── PUT /api/medical/<patient_id> ─────────────────────────────────────────────
@medical_bp.route("/medical/<int:patient_id>", methods=["PUT"])
def save_medical(patient_id):
    data = request.get_json() or {}

    record = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    if not record:
        record = MedicalHistory(patient_id=patient_id)
        db.session.add(record)

    for raw_key, val in data.items():
        # Resolve alias if needed
        db_key = ALIASES.get(raw_key, raw_key)
        if db_key in ALLOWED_FIELDS:
            # "other" / "other_conditions" is a text field — don't cast to bool
            if db_key == "other":
                setattr(record, db_key, str(val) if val else None)
            else:
                setattr(record, db_key, to_bool(val))

    db.session.commit()
    return jsonify({"status": "medical history saved", "patient_id": patient_id}), 200


# ── GET /api/medical/<patient_id> ─────────────────────────────────────────────
@medical_bp.route("/medical/<int:patient_id>", methods=["GET"])
def get_medical(patient_id):
    record = MedicalHistory.query.filter_by(patient_id=patient_id).first()

    if not record:
        return jsonify({field: False for field in ALLOWED_FIELDS}), 200

    return jsonify({
        field: getattr(record, field, False)
        for field in ALLOWED_FIELDS
    }), 200