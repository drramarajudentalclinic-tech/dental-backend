from flask import Blueprint, request, jsonify
from database import db
from models import (
    Visit,
    VisitAudit,
    Patient,
    MedicalHistory,
    AllergyRecord,
    Habit,
    WomanHistory,
    FamilyDoctor,
    Consent,
    Consultation,
)
from datetime import date, datetime

visits_bp = Blueprint("visits", __name__)


def row_to_dict(obj, exclude=None):
    if not obj:
        return {}
    exclude = set(exclude or [])
    result = {}
    for col in obj.__table__.columns:
        if col.name in exclude:
            continue
        val = getattr(obj, col.name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        result[col.name] = val
    return result


def resolve_age(dob, manual_age):
    if dob:
        today = date.today()
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age
    return manual_age


# ─────────────────────────────────────────────
# CREATE VISIT
# POST /api/visits
# Workflow step 6: "If no active visit exists, create one (CREATED),
# assign doctor and open it. Otherwise open the active visit."
# ─────────────────────────────────────────────
@visits_bp.route("/visits", methods=["POST"])
def create_visit():
    data = request.get_json() or {}

    patient_id = data.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400

    patient = Patient.query.get_or_404(patient_id)

    # Prevent duplicate active visits for the same patient
    existing = Visit.query.filter(
        Visit.patient_id == patient.id,
        Visit.status.in_(["CREATED", "IN_PROGRESS"])
    ).first()

    if existing:
        return jsonify({
            "id":             existing.id,
            "visit_id":       existing.id,
            "already_exists": True,
            "status":         existing.status,
            "message":        "Patient already has an active visit.",
        }), 200

    visit = Visit(
        patient_id=patient.id,
        visit_date=datetime.utcnow(),
        chief_complaint=data.get("chief_complaint") or patient.chief_complaint,
        followup_treatment=data.get("followup_treatment"),
        status="CREATED",
        created_by=data.get("created_by", "Reception"),
        assigned_doctor=data.get("assigned_doctor"),
    )
    db.session.add(visit)
    db.session.commit()

    return jsonify({
        "id":             visit.id,
        "visit_id":       visit.id,
        "already_exists": False,
        "status":         visit.status,
        "message":        "Visit created successfully.",
    }), 201


# ─────────────────────────────────────────────
# GET VISIT + FULL PATIENT SNAPSHOT
# GET /api/visits/<visit_id>
# ─────────────────────────────────────────────
@visits_bp.route("/visits/<int:visit_id>", methods=["GET"])
def get_visit(visit_id):
    try:
        visit = Visit.query.get_or_404(visit_id)
        patient = Patient.query.get_or_404(visit.patient_id)

        medical = MedicalHistory.query.filter_by(patient_id=patient.id).first()
        allergy = AllergyRecord.query.filter_by(patient_id=patient.id).first()
        habits = Habit.query.filter_by(patient_id=patient.id).all()
        women = WomanHistory.query.filter_by(patient_id=patient.id).first()
        family_doc = FamilyDoctor.query.filter_by(patient_id=patient.id).first()
        consent = Consent.query.filter_by(patient_id=patient.id).first()

        chief_complaint = (
            visit.chief_complaint
            if visit.chief_complaint and visit.chief_complaint.strip()
            else (patient.chief_complaint or "")
        )

        status = (visit.status or "open").lower()

        return jsonify({
            "visit": {
                "id": visit.id,
                "status": status,
                "chief_complaint": chief_complaint,
                "followup_treatment": visit.followup_treatment or "",
                "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
                "date": visit.visit_date.strftime("%d-%b-%Y") if visit.visit_date else None,
                "closed_at": visit.closed_at.isoformat() if visit.closed_at else None,
                "closed_by": visit.closed_by or "",
                "billing_note": getattr(visit, "billing_note", "") or "",
                "diagnosis": getattr(visit, "diagnosis", "") or "",
                "treatment_done": getattr(visit, "treatment_done", "") or "",
                "treatment_plan": getattr(visit, "treatment_plan", "") or "",
                "advice": getattr(visit, "advice", "") or "",
            },

            "patient": {
                "id": patient.id,
                "case_number": patient.case_number,
                "name": patient.name,
                "date": patient.date.isoformat() if patient.date else None,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "age": resolve_age(patient.date_of_birth, patient.age),
                "gender": patient.gender,
                "marital_status": patient.marital_status,
                "mobile": patient.mobile,
                "email": patient.email,
                "blood_group": patient.blood_group,
                "address": patient.address,
                "profession": patient.profession,
                "referred_by": patient.referred_by,
                "chief_complaint": patient.chief_complaint,
            },

            "medical": row_to_dict(medical, ["id", "patient_id", "updated_at"]),

            "allergy": allergy.to_dict() if allergy else {
                "drug_allergy": False, "food_allergy": False, "latex_allergy": False,
                "iodine_allergy": False, "anesthesia_allergy": False,
                "other_allergy": "", "no_known_allergies": False,
            },

            "habits": [
                {
                    "id": h.id,
                    "smoking": bool(h.smoking),
                    "smoking_detail": h.smoking or "",

                    "alcohol": bool(h.alcohol),
                    "alcohol_detail": h.alcohol or "",

                    "tobacco": bool(h.tobacco),
                    "tobacco_detail": h.tobacco or "",

                    "pan_chewing": bool(h.pan_chewing),
                    "pan_chewing_detail": h.pan_chewing or "",

                    "spicy_foods": bool(h.spicy_foods),
                    "spicy_foods_detail": h.spicy_foods or "",
                }
                for h in habits
            ],

            "women": {
                "pregnant": women.pregnant if women else False,
                "due_date": women.due_date.isoformat() if women and women.due_date else None,
                "nursing_child": women.nursing_child if women else False,
            },

            "family_doctor": row_to_dict(family_doc, ["id", "patient_id"]),
            "consent": row_to_dict(consent, ["id", "patient_id"]),
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


# ─────────────────────────────────────────────
# NOTE:
# "/patients/<id>/full-history" used to be duplicated here. It was a
# third copy of the same "complete patient history" logic already built
# properly in patients.py, but missing medical/habits/allergy/women/
# medications/family-doctor/consent data, and no frontend file called it.
# Removed in favor of the single, complete implementation:
#
#   GET /api/patients/<patient_id>/complete-history   (patients.py)
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# SET NEXT APPOINTMENT
# PUT /api/visits/<visit_id>/next-appointment
# Workflow step 10: "Reception performs billing, payments, receipts and
# next appointment." Visit.next_appointment already existed as a column
# but nothing read or wrote it — this is that missing piece.
# ─────────────────────────────────────────────
@visits_bp.route("/visits/<int:visit_id>/next-appointment", methods=["PUT"])
def set_next_appointment(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    data = request.get_json(force=True, silent=True) or {}

    raw_date = (data.get("next_appointment") or "").strip()

    if not raw_date:
        visit.next_appointment = None
    else:
        try:
            visit.next_appointment = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "next_appointment must be YYYY-MM-DD"}), 400

    db.session.commit()

    return jsonify({
        "visit_id": visit.id,
        "next_appointment": visit.next_appointment.isoformat() if visit.next_appointment else None,
    }), 200


# ─────────────────────────────────────────────
# CLOSE VISIT
# PUT /api/visits/<visit_id>/close
# Workflow step 9: "Status becomes COMPLETED. Completion time and audit
# are saved."
# ─────────────────────────────────────────────
@visits_bp.route("/visits/<int:visit_id>/close", methods=["PUT"])
def close_visit(visit_id):
    visit = Visit.query.get_or_404(visit_id)

    if (visit.status or "").lower() == "closed":
        return jsonify({"message": "Visit already closed", "visit_id": visit_id}), 200

    # force=True  → parse even without Content-Type: application/json
    # silent=True → return None instead of raising 400 when body is empty
    data = request.get_json(force=True, silent=True) or {}

    old_status = visit.status

    # Mark closed
    # NOTE: kept as lowercase "closed" (not "COMPLETED") because
    # DoctorPatientView.jsx already gates on
    # visit.status.toLowerCase() === "closed", and doctor.py's
    # get_doctor_visits() only ever matches "CREATED"/"IN_PROGRESS" as
    # active — either value correctly falls out of the active list.
    # The COMPLETED milestone itself is captured explicitly below via
    # the VisitAudit entry.
    visit.status    = "closed"
    visit.closed_at = datetime.utcnow()
    visit.closed_by = data.get("doctor_name") or visit.assigned_doctor or "Doctor"

    # Persist doctor's optional billing instructions for reception
    visit.billing_note = (data.get("billing_note") or "").strip()

    # Snapshot latest Consultation fields onto Visit so the billing desk
    # can read them in a single query without joining Consultation.
    c = (Consultation.query
         .filter_by(visit_id=visit_id)
         .order_by(Consultation.created_at.desc())
         .first())
    if c:
        visit.diagnosis      = (c.diagnosis            or "").strip()
        visit.treatment_done = (c.treatment_done_today or "").strip()
        visit.treatment_plan = (c.treatment_plan        or "").strip()
        visit.advice         = (c.advice               or "").strip()

    audit = VisitAudit(
        visit_id=visit.id,
        action="COMPLETE_VISIT",
        old_status=old_status,
        new_status=visit.status,
        performed_by=visit.closed_by,
        reason=data.get("reason"),
    )
    db.session.add(audit)

    db.session.commit()

    return jsonify({
        "message":        "Visit closed successfully",
        "visit_id":       visit_id,
        "status":         visit.status,
        "closed_at":      visit.closed_at.strftime("%d-%b-%Y %H:%M"),
        "closed_by":      visit.closed_by   or "",
        "billing_note":   visit.billing_note   or "",
        "diagnosis":      visit.diagnosis      or "",
        "treatment_done": visit.treatment_done or "",
        "treatment_plan": visit.treatment_plan or "",
        "advice":         visit.advice         or "",
    }), 200