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
                patient_id      = patient.id,
                status          = "OPEN",
                chief_complaint = chief_complaint,
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
#  SEARCH ALL PATIENTS
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
                "visit_id":        v.id,
                "visit_date":      v.visit_date.isoformat() if v.visit_date else None,
                "status":          v.status,
                "case_number":     p.case_number,
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
    allergy    = AllergyRecord.query.filter_by(patient_id=patient_id).first()
    habit      = Habit.query.filter_by(patient_id=patient_id).first()
    family_doc = FamilyDoctor.query.filter_by(patient_id=patient_id).first()
    consent    = Consent.query.filter_by(patient_id=patient_id).first()

    women = None
    if patient.gender == "Female":
        women = WomanHistory.query.filter_by(patient_id=patient_id).first()

    return jsonify({
        "patient":       serialize_patient(patient),
        "medical":       medical.to_dict() if medical else {},
        "allergy":       allergy.to_dict() if allergy else {
            "drug_allergy": False, "food_allergy": False, "latex_allergy": False,
            "iodine_allergy": False, "anesthesia_allergy": False,
            "other_allergy": "", "no_known_allergies": False,
        },
        "habits":        habit.to_dict() if habit else {
            "smoking": "", "alcohol": "", "tobacco": "",
            "other_habit": "", "no_known_habits": False,
        },
        "women":         women.to_dict() if women else {},
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


# ══════════════════════════════════════════════
#  SAVE ALLERGIES  (flat checkbox model)
#  POST/PUT /api/patients/<patient_id>/allergy
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/allergy", methods=["POST", "PUT"])
def save_allergy(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    ALLERGY_FLAGS = [
        "drug_allergy", "food_allergy", "latex_allergy",
        "iodine_allergy", "anesthesia_allergy",
    ]

    has_allergy   = any(to_bool(data.get(f)) for f in ALLERGY_FLAGS)
    has_other     = bool((data.get("other_allergy") or "").strip())
    no_known      = to_bool(data.get("no_known_allergies") or data.get("No_Known_Allergies"))

    if not has_allergy and not has_other and not no_known:
        return jsonify({
            "error": "Allergy acknowledgement required. "
                     "Select at least one allergy or confirm no known allergies."
        }), 400

    record = AllergyRecord.query.filter_by(patient_id=patient_id).first()
    if not record:
        record = AllergyRecord(patient_id=patient_id)
        db.session.add(record)

    if no_known:
        # Confirmed no allergies — clear all flags
        for f in ALLERGY_FLAGS:
            setattr(record, f, False)
        record.other_allergy      = None
        record.no_known_allergies = True
    else:
        for f in ALLERGY_FLAGS:
            setattr(record, f, to_bool(data.get(f, False)))
        record.other_allergy      = (data.get("other_allergy") or "").strip() or None
        record.no_known_allergies = False

    db.session.commit()
    return jsonify({"status": "allergies saved"}), 200


# ══════════════════════════════════════════════
#  SAVE HABITS
#  POST/PUT /api/patients/<patient_id>/habits
# ══════════════════════════════════════════════
@patients_bp.route("/<int:patient_id>/habits", methods=["POST", "PUT"])
def save_habits(patient_id):
    Patient.query.get_or_404(patient_id)
    data = request.json or {}

    HABIT_FIELDS = ["smoking", "alcohol", "tobacco"]

    has_habit = any((data.get(f) or "").strip() for f in HABIT_FIELDS)
    has_other = bool((data.get("other_habit") or "").strip())
    no_known  = to_bool(data.get("no_known_habits") or data.get("No_Known_Habits"))

    if not has_habit and not has_other and not no_known:
        return jsonify({
            "error": "Habits acknowledgement required. "
                     "Enter at least one habit or confirm no known habits."
        }), 400

    habit = Habit.query.filter_by(patient_id=patient_id).first()
    if not habit:
        habit = Habit(patient_id=patient_id)
        db.session.add(habit)

    if no_known:
        habit.smoking        = None
        habit.alcohol        = None
        habit.tobacco        = None
        habit.other_habit    = None
        habit.no_known_habits = True
    else:
        habit.smoking         = (data.get("smoking")     or "").strip() or None
        habit.alcohol         = (data.get("alcohol")     or "").strip() or None
        habit.tobacco         = (data.get("tobacco")     or "").strip() or None
        habit.other_habit     = (data.get("other_habit") or "").strip() or None
        habit.no_known_habits = False

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

    no_known  = to_bool(data.get("no_known_women_conditions") or data.get("No_Known_Women_Conditions"))
    pregnant  = to_bool(data.get("pregnant"))
    nursing   = to_bool(data.get("nursing_child"))

    if not pregnant and not nursing and not no_known:
        return jsonify({
            "error": "Women's health acknowledgement required. "
                     "Select an applicable condition or confirm none apply."
        }), 400

    women = WomanHistory.query.filter_by(patient_id=patient_id).first()
    if not women:
        women = WomanHistory(patient_id=patient_id)
        db.session.add(women)

    if no_known:
        women.pregnant                  = False
        women.due_date                  = None
        women.nursing_child             = False
        women.no_known_women_conditions = True
    else:
        women.pregnant                  = pregnant
        women.due_date                  = parse_date(data.get("due_date")) if pregnant else None
        women.nursing_child             = nursing
        women.no_known_women_conditions = False

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