from flask import Blueprint, request, jsonify
from database import db
from models import AllergyRecord, Patient

allergy_bp = Blueprint("allergy", __name__)


# ============================================================
# GET ALL ALLERGIES OF A PATIENT
# ============================================================
@allergy_bp.route("/allergies/<int:patient_id>", methods=["GET"])
def get_allergies(patient_id):

    Patient.query.get_or_404(patient_id)

    allergies = AllergyRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(AllergyRecord.id.asc()).all()

    return jsonify({
        "rows": [a.to_dict() for a in allergies]
    }), 200


# ============================================================
# SAVE ALLERGIES
# ============================================================
@allergy_bp.route("/allergies/<int:patient_id>", methods=["POST", "PUT"])
def save_allergies(patient_id):

    Patient.query.get_or_404(patient_id)

    data = request.get_json() or {}

    rows = data.get("rows", [])

    # Delete existing allergies
    AllergyRecord.query.filter_by(
        patient_id=patient_id
    ).delete()

    for row in rows:

        allergen = (row.get("allergen") or "").strip()

        if allergen == "":
            continue

        allergy = AllergyRecord(
            patient_id=patient_id,
            allergy_type=row.get("type", ""),
            allergen=allergen,
            reaction=row.get("reaction", ""),
            severity=row.get("severity", ""),
            notes=row.get("notes", "")
        )

        db.session.add(allergy)

    db.session.commit()

    allergies = AllergyRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(AllergyRecord.id.asc()).all()

    return jsonify({
        "message": "Allergies saved successfully",
        "rows": [a.to_dict() for a in allergies]
    }), 200


# ============================================================
# ADD SINGLE ALLERGY
# ============================================================
@allergy_bp.route("/allergies/<int:patient_id>/add", methods=["POST"])
def add_allergy(patient_id):

    Patient.query.get_or_404(patient_id)

    data = request.get_json() or {}

    allergy = AllergyRecord(
        patient_id=patient_id,
        allergy_type=data.get("type", ""),
        allergen=data.get("allergen", ""),
        reaction=data.get("reaction", ""),
        severity=data.get("severity", ""),
        notes=data.get("notes", "")
    )

    db.session.add(allergy)
    db.session.commit()

    return jsonify(allergy.to_dict()), 201


# ============================================================
# UPDATE SINGLE ALLERGY
# ============================================================
@allergy_bp.route("/allergies/record/<int:allergy_id>", methods=["PUT"])
def update_allergy(allergy_id):

    allergy = AllergyRecord.query.get_or_404(allergy_id)

    data = request.get_json() or {}

    allergy.allergy_type = data.get("type", allergy.allergy_type)
    allergy.allergen = data.get("allergen", allergy.allergen)
    allergy.reaction = data.get("reaction", allergy.reaction)
    allergy.severity = data.get("severity", allergy.severity)
    allergy.notes = data.get("notes", allergy.notes)

    db.session.commit()

    return jsonify(allergy.to_dict()), 200


# ============================================================
# DELETE SINGLE ALLERGY
# ============================================================
@allergy_bp.route("/allergies/record/<int:allergy_id>", methods=["DELETE"])
def delete_allergy(allergy_id):

    allergy = AllergyRecord.query.get_or_404(allergy_id)

    db.session.delete(allergy)
    db.session.commit()

    return jsonify({
        "message": "Allergy deleted successfully"
    }), 200