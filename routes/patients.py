from flask import Blueprint, request, jsonify
from database import db
from flask import request, jsonify
from models import Patient, Visit
from models import (
    Patient,
    MedicalHistory,
    AllergyRecord,
    Habit,
     Medication,
    WomanHistory,
    FamilyDoctor,
    Consent,
    Visit,
    Consultation,
    Prescription,
    DentalChart,
    OtherFinding,
    Image,
    Payment,
    CBCTVolume,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
from datetime import datetime, date
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth_utils import require_role, require_login, get_current_role
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

patients_bp = Blueprint(
    "patients",
    __name__,
    url_prefix="/api/patients"
)


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def resolve_age(dob, manual_age):
    if dob:
        today = date.today()
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age
    return manual_age


def parse_date(value):
    if not value or not str(value).strip():
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_int(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


def to_bool(val):
    """Convert YES/NO/1/0/True/False → Python bool."""
    if isinstance(val, bool): return val
    if isinstance(val, int):  return bool(val)
    if isinstance(val, str):  return val.strip().upper() in ("YES", "TRUE", "1")
    return False


def get_chief_complaint(data):
    for key in [
        "chief_complaint", "Chief_Complaint", "chiefComplaint",
        "main_complaint", "mainComplaint", "complaint",
        "reason_for_visit", "reason", "presenting_complaint",
    ]:
        val = data.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return None


def model_to_dict(obj, exclude=None):
    if not obj:
        return {}
    exclude = exclude or []
    result = {}
    for column in obj.__table__.columns:
        if column.name in exclude:
            continue
        val = getattr(obj, column.name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        result[column.name] = val
    return result

# ==========================================
# Medication Dropdown Constants
# ==========================================

VALID_FREQUENCIES = [
    "OD",
    "BD",
    "TDS",
    "QID",
    "HS",
    "SOS",
    "STAT",
    "Weekly",
    "Monthly",
    "Custom"
]

VALID_DURATIONS = [
    "3 Days",
    "5 Days",
    "7 Days",
    "10 Days",
    "14 Days",
    "21 Days",
    "1 Month",
    "2 Months",
    "3 Months",
    "6 Months",
    "Ongoing",
    "Custom"
]

VALID_PURPOSES = [
    "Diabetes",
    "Hypertension",
    "Cardiac",
    "Thyroid",
    "Asthma",
    "Pain Relief",
    "Antibiotic",
    "Vitamin Supplement",
    "Gastric Protection",
    "Blood Thinner",
    "Other"
]

def serialize_patient(p):
    return {
        "id":              p.id,
        "case_number":     p.case_number,
        "name":            p.name,
        "date":            p.date.isoformat() if p.date else None,
        "age":             resolve_age(p.date_of_birth, p.age),
        "date_of_birth":   p.date_of_birth.isoformat() if p.date_of_birth else None,
        "gender":          p.gender,
        "marital_status":  p.marital_status,
        "mobile":          p.mobile,
        "email":           p.email,
        "blood_group":     p.blood_group,
        "address":         p.address,
        "profession":      p.profession,
        "referred_by":     p.referred_by,
        "chief_complaint": p.chief_complaint,
    }


# ══════════════════════════════════════════════
#  CREATE + SEARCH PATIENT
#  POST /api/patients
#  GET  /api/patients?search=...
# ══════════════════════════════════════════════
@patients_bp.route("", methods=["GET", "POST"])
@require_login
def patients():

    # ── CREATE ──────────────────────────────────────────────────
    # Registering a new patient is a Reception (front-desk) workflow —
    # Doctor can view/search patients via this same route (GET below)
    # but should not be creating patient records.
    if request.method == "POST":
        role = get_current_role()
        print("🔍 DEBUG role received:", repr(role))
        print("🔍 DEBUG full claims:", get_jwt())
        if role not in ("reception", "admin"):
            return jsonify({
                "error": "Forbidden",
                "detail": "Only Reception can register new patients."
            }), 403

        data = request.json or {}

        print("📥 Patient POST keys:", list(data.keys()))

        # ── Mandatory field validation ───────────────────────────
        missing = []
        if not data.get("name",        "").strip(): missing.append("Full Name")
        if not data.get("case_number", "").strip(): missing.append("Case Number")
        if not data.get("gender",      "").strip(): missing.append("Gender")
        if not data.get("mobile",      "").strip(): missing.append("Mobile Number")

        parsed_dob = parse_date(data.get("dob") or data.get("date_of_birth"))
        age_val    = parse_int(data.get("age"))
        if parsed_dob:
            age_val = resolve_age(parsed_dob, age_val)
        if age_val is None:
            missing.append("Age")

        if missing:
            return jsonify({
                "error":  "Missing required fields",
                "fields": missing
            }), 400
        # ────────────────────────────────────────────────────────

        parsed_date     = parse_date(data.get("date"))
        chief_complaint = get_chief_complaint(data)

        patient = Patient(
            case_number    = data.get("case_number").strip(),
            name           = data.get("name").strip(),
            date           = parsed_date,
            age            = age_val,
            date_of_birth  = parsed_dob,
            gender         = data.get("gender").strip(),
            marital_status = data.get("marital_status"),
            mobile         = data.get("mobile").strip(),
            email          = data.get("email"),
            blood_group    = data.get("blood_group"),
            address        = data.get("address"),
            profession     = data.get("profession"),
            referred_by    = data.get("referred_by"),
            chief_complaint= chief_complaint,
        )

        try:
            db.session.add(patient)
            db.session.flush() 

            visit = Visit(
    patient_id=patient.id,
    visit_date=datetime.utcnow(),
    chief_complaint=chief_complaint,
    status="CREATED",
    created_by="Reception",
    assigned_doctor=data.get("assigned_doctor"),
)
            db.session.add(visit)
            db.session.commit()

        except IntegrityError as e:
            db.session.rollback()
            print("❌ IntegrityError:", str(e))
            return jsonify({"error": "Case number already exists"}), 409

        except Exception as e:
            db.session.rollback()
            print("❌ Unexpected error on patient save:", str(e))
            return jsonify({
                "error": "Internal server error",
                "detail": str(e)
            }), 500
        return jsonify({
            "patient_id": patient.id,
            "visit_id": visit.id,
        }), 201

    # GET /api/patients
    search = request.args.get("search", "").strip()
    query = Patient.query

    if search:
        query = query.filter(
            or_(
                Patient.name.ilike(f"%{search}%"),
                Patient.case_number.ilike(f"%{search}%"),
                Patient.mobile.ilike(f"%{search}%")
            )
        )

    return jsonify([serialize_patient(p) for p in query.all()]), 200


# ══════════════════════════════════════════════
# ══════════════════════════════════════════════
#  SEARCH ALL PATIENTS
#  GET /api/patients/search?q=...
# ══════════════════════════════════════════════


# ══════════════════════════════════════════════
#  GET FULL PATIENT
#  GET /api/patients/<patient_id>
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>", methods=["GET"])
@require_login
def get_patient(patient_id):
    patient    = Patient.query.get_or_404(patient_id)
    medical    = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    # AllergyRecord is patient_id-indexed multi-row (one row per allergy) —
    # must use .all(), not .first(), or every allergy but one disappears.
    allergies  = (AllergyRecord.query
                  .filter_by(patient_id=patient_id)
                  .order_by(AllergyRecord.id.asc())
                  .all())
    habit      = Habit.query.filter_by(patient_id=patient_id).first()
    medications = Medication.query.filter_by(
    patient_id=patient_id
).all()
    family_doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()
    consent    = Consent.query.filter_by(patient_id=patient_id).first()
    visit_history = []

    for v in sorted(patient.visits, key=lambda x: x.visit_date or datetime.min, reverse=True):
        visit_history.append({
            "visit_id": v.id,
            "visit_date": v.visit_date.isoformat() if v.visit_date else None,
            "status": v.status,
            "chief_complaint": v.chief_complaint,
            "diagnosis": v.diagnosis,
            "treatment_plan": v.treatment_plan,
            "treatment_done": v.treatment_done,
            "advice": v.advice,
            "billing_note": v.billing_note,
            "followup_treatment": v.followup_treatment,
        })
    women = None
    if patient.gender == "Female":
        women = WomanHistory.query.filter_by(patient_id=patient_id).first()

    return jsonify({
        "patient":       serialize_patient(patient),
        "medical":       medical.to_dict() if medical else {},
        "allergy":       {"rows": [a.to_dict() for a in allergies]},
        "habits": {
    "smoking": bool(habit.smoking) if habit else False,
    "smoking_detail": habit.smoking or "" if habit else "",

    "alcohol": bool(habit.alcohol) if habit else False,
    "alcohol_detail": habit.alcohol or "" if habit else "",

    "tobacco": bool(habit.tobacco) if habit else False,
    "tobacco_detail": habit.tobacco or "" if habit else "",

    "pan_chewing": bool(habit.pan_chewing) if habit else False,
    "pan_chewing_detail": habit.pan_chewing or "" if habit else "",

    "spicy_foods": bool(habit.spicy_foods) if habit else False,
    "spicy_foods_detail": habit.spicy_foods or "" if habit else "",

    "no_habits": bool(habit.no_habits) if habit else False,
},
         "medications": [
        m.to_dict()
        for m in medications
    ],
        "women":         women.to_dict() if women else {},
        "visit_history": visit_history,
        "family_doctor": model_to_dict(family_doc, ["id", "patient_id"]),
        "consent":       model_to_dict(consent,    ["id", "patient_id"]),
    }), 200

##########################################################################
# COMPLETE PATIENT HISTORY  (read-only, used by Doctor + Reception)
# GET /api/patients/<patient_id>/complete-history
##########################################################################

@patients_bp.route("/<int:patient_id>/complete-history", methods=["GET"])
@require_login
def complete_history(patient_id):

    patient = Patient.query.get_or_404(patient_id)

    # ── Demographics-adjacent single records ──
    medical     = MedicalHistory.query.filter_by(patient_id=patient.id).first()
    women       = WomanHistory.query.filter_by(patient_id=patient.id).first()
    family_doc  = FamilyDoctor.query.filter_by(patient_id=patient.id).first()
    consent     = Consent.query.filter_by(patient_id=patient.id).first()

    # ── One-to-many records ──
    allergies   = (AllergyRecord.query
                   .filter_by(patient_id=patient.id)
                   .order_by(AllergyRecord.id.asc())
                   .all())
    habits      = Habit.query.filter_by(patient_id=patient.id).all()
    medications = Medication.query.filter_by(patient_id=patient.id, active=True).all()

    # ── All visits, newest first ──
    visits = (
        Visit.query
        .filter_by(patient_id=patient.id)
        .order_by(Visit.visit_date.desc())
        .all()
    )

    active_visit = next(
        (v for v in visits if v.status in ["CREATED", "IN_PROGRESS"]),
        None
    )

    visit_history = []

    for visit in visits:

        consultations = Consultation.query.filter_by(visit_id=visit.id).all()
        prescriptions = Prescription.query.filter_by(visit_id=visit.id).all()
        images        = Image.query.filter_by(visit_id=visit.id).all()
        dental_chart  = DentalChart.query.filter_by(visit_id=visit.id).all()
        findings      = OtherFinding.query.filter_by(visit_id=visit.id).all()
        payments      = Payment.query.filter_by(visit_id=visit.id).all()
        cbct_volumes  = CBCTVolume.query.filter_by(visit_id=visit.id).order_by(CBCTVolume.uploaded_at.desc()).all()

        visit_history.append({
            "visit_id":       visit.id,
            "visit_date":     visit.visit_date.isoformat() if visit.visit_date else None,
            "status":         visit.status,
            "chief_complaint": visit.chief_complaint,
            "diagnosis":       visit.diagnosis,
            "treatment_plan":  visit.treatment_plan,
            "treatment_done":  visit.treatment_done,
            "advice":          visit.advice,
            "assigned_doctor": visit.assigned_doctor,
            "billing_note":    visit.billing_note,
            "next_appointment": visit.next_appointment.isoformat() if visit.next_appointment else None,

            "dental_chart": [d.to_dict() for d in dental_chart],

            "other_findings": [
                {
                    "id":           f.id,
                    "finding_type": f.finding_type,
                    "value":        f.value,
                    "notes":        f.notes,
                    "doctor":       f.doctor,
                    "created_at":   f.created_at.isoformat() if f.created_at else None,
                }
                for f in findings
            ],

            "consultations": [
                {
                    "id":                   c.id,
                    "diagnosis":            c.diagnosis,
                    "advice":               c.advice,
                    "treatment_plan":       c.treatment_plan,
                    "treatment_done_today": c.treatment_done_today,
                    "follow_up_date":       c.follow_up_date.isoformat() if c.follow_up_date else None,
                    "follow_up_time":       c.follow_up_time,
                    "doctor":               c.doctor,
                }
                for c in consultations
            ],

            "prescriptions": [p.to_dict() for p in prescriptions],

            # NOTE: images are stored as base64 in Image.image_data and
            # served via GET /api/images/<id>/data (see images.py) —
            # image_path is just the original filename, not a loadable
            # URL. Building the real url/mime_type here so the frontend
            # can actually render these instead of a broken <img src>.
            "images": [
                {
                    "id":          i.id,
                    "url":         f"/api/images/{i.id}/data",
                    "mime_type":   getattr(i, "mime_type", None) or "image/jpeg",
                    "image_type":  i.image_type,
                    "description": i.description,
                    "image_date":  i.image_date.isoformat() if i.image_date else None,
                }
                for i in images
            ],

            # Summary only — full slice_data (all axial/coronal/sagittal
            # base64 images) stays out of this response on purpose; it can
            # be very large. The dedicated CBCT viewer
            # (GET /api/cbct/<id>/slices) loads that separately.
            "cbct_scans": [
                {
                    "id":              v.id,
                    "study_date":      v.study_date or "",
                    "modality":        v.modality or "CT",
                    "institution":     v.institution or "",
                    "num_slices":      v.num_slices,
                    "uploaded_by":     v.uploaded_by or "",
                    "uploaded_at":     v.uploaded_at.strftime("%d-%b-%Y %H:%M") if v.uploaded_at else None,
                    "notes":           v.notes or "",
                }
                for v in cbct_volumes
            ],

            "payments": [
                {
                    "id":             p.id,
                    "fee":            p.fee,
                    "discount":       p.discount,
                    "paid_amount":    p.paid_amount,
                    "balance":        p.balance,
                    "payment_method": p.payment_method,
                    "receipt_number": p.receipt_number,
                }
                for p in payments
            ],
        })

    return jsonify({
        "patient": serialize_patient(patient),

        "medical_history": medical.to_dict() if medical else None,
        "woman_history":   women.to_dict()   if women   else None,

        "allergies": {"rows": [a.to_dict() for a in allergies]},
        "habits":    [model_to_dict(h, ["patient_id"]) for h in habits],

        "medications": [m.to_dict() for m in medications],

        "family_doctor": model_to_dict(family_doc, ["id", "patient_id"]),
        "consent":       model_to_dict(consent,    ["id", "patient_id"]),

        "has_active_visit": active_visit is not None,
        "active_visit_id":  active_visit.id if active_visit else None,

        "visits": visit_history,
    }), 200
# ══════════════════════════════════════════════
#  UPDATE PATIENT
#  PUT /api/patients/<patient_id>
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>", methods=["PUT"])
@require_role("reception")
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    data    = request.json or {}

    # Re-validate mandatory fields if they are being updated
    if "name" in data and not data["name"].strip():
        return jsonify({"error": "Full Name is required"}), 400
    if "case_number" in data and not data["case_number"].strip():
        return jsonify({"error": "Case Number is required"}), 400
    if "gender" in data and not data["gender"].strip():
        return jsonify({"error": "Gender is required"}), 400
    if "mobile" in data and not data["mobile"].strip():
        return jsonify({"error": "Mobile Number is required"}), 400

    if "dob" in data or "date_of_birth" in data:
        patient.date_of_birth = parse_date(data.get("dob") or data.get("date_of_birth"))
        if patient.date_of_birth:
            patient.age = resolve_age(patient.date_of_birth, patient.age)

    if "date" in data:
        patient.date = parse_date(data["date"])

    if "age" in data:
        new_age = parse_int(data["age"])
        if new_age is not None and not patient.date_of_birth:
            patient.age = new_age
        elif new_age is None and not patient.date_of_birth:
            return jsonify({"error": "Age is required"}), 400

    new_complaint = get_chief_complaint(data)

    for field in [
        "case_number", "name", "gender", "marital_status",
        "mobile", "email", "blood_group", "address",
        "profession", "referred_by", "chief_complaint",
    ]:
        if field in data:
            setattr(patient, field, data[field])

    if new_complaint and not data.get("chief_complaint"):
        patient.chief_complaint = new_complaint

    if new_complaint or data.get("chief_complaint"):
        complaint_val = data.get("chief_complaint") or new_complaint
        open_visit = Visit.query.filter(
        Visit.patient_id == patient_id,
        Visit.status.in_(["CREATED", "IN_PROGRESS"])
    ).first()
        if open_visit and not open_visit.chief_complaint:
            open_visit.chief_complaint = complaint_val

    patient.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "updated"}), 200

# # ══════════════════════════════════════════════
# CREATE NEW VISIT (Existing Patient)
# POST /api/patients/<patient_id>/create-visit
# ══════════════════════════════════════════════

@patients_bp.route("/<int:patient_id>/create-visit", methods=["POST"])
@require_login
def create_visit(patient_id):

    patient = Patient.query.get_or_404(patient_id)

    # Prevent duplicate active visits
    existing = Visit.query.filter(
        Visit.patient_id == patient.id,
        Visit.status.in_(["CREATED", "IN_PROGRESS"])
    ).first()

    if existing:
        return jsonify({
            "success": True,
            "already_exists": True,
            "message": "Patient already has an active visit.",
            "visit_id": existing.id,
            "status": existing.status
        }), 200

    data = request.get_json() or {}

    visit = Visit(
        patient_id=patient.id,
        visit_date=datetime.utcnow(),
        chief_complaint=patient.chief_complaint,
        status="CREATED",
        created_by=data.get("created_by", "Reception"),

        # Doctor can be assigned by Reception.
        # If not assigned, Doctor Dashboard will assign automatically
        assigned_doctor=data.get("assigned_doctor")
    )

    db.session.add(visit)
    db.session.commit()

    return jsonify({
        "success": True,
        "already_exists": False,
        "message": "Visit created successfully.",
        "visit_id": visit.id,
        "patient_id": patient.id,
        "status": visit.status
    }), 201
# ══════════════════════════════════════════════
#  SAVE MEDICAL HISTORY
#  POST/PUT /api/patients/<patient_id>/medical
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/medical", methods=["POST", "PUT"])
@require_login
def save_medical(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    # ── Mandatory: must have at least one condition, other text,
    #    OR explicitly set no_known_conditions = true ────────────
    CONDITION_FIELDS = [
        "aids", "asthma", "arthritis_rheumatism", "blood_disease",
        "bp_high", "bp_low", "corticosteroid_treatment", "cancer",
        "diabetes", "epilepsy", "heart_problems", "hepatitis", "herpes",
        "jaundice", "liver_disease", "kidney_disease", "psychiatric_treatment",
        "radiation_treatment", "respiratory_disease", "rheumatic_fever", "tb",
        "thyroid_problems", "ulcer", "venereal_disease",
    ]

    # Map frontend keys (YES/NO strings or booleans)
    has_condition = any(to_bool(data.get(f)) for f in CONDITION_FIELDS)
    has_other     = bool((data.get("other") or data.get("Other") or "").strip())
    no_known      = to_bool(data.get("no_known_conditions") or data.get("No_Known_Conditions"))

    if not has_condition and not has_other and not no_known:
        return jsonify({
            "error": "Medical history acknowledgement required. "
                     "Select at least one condition or confirm no known conditions."
        }), 400

    medical = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    if not medical:
        medical = MedicalHistory(patient_id=patient_id)
        db.session.add(medical)

    # Field aliases from frontend (PascalCase → snake_case)
    ALIASES = {
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
        "No_Known_Conditions":      "no_known_conditions",
        # Old aliases
        "aids_hiv":               "aids",
        "cardiac_problem":        "heart_problems",
        "hypertension":           "bp_high",
        "other_conditions":       "other",
        "corticosteroid_therapy": "corticosteroid_treatment",
        "radiation_therapy":      "radiation_treatment",
        "tuberculosis":           "tb",
    }

    valid_cols = {col.name for col in MedicalHistory.__table__.columns} - {"id", "patient_id"}

    for raw_key, val in data.items():
        db_key = ALIASES.get(raw_key, raw_key)
        if db_key not in valid_cols:
            continue
        if db_key in ("other",):
            setattr(medical, db_key, str(val) if val else None)
        elif db_key == "no_known_conditions":
            setattr(medical, db_key, to_bool(val))
        else:
            setattr(medical, db_key, to_bool(val))

    # If no_known_conditions confirmed → clear all condition booleans
    if no_known:
        for f in CONDITION_FIELDS:
            setattr(medical, f, False)
        medical.other = None
        medical.no_known_conditions = True

    db.session.commit()
    return jsonify({"status": "medical history saved"}), 200


# ─────────────────────────────────────────────
# NOTE: allergies are now saved/read exclusively via allergies.py's
#   GET/POST/PUT /api/allergies/<patient_id>
# Same schema, same acknowledgment validation as this route used to have —
# consolidated here to match the same standalone-blueprint pattern already
# used for habits.py and women.py, avoiding two blueprints independently
# writing to the same AllergyRecord row.
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# NOTE: habits are now saved/read exclusively via habits.py's
#   GET/POST/PUT /api/habits/<patient_id>
# which has the identical mandatory-acknowledgment validation and field
# mapping as this route used to, plus a GET endpoint this one never had.
# Removed to avoid two blueprints independently writing to the same
# Habit row.
# ─────────────────────────────────────────────

@patients_bp.route("/<int:patient_id>/medications", methods=["GET"])
@require_login
def get_medications(patient_id):

    Patient.query.get_or_404(patient_id)

    medications = Medication.query.filter_by(
        patient_id=patient_id
    ).order_by(
        Medication.medicine_name
    ).all()

    return jsonify([
        m.to_dict()
        for m in medications
    ])
    
# ══════════════════════════════════════════════
# ADD MEDICATION
# POST /api/patients/<patient_id>/medications
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/medications", methods=["POST"])
@require_role("doctor", "reception")
def add_medication(patient_id):

    # Ensure patient exists
    Patient.query.get_or_404(patient_id)

    data = request.get_json() or {}

    # -----------------------------
    # Mandatory Validation
    # -----------------------------
    if not data.get("medicine_name", "").strip():
        return jsonify({
            "error": "Medicine Name is required."
        }), 400

    if not data.get("frequency"):
        return jsonify({
            "error": "Frequency is required."
        }), 400

    if not data.get("duration"):
        return jsonify({
            "error": "Duration is required."
        }), 400

    if not data.get("purpose"):
        return jsonify({
            "error": "Purpose is required."
        }), 400
# -----------------------------
# Dropdown Validation
# -----------------------------
    if data.get("frequency") not in VALID_FREQUENCIES:
        return jsonify({
            "error": "Invalid frequency"
        }), 400

    if data.get("duration") not in VALID_DURATIONS:
        return jsonify({
            "error": "Invalid duration"
        }), 400

    if data.get("purpose") not in VALID_PURPOSES:
        return jsonify({
            "error": "Invalid purpose"
        }), 400
    # -----------------------------
    # Prevent Duplicate Medication
    # -----------------------------
    existing = Medication.query.filter(
        Medication.patient_id == patient_id,
        func.lower(Medication.medicine_name) ==
        data.get("medicine_name", "").strip().lower(),
        Medication.active == True
    ).first()

    if existing:
        return jsonify({
            "error": "This medication is already active for the patient."
        }), 409

    # -----------------------------
    # Create Medication
    # -----------------------------
    medication = Medication(
        patient_id=patient_id,
        medicine_name=data.get("medicine_name").strip(),
        dosage=data.get("dosage"),
        frequency=data.get("frequency"),
        duration=data.get("duration"),
        purpose=data.get("purpose"),
        prescribed_by=data.get("prescribed_by"),
        notes=data.get("notes"),
        active=bool(data.get("active", True))
    )

    db.session.add(medication)
    db.session.commit()

    return jsonify({
        "status": "Medication added successfully",
        "medication_id": medication.id
    }), 201
    
@patients_bp.route("/<int:patient_id>/medications/<int:medication_id>", methods=["PUT"])
@require_role("doctor", "reception")
def update_medication(patient_id, medication_id):

    medication = Medication.query.filter_by(
        patient_id=patient_id,
        id=medication_id
    ).first_or_404()

    data = request.json or {}

    medication.medicine_name = data.get(
        "medicine_name",
        medication.medicine_name
    )

    medication.dosage = data.get(
        "dosage",
        medication.dosage
    )

    medication.frequency = data.get(
        "frequency",
        medication.frequency
    )

    medication.duration = data.get(
        "duration",
        medication.duration
    )

    medication.purpose = data.get(
        "purpose",
        medication.purpose
    )

    medication.prescribed_by = data.get(
        "prescribed_by",
        medication.prescribed_by
    )

    medication.notes = data.get(
        "notes",
        medication.notes
    )

    medication.active = data.get(
        "active",
        medication.active
    )

    db.session.commit()

    return jsonify({
        "status": "Medication updated"
    })
    
@patients_bp.route("/<int:patient_id>/medications/<int:medication_id>", methods=["DELETE"])
@require_role("doctor")
def delete_medication(patient_id, medication_id):

    medication = Medication.query.filter_by(
        patient_id=patient_id,
        id=medication_id
    ).first_or_404()

    db.session.delete(medication)

    db.session.commit()

    return jsonify({
        "status": "Medication deleted"
    })

# ─────────────────────────────────────────────
# NOTE: women's history is now saved/read exclusively via women.py's
#   GET/POST/PUT /api/women/<patient_id>
# This route used to also try to set women.no_known_women_conditions,
# a column that doesn't exist on WomanHistory (pregnant/due_date/
# nursing_child are the only real columns) — a silent no-op. The
# validation also unconditionally required that phantom flag whenever
# both pregnant and nursing were false, which would have rejected every
# legitimate "not pregnant, not nursing" answer once a frontend actually
# sent the required keys. women.py's version fixes both issues.
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════
#  SAVE FAMILY DOCTOR
#  POST/PUT /api/patients/<patient_id>/family-doctor
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/family-doctor", methods=["POST", "PUT"])
@require_role("reception")
def save_family_doctor(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()
    if not doc:
        doc = FamilyDoctor(patient_id=patient_id)
        db.session.add(doc)

    doc.doctor_name    = data.get("doctor_name",    doc.doctor_name)
    doc.doctor_phone   = data.get("doctor_phone",   doc.doctor_phone)
    doc.doctor_address = data.get("doctor_address", doc.doctor_address)

    db.session.commit()
    return jsonify({"status": "family doctor saved"}), 200


# ══════════════════════════════════════════════
#  SAVE CONSENT
#  POST/PUT /api/patients/<patient_id>/consent
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/consent", methods=["POST", "PUT"])
@require_role("reception")
def save_consent(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    consent = Consent.query.filter_by(patient_id=patient_id).first()
    if not consent:
        consent = Consent(patient_id=patient_id)
        db.session.add(consent)

    consent.agreed       = bool(data.get("agreed", False))
    consent.signature    = data.get("signature")    or None
    consent.relationship = data.get("relationship") or None
    consent.consent_date = parse_date(data.get("consent_date"))

    db.session.commit()
    return jsonify({"status": "consent saved"}), 200

# ══════════════════════════════════════════════
# SEARCH PATIENTS
# GET /api/patients/search?q=...
# ══════════════════════════════════════════════

@patients_bp.route("/search", methods=["GET"])
@require_login
def search_patients():

    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    patients = (
        Patient.query.filter(
            (Patient.name.ilike(f"%{q}%")) |
            (Patient.mobile.ilike(f"%{q}%")) |
            (Patient.case_number.ilike(f"%{q}%"))
        )
        .order_by(Patient.name.asc())
        .all()
    )

    results = []

    for patient in patients:

        visits = (
            Visit.query
            .filter_by(patient_id=patient.id)
            .order_by(Visit.visit_date.desc())
            .all()
        )

        latest_visit = visits[0] if visits else None

        active_visit = next(
            (
                v for v in visits
                if v.status in ["CREATED", "IN_PROGRESS"]
            ),
            None
        )

        results.append({
            "patient_id": patient.id,
            "case_number": patient.case_number,
            "name": patient.name,
            "mobile": patient.mobile,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,

            # Summary
            "visit_count": len(visits),

            "current_visit_id": (
                active_visit.id if active_visit else None
            ),

            "current_status": (
                active_visit.status if active_visit else None
            ),

            "assigned_doctor": (
                active_visit.assigned_doctor if active_visit else None
            ),

            "latest_visit_date": (
                latest_visit.visit_date.isoformat()
                if latest_visit and latest_visit.visit_date
                else None
            ),

            # Visit History
            "visits": [
                {
                    "visit_id": v.id,
                    "visit_date": (
                        v.visit_date.isoformat()
                        if v.visit_date
                        else None
                    ),
                    "status": v.status,
                    "chief_complaint": v.chief_complaint,
                    "assigned_doctor": v.assigned_doctor,
                }
                for v in visits
            ]
        })

    return jsonify(results), 200