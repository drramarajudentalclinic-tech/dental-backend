from flask import Blueprint, jsonify
from models import (
    Visit,
    Patient,
    MedicalHistory,
    WomanHistory,
    AllergyRecord,
)

doctor_bp = Blueprint("doctor", __name__)


# ─────────────────────────────────────────────
# GET OPEN VISITS
# GET /api/doctor/visits
# ─────────────────────────────────────────────
@doctor_bp.route("/doctor/visits", methods=["GET"])
def get_open_visits():
    visits = (
        Visit.query
        .filter_by(status="OPEN")
        .order_by(Visit.visit_date.desc())
        .all()
    )

    result = []
    for v in visits:
        patient = Patient.query.get(v.patient_id)
        if not patient:
            continue

        result.append({
            "visit_id":            v.id,
            "visit_date":          v.visit_date.isoformat() if v.visit_date else None,
            "patient_id":          patient.id,
            "name":                patient.name,
            "case_number":         patient.case_number,
            "mobile":              patient.mobile or "",
            "chief_complaint":     v.chief_complaint     or "",
            "followup_treatment":  v.followup_treatment  or "",
        })

    return jsonify(result), 200


# ─────────────────────────────────────────────
# OPEN SINGLE VISIT (DOCTOR VIEW)
# GET /api/doctor/visit/<visit_id>
# ─────────────────────────────────────────────
@doctor_bp.route("/doctor/visit/<int:visit_id>", methods=["GET"])
def open_visit(visit_id):
    visit   = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)

    # uselist=False relationships — may be None
    medical = MedicalHistory.query.filter_by(patient_id=patient.id).first()
    woman   = WomanHistory.query.filter_by(patient_id=patient.id).first()

    # one-to-many — return list
    allergies = AllergyRecord.query.filter_by(patient_id=patient.id).all()

    return jsonify({
        "patient": {
            "id":          patient.id,
            "name":        patient.name,
            "case_number": patient.case_number,
            "age":         patient.age,
            "gender":      patient.gender,
            "mobile":      patient.mobile or "",
        },
        # .to_dict() added to MedicalHistory & WomanHistory in models.py
        "medical_history": medical.to_dict() if medical else None,
        "woman_history":   woman.to_dict()   if woman   else None,
        # .to_dict() added to AllergyRecord in models.py
        "allergies":       [a.to_dict() for a in allergies],
        "visit": {
            "id":                  visit.id,
            "date":                visit.visit_date.isoformat() if visit.visit_date else None,
            "chief_complaint":     visit.chief_complaint    or "",
            "followup_treatment":  visit.followup_treatment or "",
            "status":              visit.status,
        },
    }), 200