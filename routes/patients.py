from flask import Blueprint, request, jsonify
from database import db
from models import (
    Patient,
    MedicalHistory,
    AllergyRecord,
    Habit,
    WomanHistory,
    FamilyDoctor,
    Consent,
    Visit,
)
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date
from flask_jwt_extended import jwt_required, get_jwt_identity
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
def patients():

    # ── CREATE ──────────────────────────────────────────────────
    if request.method == "POST":
        data = request.json or {}

        print("📥 Patient POST keys:", list(data.keys()))

        parsed_dob      = parse_date(data.get("dob") or data.get("date_of_birth"))
        parsed_date     = parse_date(data.get("date"))
        chief_complaint = get_chief_complaint(data)

        print("📥 chief_complaint value:", chief_complaint)

        patient = Patient(
            case_number     = data.get("case_number"),
            name            = data.get("name"),
            date            = parsed_date,
            age             = None if parsed_dob else data.get("age"),
            date_of_birth   = parsed_dob,
            gender          = data.get("gender"),
            marital_status  = data.get("marital_status"),
            mobile          = data.get("mobile"),
            email           = data.get("email"),
            blood_group     = data.get("blood_group"),
            address         = data.get("address"),
            profession      = data.get("profession"),
            referred_by     = data.get("referred_by"),
            chief_complaint = chief_complaint,
        )

        try:
            db.session.add(patient)
            db.session.flush()   # get patient.id before visit insert

            visit = Visit(
                patient_id      = patient.id,
                status          = "OPEN",
                chief_complaint = chief_complaint,
                # FIX: Visit.visit_date is DateTime — pass datetime, not date
                visit_date      = datetime.utcnow(),
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
            return jsonify({"error": "Internal server error", "detail": str(e)}), 500

        return jsonify({
            "patient_id": patient.id,
            "visit_id":   visit.id,
        }), 201

    # ── SEARCH / LIST ────────────────────────────────────────────
    search = request.args.get("search", "").strip()
    query  = Patient.query

    if search:
        query = query.filter(
            (Patient.name.contains(search)) |
            (Patient.case_number.contains(search)) |
            (Patient.mobile.contains(search))
        )

    return jsonify([serialize_patient(p) for p in query.all()]), 200


# ══════════════════════════════════════════════
#  SEARCH ALL PATIENTS (for doctor dashboard lookup)
#  GET /api/patients/search?q=...
# ══════════════════════════════════════════════
@patients_bp.route("/search", methods=["GET"])
def search_patients():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 200

    patients = Patient.query.filter(
        (Patient.name.contains(q)) |
        (Patient.case_number.contains(q)) |
        (Patient.mobile.contains(q))
    ).all()

    result = []
    for p in patients:
        visits = []
        for v in p.visits:
            visits.append({
                "visit_id":       v.id,
                "visit_date":     v.visit_date.isoformat() if v.visit_date else None,
                "status":         v.status,
                "case_number":    p.case_number,
                "chief_complaint": v.chief_complaint or "",
            })
        result.append({
            "patient_id":  p.id,
            "name":        p.name,
            "mobile":      p.mobile or "",
            "age":         resolve_age(p.date_of_birth, p.age),
            "gender":      p.gender,
            "blood_group": p.blood_group,
            "visits":      sorted(visits, key=lambda x: x["visit_date"] or "", reverse=True),
        })

    return jsonify(result), 200


# ══════════════════════════════════════════════
#  GET FULL PATIENT
#  GET /api/patients/<patient_id>
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient    = Patient.query.get_or_404(patient_id)
    medical    = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    allergies  = AllergyRecord.query.filter_by(patient_id=patient_id).all()
    habits     = Habit.query.filter_by(patient_id=patient_id).all()
    family_doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()
    consent    = Consent.query.filter_by(patient_id=patient_id).first()

    women = None
    if patient.gender == "Female":
        women = WomanHistory.query.filter_by(patient_id=patient_id).first()

    return jsonify({
        "patient":       serialize_patient(patient),
        "medical":       model_to_dict(medical,    ["id", "patient_id"]),
        "allergy": {
            "rows": [
                model_to_dict(a, ["id", "patient_id", "created_at"])
                for a in allergies
            ]
        },
        "habits":        [model_to_dict(h, ["id", "patient_id"]) for h in habits],
        "women":         model_to_dict(women,      ["id", "patient_id"]),
        "family_doctor": model_to_dict(family_doc, ["id", "patient_id"]),
        "consent":       model_to_dict(consent,    ["id", "patient_id"]),
    }), 200


# ══════════════════════════════════════════════
#  UPDATE PATIENT
#  PUT /api/patients/<patient_id>
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    data    = request.json or {}

    if "dob" in data or "date_of_birth" in data:
        patient.date_of_birth = parse_date(data.get("dob") or data.get("date_of_birth"))
        patient.age = None if patient.date_of_birth else patient.age

    if "date" in data:
        patient.date = parse_date(data["date"])

    if "age" in data and not patient.date_of_birth:
        patient.age = data["age"]

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
        open_visit = Visit.query.filter_by(patient_id=patient_id, status="OPEN").first()
        if open_visit and not open_visit.chief_complaint:
            open_visit.chief_complaint = complaint_val

    patient.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "updated"}), 200


# ══════════════════════════════════════════════
#  SAVE MEDICAL HISTORY
#  POST/PUT /api/patients/<patient_id>/medical
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/medical", methods=["POST", "PUT"])
def save_medical(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    medical = MedicalHistory.query.filter_by(patient_id=patient_id).first()
    if not medical:
        medical = MedicalHistory(patient_id=patient_id)
        db.session.add(medical)

    valid = {col.name for col in medical.__table__.columns} - {"id", "patient_id"}
    for field, val in data.items():
        if field in valid:
            setattr(medical, field, val)

    db.session.commit()
    return jsonify({"status": "medical saved"}), 200


# ══════════════════════════════════════════════
#  SAVE ALLERGIES  (row-based)
#  POST/PUT /api/patients/<patient_id>/allergy
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/allergy", methods=["POST", "PUT"])
def save_allergy(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    rows = data.get("rows", [])
    AllergyRecord.query.filter_by(patient_id=patient_id).delete()

    for row in rows:
        allergen_type = (row.get("type") or "").strip()
        if not allergen_type and not row.get("allergen"):
            continue
        record = AllergyRecord(
            patient_id = patient_id,
            type       = allergen_type,
            allergen   = row.get("allergen") or None,
            reaction   = row.get("reaction") or None,
            severity   = row.get("severity") or None,
            notes      = row.get("notes")    or None,
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({"status": "allergies saved"}), 200


# ══════════════════════════════════════════════
#  SAVE HABITS
#  POST/PUT /api/patients/<patient_id>/habits
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/habits", methods=["POST", "PUT"])
def save_habits(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json

    if isinstance(data, dict):
        habit_list = [
            {"habit_type": k, "remarks": v}
            for k, v in data.items()
            if v not in (None, "", False)
        ]
    elif isinstance(data, list):
        habit_list = data
    else:
        return jsonify({"error": "Invalid habits format"}), 400

    Habit.query.filter_by(patient_id=patient_id).delete()

    valid = {col.name for col in Habit.__table__.columns} - {"id", "patient_id"}
    for h in habit_list:
        row = Habit(patient_id=patient_id)
        for field, val in h.items():
            if field in valid:
                setattr(row, field, val)
        db.session.add(row)

    db.session.commit()
    return jsonify({"status": "habits saved"}), 200


# ══════════════════════════════════════════════
#  SAVE WOMEN HISTORY
#  POST/PUT /api/patients/<patient_id>/women
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/women", methods=["POST", "PUT"])
def save_women_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if patient.gender != "Female":
        return jsonify({"error": "Not a female patient"}), 400

    data  = request.json or {}
    women = WomanHistory.query.filter_by(patient_id=patient_id).first()
    if not women:
        women = WomanHistory(patient_id=patient_id)
        db.session.add(women)

    if "due_date" in data:
        women.due_date = parse_date(data.pop("due_date"))

    valid = {col.name for col in women.__table__.columns} - {"id", "patient_id", "due_date"}
    for field, val in data.items():
        if field in valid:
            setattr(women, field, val)

    db.session.commit()
    return jsonify({"status": "women history saved"}), 200


# ══════════════════════════════════════════════
#  SAVE FAMILY DOCTOR
#  POST/PUT /api/patients/<patient_id>/family-doctor
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/family-doctor", methods=["POST", "PUT"])
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