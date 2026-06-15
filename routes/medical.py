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
    """Convert YES/NO/1/0/True/False/None → Python bool."""
    if val is None:           return False
    if isinstance(val, bool): return val
    if isinstance(val, int):  return bool(val)
    if isinstance(val, str):  return val.strip().upper() in ("YES", "TRUE", "1")
    return False


def _resolve_key(raw_key):
    """Return the DB column name for any incoming key, or None if not allowed."""
    db_key = ALIASES.get(raw_key, raw_key)
    return db_key if db_key in ALLOWED_FIELDS else None


def _check_has_condition(data):
    """
    Return True if any condition field in data resolves to a truthy bool.
    Checks both snake_case DB keys and PascalCase frontend keys via ALIASES.
    """
    for raw_key, val in data.items():
        db_key = _resolve_key(raw_key)
        if db_key and db_key in CONDITION_FIELDS and to_bool(val):
            return True
    return False


# ── PUT /api/medical/<patient_id> ─────────────────────────────────────────────
@medical_bp.route("/medical/<int:patient_id>", methods=["PUT"])
def save_medical(patient_id):
    try:
        data = request.get_json(silent=True) or {}

        # ── Mandatory acknowledgement check ──────────────────────────────────
        has_condition = _check_has_condition(data)

        has_other = bool(
            str(data.get("other") or data.get("Other") or data.get("other_conditions") or "").strip()
        )

        no_known = to_bool(
            data.get("No_Known_Conditions") if "No_Known_Conditions" in data
            else data.get("no_known_conditions")
        )

        if not has_condition and not has_other and not no_known:
            return jsonify({
                "error": "Medical history acknowledgement required. "
                         "Select at least one condition or confirm no known conditions."
            }), 400
        # ─────────────────────────────────────────────────────────────────────

        record = MedicalHistory.query.filter_by(patient_id=patient_id).first()
        if not record:
            record = MedicalHistory(patient_id=patient_id)
            db.session.add(record)

        # If "No Known Conditions" confirmed → clear all conditions
        if no_known:
            for f in CONDITION_FIELDS:
                setattr(record, f, False)
            record.other               = None
            record.no_known_conditions = True
            db.session.commit()
            return jsonify({"status": "medical history saved", "patient_id": patient_id}), 200

        # Apply each incoming field to the record
        for raw_key, val in data.items():
            db_key = _resolve_key(raw_key)
            if not db_key:
                continue
            if db_key == "other":
                setattr(record, db_key, str(val).strip() if val else None)
            else:
                setattr(record, db_key, to_bool(val))

        record.no_known_conditions = False  # at least one condition was set

        db.session.commit()
        return jsonify({"status": "medical history saved", "patient_id": patient_id}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()          # prints full stack trace to Render logs
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


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