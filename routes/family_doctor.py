from flask import Blueprint, request, jsonify
from database import db
from models import FamilyDoctor, Patient

family_doctor_bp = Blueprint("family_doctor", __name__)


@family_doctor_bp.route("/family-doctor/<int:patient_id>", methods=["GET", "PUT", "OPTIONS"])
def save_family_doctor(patient_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    Patient.query.get_or_404(patient_id)
    doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()

    # ── GET: return the current record ──
    # NOTE: previously there was no method branch — a GET request fell
    # through to the same code as PUT. Because every field used the
    # "data.get(x) or existing_value" pattern, an empty GET body wasn't
    # destructive here (unlike consent.py), but it also never returned
    # the actual saved data — every read got back only
    # {"status": "family doctor saved"}, so any form trying to load
    # existing family-doctor info always rendered blank.
    if request.method == "GET":
        if not doc:
            return jsonify({
                "doctor_name": "", "doctor_phone": "", "doctor_address": "",
            }), 200
        return jsonify({
            "doctor_name":    doc.doctor_name or "",
            "doctor_phone":   doc.doctor_phone or "",
            "doctor_address": doc.doctor_address or "",
        }), 200

    # ── PUT: save ──
    data = request.get_json() or {}

    if not doc:
        doc = FamilyDoctor(patient_id=patient_id)
        db.session.add(doc)

    doc.doctor_name    = data.get("doctor_name")    or doc.doctor_name
    doc.doctor_phone   = data.get("doctor_phone")   or doc.doctor_phone
    doc.doctor_address = data.get("doctor_address") or doc.doctor_address

    db.session.commit()
    return jsonify({"patient_id": patient_id, "status": "family doctor saved"}), 200