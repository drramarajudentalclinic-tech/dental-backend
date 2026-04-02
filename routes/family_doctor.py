from flask import Blueprint, request, jsonify
from database import db
from models import FamilyDoctor

family_doctor_bp = Blueprint("family_doctor", __name__)

@family_doctor_bp.route("/family-doctor/<int:patient_id>", methods=["GET", "PUT", "OPTIONS"])
def save_family_doctor(patient_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json() or {}

    doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()
    if not doc:
        doc = FamilyDoctor(patient_id=patient_id)
        db.session.add(doc)

    doc.doctor_name    = data.get("doctor_name")    or doc.doctor_name
    doc.doctor_phone   = data.get("doctor_phone")   or doc.doctor_phone
    doc.doctor_address = data.get("doctor_address") or doc.doctor_address

    db.session.commit()
    return jsonify({"patient_id": patient_id, "status": "family doctor saved"}), 200