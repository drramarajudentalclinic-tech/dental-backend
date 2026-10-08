from flask import Blueprint, request, jsonify
from database import db
from models import (
    Visit,
    VisitAudit,
    Patient,
    MedicalHistory,
    AllergyRecord,
    Habit,
    Medication,
    WomanHistory,
    FamilyDoctor,
    Consent,
    Consultation,
)
from datetime import date, datetime, timedelta
from sqlalchemy import func, or_

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

    # `data.get("chief_complaint") or patient.chief_complaint` used to treat an
    # intentionally-empty chief complaint (e.g. a follow-up visit, where
    # `followup_treatment` carries the reason instead) the same as the field
    # being omitted entirely — an empty string is falsy in Python, so `or`
    # silently substituted the patient's original on-file complaint. Checking
    # for the key's presence keeps that fallback only for callers who don't
    # send the field at all, while a deliberate "" (as Reception's follow-up
    # flow sends) stays blank.
    if "chief_complaint" in data:
        chief_complaint = data.get("chief_complaint") or ""
    else:
        chief_complaint = patient.chief_complaint

    visit = Visit(
        patient_id=patient.id,
        visit_date=datetime.utcnow(),
        chief_complaint=chief_complaint,
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
        # AllergyRecord is patient_id-indexed multi-row (one row per
        # allergy), same as the dedicated GET /allergies/<patient_id>
        # route — unlike Habit/MedicalHistory/Women/FamilyDoctor/Consent
        # below, which really are one-row-per-patient. Must use .all()
        # here or every allergy but the first silently disappears.
        allergies = (AllergyRecord.query
                     .filter_by(patient_id=patient.id)
                     .order_by(AllergyRecord.id.asc())
                     .all())
        # Medication is likewise patient_id-indexed multi-row (one row per
        # medication) — same reasoning as allergies above.
        medications = (Medication.query
                       .filter_by(patient_id=patient.id)
                       .order_by(Medication.medicine_name)
                       .all())
        # NOTE: Habit is a one-row-per-patient model (see habits.py, which
        # always does .first()). This used to be .all() + list-wrapped,
        # which mismatched every sibling relation here (medical/allergy/
        # women/family_doc/consent all use .first() + a flat dict) and
        # caused the frontend to receive habits as Array(1) instead of a
        # flat object, breaking DoctorHabitsSummary's rendering.
        habits = Habit.query.filter_by(patient_id=patient.id).first()
        women = WomanHistory.query.filter_by(patient_id=patient.id).first()
        family_doc = FamilyDoctor.query.filter_by(patient_id=patient.id).first()
        consent = Consent.query.filter_by(patient_id=patient.id).first()

        # NOTE: this used to fall back to patient.chief_complaint whenever
        # visit.chief_complaint was blank — but a blank chief_complaint on a
        # visit can be intentional (e.g. a follow-up visit, where
        # followup_treatment is the actual reason for the visit). Falling
        # back here would keep masking that even after create_visit() stores
        # the intentional blank correctly. Show the visit's own value as-is.
        chief_complaint = visit.chief_complaint or ""

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

            "allergy": {
                "rows": [a.to_dict() for a in allergies]
            },

            "medications": [m.to_dict() for m in medications],

            "habits": {
                "smoking": bool(habits.smoking) if habits else False,
                "smoking_detail": (habits.smoking or "") if habits else "",

                "alcohol": bool(habits.alcohol) if habits else False,
                "alcohol_detail": (habits.alcohol or "") if habits else "",

                "tobacco": bool(habits.tobacco) if habits else False,
                "tobacco_detail": (habits.tobacco or "") if habits else "",

                "pan_chewing": bool(habits.pan_chewing) if habits else False,
                "pan_chewing_detail": (habits.pan_chewing or "") if habits else "",

                "spicy_foods": bool(habits.spicy_foods) if habits else False,
                "spicy_foods_detail": (habits.spicy_foods or "") if habits else "",

                "no_habits": bool(habits.no_habits) if habits else False,

                "recorded_date": (habits.recorded_date.isoformat() if habits and habits.recorded_date else None),
            },

            "women": {
                "pregnant": women.pregnant if women else False,
                "due_date": women.due_date.isoformat() if women and women.due_date else None,
                "nursing_child": women.nursing_child if women else False,
                "recorded_date": (women.recorded_date.isoformat() if women and women.recorded_date else None),
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
# UPDATE CHIEF COMPLAINT
# PUT /api/visits/<visit_id>/chief-complaint
# Lets the doctor correct/add the chief complaint on an existing visit.
# Reception sets it at intake (create_visit / patients.py), but a patient
# may clarify or change their complaint once they're actually with the
# doctor — nothing previously wrote to this field after visit creation.
# ─────────────────────────────────────────────
@visits_bp.route("/visits/<int:visit_id>/chief-complaint", methods=["PUT"])
def update_chief_complaint(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    data = request.get_json(force=True, silent=True) or {}

    visit.chief_complaint = (data.get("chief_complaint") or "").strip()
    db.session.commit()

    return jsonify({
        "visit_id": visit.id,
        "chief_complaint": visit.chief_complaint,
    }), 200


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

# ═════════════════════════════════════════════
# CLOSED VISITS FOR RECEPTION  ("Doctor's Instructions")
#
# The clinic bills in its own separate billing software. This system no
# longer has a Billing section; it only hands over what Reception needs:
# which visits the doctor has closed, what was done, and the doctor's
# billing instructions. Reception ticks a visit off once it has been
# billed in the billing software.
#
# These two addresses are also the connection point for that billing
# software: it can read the same list and mark a visit as done.
#
#   GET /api/visits/closed
#         ?status=pending | done | all      (default: pending)
#         &date_from=YYYY-MM-DD  &date_to=YYYY-MM-DD   (day the visit was closed, Indian time)
#         &q=<name, case number or mobile>
#         &visit_id=<one particular visit>   (the billing software uses this
#                                             when it opens a receipt for a visit)
#         &limit=<max rows, default 300>
#
#   PUT /api/visits/<visit_id>/billing-done      { "done": true | false }
#
# "Done" is kept in the existing visits.billing_closed column.
# ═════════════════════════════════════════════
_IST = timedelta(hours=5, minutes=30)


def _to_ist(dt):
    return dt + _IST if dt else None


def _parse_day(value):
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d") if value else None
    except ValueError:
        return None


def _handover_item(visit, patient):
    closed_ist = _to_ist(visit.closed_at)
    done_ist   = _to_ist(getattr(visit, "billing_closed_at", None))
    return {
        "visit_id":        visit.id,
        "patient_id":      visit.patient_id,
        "name":            (patient.name if patient else "") or "",
        "case_number":     (patient.case_number if patient else "") or "",
        "mobile":          (patient.mobile if patient else "") or "",
        "age":             resolve_age(getattr(patient, "date_of_birth", None), getattr(patient, "age", None)) if patient else None,
        "gender":          (getattr(patient, "gender", "") if patient else "") or "",
        "visit_date":      _to_ist(visit.visit_date).strftime("%Y-%m-%d") if visit.visit_date else None,
        "closed_at":       closed_ist.strftime("%Y-%m-%dT%H:%M:%S") if closed_ist else None,
        "closed_date":     closed_ist.strftime("%Y-%m-%d") if closed_ist else None,
        "closed_display":  closed_ist.strftime("%d-%m-%Y %I:%M %p") if closed_ist else "",
        "closed_by":       visit.closed_by or "",
        "billing_note":    (visit.billing_note or "").strip(),
        "diagnosis":       (visit.diagnosis or "").strip(),
        "treatment_done":  (visit.treatment_done or "").strip(),
        "treatment_plan":  (visit.treatment_plan or "").strip(),
        "advice":          (visit.advice or "").strip(),
        "next_appointment": visit.next_appointment.isoformat() if visit.next_appointment else None,
        "done":            bool(getattr(visit, "billing_closed", False)),
        "done_at":         done_ist.strftime("%Y-%m-%dT%H:%M:%S") if done_ist else None,
        "done_display":    done_ist.strftime("%d-%m-%Y %I:%M %p") if done_ist else "",
    }


def _is_closed(visit):
    return (visit.status or "").strip().lower() in ("closed", "completed")


@visits_bp.route("/visits/closed", methods=["GET"])
def list_closed_visits():
    status = (request.args.get("status") or "pending").strip().lower()
    if status not in ("pending", "done", "all"):
        status = "pending"

    query = (db.session.query(Visit, Patient)
             .outerjoin(Patient, Patient.id == Visit.patient_id)
             .filter(func.lower(Visit.status).in_(["closed", "completed"])))

    if status == "pending":
        query = query.filter(or_(Visit.billing_closed.is_(None), Visit.billing_closed.is_(False)))
    elif status == "done":
        query = query.filter(Visit.billing_closed.is_(True))

    # Dates are the day the visit was closed in Indian time; closed_at is stored in UTC.
    day_from = _parse_day(request.args.get("date_from"))
    day_to   = _parse_day(request.args.get("date_to"))
    if day_from:
        query = query.filter(Visit.closed_at >= day_from - _IST)
    if day_to:
        query = query.filter(Visit.closed_at < day_to + timedelta(days=1) - _IST)

    # One particular visit — asked for by the billing software when Reception
    # opens a receipt for it.
    only_id = request.args.get("visit_id", type=int)
    if only_id:
        query = query.filter(Visit.id == only_id)

    q = (request.args.get("q") or "").strip()
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(
            func.lower(func.coalesce(Patient.name, "")).like(like),
            func.lower(func.coalesce(Patient.case_number, "")).like(like),
            func.coalesce(Patient.mobile, "").like(f"%{q}%"),
        ))

    try:
        limit = max(1, min(int(request.args.get("limit", 300)), 1000))
    except (TypeError, ValueError):
        limit = 300

    rows = (query.order_by(Visit.closed_at.desc().nullslast(), Visit.id.desc())
            .limit(limit).all())
    return jsonify([_handover_item(v, p) for v, p in rows]), 200


@visits_bp.route("/visits/<int:visit_id>/billing-done", methods=["PUT"])
def set_billing_done(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    if not _is_closed(visit):
        return jsonify({"error": "This visit is still open. It can be marked only after the doctor closes it."}), 400

    data = request.get_json(force=True, silent=True) or {}
    raw = data.get("done", True) if isinstance(data, dict) else True
    done = str(raw).strip().lower() not in ("false", "0", "no", "") if not isinstance(raw, bool) else raw

    try:
        visit.billing_closed    = done
        visit.billing_closed_at = datetime.utcnow() if done else None
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "The server could not save this. Nothing was changed - please try again."}), 500

    patient = db.session.get(Patient, visit.patient_id)
    return jsonify(_handover_item(visit, patient)), 200

# ═════════════════════════════════════════════
# BILLING (receipts)
#
# The clinic's billing — the old stand-alone billing software rebuilt
# inside this system — lives in billing_receipts.py, in this same routes
# folder. Its addresses (/clinic-billing/receipts, /clinic-billing/excel, …) are added
# to this file's group of addresses here, so app.py does not need to be
# changed. If billing_receipts.py is not in the folder, everything else
# in this file works exactly as before and the Billing screen says the
# file is missing.
# ═════════════════════════════════════════════
def _load_billing():
    try:
        from routes.billing_receipts import register_billing_routes
        return register_billing_routes
    except ImportError as first:
        if first.name not in ("routes", "routes.billing_receipts"):
            raise          # billing_receipts.py is there but something it needs is missing
    try:
        from billing_receipts import register_billing_routes
        return register_billing_routes
    except ImportError as second:
        if second.name != "billing_receipts":
            raise
    return None


_register_billing = _load_billing()
if _register_billing is not None:
    _register_billing(visits_bp)
else:
    print("[visits] billing_receipts.py was not found in the routes folder - the Billing screen is switched off")