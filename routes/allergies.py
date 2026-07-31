from flask import Blueprint, request, jsonify
from database import db
from models import AllergyRecord, Patient

allergy_bp = Blueprint("allergy", __name__)

# ──────────────────────────────────────────────────────────────────────────
# NOTE ON SCHEMA:
# AllergyRecord used to be a free-form, multi-row model (type/allergen/
# reaction/severity/notes — one row per allergy). That shape was never
# actually produced by any frontend: PatientAllergy.jsx is a flat Yes/No
# checklist (drug/food/latex/iodine/anesthesia allergy + free-text
# "other"), one record per patient — matching patients.py's save_allergy()/
# get_allergy() routes at /api/patients/<id>/allergy. AllergyRecord has
# been migrated to that flat schema; these routes are rewritten to match.
#
# This also drops the dependency on Patient.no_known_allergies (a second,
# separate flag that could disagree with AllergyRecord's own flag) in
# favor of the single source of truth: AllergyRecord.no_known_allergies.
# ──────────────────────────────────────────────────────────────────────────


# ── GET /api/allergies/<patient_id> ─────────────────────────────────────
@allergy_bp.route("/allergies/<int:patient_id>", methods=["GET"])
def get_allergy(patient_id):
    Patient.query.get_or_404(patient_id)
    record = AllergyRecord.query.filter_by(patient_id=patient_id).first()
    if not record:
        return jsonify({
            "drug_allergy": False, "food_allergy": False, "latex_allergy": False,
            "iodine_allergy": False, "anesthesia_allergy": False,
            "other_allergy": "", "no_known_allergies": False,
        }), 200
    return jsonify(record.to_dict()), 200

@allergy_bp.route("/allergies/<int:patient_id>", methods=["POST", "PUT"])
def save_allergy(patient_id):
    Patient.query.get_or_404(patient_id)

    data = request.get_json() or {}

    no_known = bool(data.get("no_known_allergies"))

    other_text = data.get("other_allergy")
    has_other = bool(other_text.strip()) if isinstance(other_text, str) else bool(other_text)

    has_any = any([
        data.get("drug_allergy"),
        data.get("food_allergy"),
        data.get("latex_allergy"),
        data.get("iodine_allergy"),
        data.get("anesthesia_allergy"),
        has_other,
    ])

    if not has_any and not no_known:
        return jsonify({
            "error": "Please select at least one allergy or confirm No Known Allergies."
        }), 400

    record = AllergyRecord.query.filter_by(patient_id=patient_id).first()

    if not record:
        record = AllergyRecord(patient_id=patient_id)
        db.session.add(record)

    if no_known:
        record.drug_allergy = False
        record.food_allergy = False
        record.latex_allergy = False
        record.iodine_allergy = False
        record.anesthesia_allergy = False
        record.other_allergy = None
        record.no_known_allergies = True

        # NEW
        record.allergen = None
        record.reaction = None
        record.severity = None
        record.notes = None

    else:
        record.drug_allergy = bool(data.get("drug_allergy"))
        record.food_allergy = bool(data.get("food_allergy"))
        record.latex_allergy = bool(data.get("latex_allergy"))
        record.iodine_allergy = bool(data.get("iodine_allergy"))
        record.anesthesia_allergy = bool(data.get("anesthesia_allergy"))

        record.other_allergy = (
            (other_text or "").strip() or None
            if isinstance(other_text, str)
            else None
        )

        record.no_known_allergies = False

        # ⭐ SAVE THESE FIELDS
        record.allergen = data.get("allergen")
        record.reaction = data.get("reaction")
        record.severity = data.get("severity")
        record.notes = data.get("notes")

    db.session.commit()

    return jsonify(record.to_dict()), 200