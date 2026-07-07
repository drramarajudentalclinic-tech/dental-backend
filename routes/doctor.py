from flask import Blueprint, jsonify, request
from database import db
from datetime import datetime

from models import (
    Visit,
    VisitAudit,
    Patient,
    MedicalHistory,
    WomanHistory,
    AllergyRecord,
    Habit,
    FamilyDoctor,
    Consent,
    Consultation,
    Prescription,
    Image,
    CBCTFile,
    CBCTVolume,
    DentalChart,
    OtherFinding,
    Payment,
)

doctor_bp = Blueprint("doctor", __name__)


# ─────────────────────────────────────────────
# GET OPEN VISITS
# GET /api/doctor/visits
# ─────────────────────────────────────────────
@doctor_bp.route("/doctor/visits", methods=["GET"])
def get_doctor_visits():

    visits = (
        Visit.query.filter(
            Visit.status.in_(["CREATED", "IN_PROGRESS"])
        )
        .order_by(Visit.visit_date.desc())
        .all()
    )

    result = []

    for visit in visits:

        patient = Patient.query.get(visit.patient_id)

        if not patient:
            continue

        # Workflow safeguard: let the dashboard warn if a doctor tries to
        # complete a visit with no diagnosis/treatment/consultation
        # recorded yet.
        has_consultation = (
            Consultation.query.filter_by(visit_id=visit.id).first() is not None
        )
        has_clinical_notes = bool(
            has_consultation
            or (visit.diagnosis or "").strip()
            or (visit.treatment_done or "").strip()
        )

        result.append({

            "visit_id": visit.id,

            "patient_id": patient.id,

            "case_number": patient.case_number,

            "patient_name": patient.name,

            "mobile": patient.mobile,

            "age": patient.age,

            "gender": patient.gender,

            "chief_complaint": visit.chief_complaint,

            "status": visit.status,

            "assigned_doctor": visit.assigned_doctor,

            "created_by": visit.created_by,

            "has_clinical_notes": has_clinical_notes,

            "visit_date": (
                visit.visit_date.isoformat()
                if visit.visit_date
                else None
            )

        })

    return jsonify(result), 200

# ══════════════════════════════════════════════
# START / CONTINUE VISIT
# POST /api/doctor/visit/<visit_id>/start
# ══════════════════════════════════════════════

@doctor_bp.route("/doctor/visit/<int:visit_id>/start", methods=["POST"])
def start_visit(visit_id):

    visit = Visit.query.get_or_404(visit_id)

    data = request.get_json() or {}

    # Already started
    if (visit.status or "").upper() == "IN_PROGRESS":
        return jsonify({
            "message": "Visit already in progress.",
            "visit_id": visit.id
        }), 200

    # Closed visits cannot be started
    # NOTE: close_visit() (visits.py) stores the status as lowercase
    # "closed" — compare case-insensitively so this guard actually works.
    if (visit.status or "").lower() == "closed":
        return jsonify({
            "error": "Visit already closed."
        }), 400

    old_status = visit.status

    visit.status = "IN_PROGRESS"

    visit.assigned_doctor = (
        data.get("doctor_name")
        or visit.assigned_doctor
    )

    # ── Workflow step 7: "Status changes to IN_PROGRESS and an
    #    audit entry is created." ──
    audit = VisitAudit(
        visit_id=visit.id,
        action="START_VISIT",
        old_status=old_status,
        new_status=visit.status,
        performed_by=data.get("doctor_name") or visit.assigned_doctor or "Doctor",
        reason=data.get("reason"),
    )
    db.session.add(audit)

    db.session.commit()

    return jsonify({
        "message": "Visit started successfully.",
        "visit_id": visit.id
    }), 200
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
    allergy = AllergyRecord.query.filter_by(patient_id=patient.id).first()

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
        "allergies":       allergy.to_dict() if allergy else {
            "drug_allergy": False, "food_allergy": False, "latex_allergy": False,
            "iodine_allergy": False, "anesthesia_allergy": False,
            "other_allergy": "", "no_known_allergies": False,
        },
        "visit": {
            "id":                  visit.id,
            "date":                visit.visit_date.isoformat() if visit.visit_date else None,
            "chief_complaint":     visit.chief_complaint    or "",
            "followup_treatment":  visit.followup_treatment or "",
            "status":              visit.status,
        },
    }), 200
# ─────────────────────────────────────────────
# NOTE:
# "/patients/search" and "/patients/<id>/history" used to be duplicated
# here. They collided with the routes of the same URL already defined in
# patients.py (patients_bp: GET /api/patients/search) and were incomplete
# (missing medical/habits/allergy/women/medication/family-doctor/consent
# and dental-chart/findings data required for the "View Complete Patient
# History" screen). Both Doctor and Reception now call the single,
# fully-implemented endpoint instead:
#
#   GET /api/patients/search                          (patients.py)
#   GET /api/patients/<patient_id>/complete-history    (patients.py)
#
# Keeping one implementation avoids the two blueprints fighting over the
# same URL and keeps Doctor + Reception showing identical data.
# ─────────────────────────────────────────────