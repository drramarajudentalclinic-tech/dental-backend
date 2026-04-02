from flask import Blueprint, request, jsonify
from database import db
from models import AllergyRecord

allergy_bp = Blueprint("allergy", __name__)


# ── PUT /api/allergies/<patient_id> ───────────────────────────────────────────
# Expects: { "rows": [ { type, allergen, reaction, severity, notes }, ... ] }
# Full replace — deletes all existing rows and re-inserts
@allergy_bp.route("/allergies/<int:patient_id>", methods=["POST", "PUT"])
def save_allergy(patient_id):
    data = request.get_json() or {}
    rows = data.get("rows", [])

    # Full replace
    AllergyRecord.query.filter_by(patient_id=patient_id).delete()

    for row in rows:
        if not row.get("type") and not row.get("allergen"):
            continue  # skip blank rows
        record = AllergyRecord(
            patient_id = patient_id,
            type       = row.get("type")     or None,
            allergen   = row.get("allergen") or None,
            reaction   = row.get("reaction") or None,
            severity   = row.get("severity") or None,
            notes      = row.get("notes")    or None,
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({"status": "allergies saved", "patient_id": patient_id}), 200


# ── GET /api/allergies/<patient_id> ───────────────────────────────────────────
@allergy_bp.route("/allergies/<int:patient_id>", methods=["GET"])
def get_allergy(patient_id):
    rows = AllergyRecord.query.filter_by(patient_id=patient_id).all()
    return jsonify({
        "rows": [
            {
                "id":       r.id,
                "type":     r.type,
                "allergen": r.allergen,
                "reaction": r.reaction,
                "severity": r.severity,
                "notes":    r.notes,
            }
            for r in rows
        ]
    }), 200