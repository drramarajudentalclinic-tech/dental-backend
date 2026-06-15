from flask import Blueprint, request, jsonify
from database import db
from models import MedicalHistory

medical_bp = Blueprint("medical", __name__)

# ── All valid DB column names ─────────────────────────────────────────────────
CONDITION_FIELDS = [
    "aids", "asthma", "arthritis_rheumatism", "blood_disease",
    "bp_high", "bp_low", "corticosteroid_treatment", "cancer",
    "diabetes", "epilepsy", "heart_problems", "hepatitis", "herpes",
    "jaundice", "liver_disease", "kidney_disease", "psychiatric_treatment",
    "radiation_treatment", "respiratory_disease", "rheumatic_fever", "tb",
    "thyroid_problems", "ulcer", "venereal_disease",
]

ALLOWED_FIELDS = CONDITION_FIELDS + ["other", "no_known_conditions"]

# ── Aliases: map any frontend key → DB column name ───────────────────────────
ALIASES = {
    # PascalCase from PatientMedical.jsx
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
    "AIDS":                     "aids",
    "Asthma":                   "asthma",
    "Cancer":                   "cancer",
    "Diabetes":                 "diabetes",
    "Epilepsy":                 "epilepsy",
    "Hepatitis":                "hepatitis",
    "Herpes":                   "herpes",
    "Jaundice":                 "jaundice",
    "TB":                       "tb",
    "Ulcer":                    "ulcer",
    "Other":                    "other",
    # "No Known" checkbox from PatientMedical.jsx
    "No_Known_Conditions":      "no_known_conditions",
    # Legacy / old route aliases
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
    if isinstance(val, bool): return val
    if isinstance(val, int):  return bool(val)
    if isinstance(val, str):  return val.strip().upper() in ("YES", "TRUE", "1")
    return False


# ── PUT /api/medical/<patient_id> ─────────────────────────────────────────────
@medical_bp.route("/medical/<int:patient_id>", methods=["PUT"])
def save_medical(patient_id):
    data = request.get_json() or {}

    # ── Mandatory acknowledgement check ──────────────────────────────────────
    has_condition = any(
        to_bool(data.get(f) or data.get(raw))
        for f in CONDITION_FIELDS
        for raw in ([f] + [k for k, v in ALIASES.items() if v == f])
    )
    has_other = bool(
        (data.get("other") or data.get("Other") or data.get("other_conditions") or "").strip()
    )
    no_known = to_bool(
        data.get("no_known_conditions") or data.get("No_Known_Conditions")
    )

    if not has_condition and not has_other and not no_known:
        return jsonify({
            "error": "Medical history acknowledgement required. "
                     "Select at least one condition or confirm no known conditions."
        }), 400
    # ─────────────────────────────────────────────────────────────────────────

    record = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    if not record:
        record = MedicalHistory(patient_id=patient_id)
        db.session.add(record)

    # If "No Known Conditions" confirmed → clear all conditions
    if no_known:
        for f in CONDITION_FIELDS:
            setattr(record, f, False)
        record.other              = None
        record.no_known_conditions = True
        db.session.commit()
        return jsonify({"status": "medical history saved", "patient_id": patient_id}), 200

    for raw_key, val in data.items():
        db_key = ALIASES.get(raw_key, raw_key)
        if db_key not in ALLOWED_FIELDS:
            continue
        if db_key == "other":
            setattr(record, db_key, str(val) if val else None)
        elif db_key == "no_known_conditions":
            setattr(record, db_key, to_bool(val))
        else:
            setattr(record, db_key, to_bool(val))

    record.no_known_conditions = False  # at least one condition was set

    db.session.commit()
    return jsonify({"status": "medical history saved", "patient_id": patient_id}), 200


# ── GET /api/medical/<patient_id> ─────────────────────────────────────────────
@medical_bp.route("/medical/<int:patient_id>", methods=["GET"])
def get_medical(patient_id):
    record = MedicalHistory.query.filter_by(patient_id=patient_id).first()

    if not record:
        return jsonify({
            **{field: False for field in CONDITION_FIELDS},
            "other": None,
            "no_known_conditions": False,
        }), 200

    return jsonify(record.to_dict()), 200