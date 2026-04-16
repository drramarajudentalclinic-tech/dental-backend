import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from database import db
from models import (
    Visit,
    Patient,
    MedicalHistory,
    AllergyRecord,
    Habit,
    WomanHistory,
    FamilyDoctor,
    Consent,
)
from datetime import date, datetime

ALLOWED_CBCT_EXTENSIONS = {
    "dcm", "zip", "rar", "tar", "gz",   # DICOM / archives
    "jpg", "jpeg", "png",                # plain images
    "pdf",                               # reports
}

def _allowed_cbct(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_CBCT_EXTENSIONS
    )

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


# ---------------------------------
# CREATE VISIT
# POST /api/visits
# ---------------------------------
@visits_bp.route("/visits", methods=["POST"])
def create_visit():
    data = request.get_json() or {}
    valid = {col.name for col in Visit.__table__.columns} - {"id"}
    filtered = {k: v for k, v in data.items() if k in valid}
    visit = Visit(**filtered)
    db.session.add(visit)
    db.session.commit()
    return jsonify({"visit_id": visit.id}), 201


# ---------------------------------
# GET VISIT + FULL PATIENT SNAPSHOT
# GET /api/visits/<visit_id>
# ---------------------------------
@visits_bp.route("/visits/<int:visit_id>", methods=["GET"])
def get_visit(visit_id):
    visit   = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)

    medical    = MedicalHistory.query.filter_by(patient_id=patient.id).first()
    allergies  = AllergyRecord.query.filter_by(patient_id=patient.id).all()
    habits     = Habit.query.filter_by(patient_id=patient.id).all()
    women      = WomanHistory.query.filter_by(patient_id=patient.id).first()
    family_doc = FamilyDoctor.query.filter_by(patient_id=patient.id).first()
    consent    = Consent.query.filter_by(patient_id=patient.id).first()

    # chief_complaint: use visit's if set, fall back to patient's
    chief_complaint = (
        visit.chief_complaint
        if visit.chief_complaint and visit.chief_complaint.strip()
        else (patient.chief_complaint or "")
    )

    # Normalise status for frontend — always lowercase
    status = (visit.status or "open").lower()   # "open" | "closed"

    return jsonify({

        "visit": {
            "id":                visit.id,
            "status":            status,
            "chief_complaint":   chief_complaint,
            "followup_treatment": visit.followup_treatment or "",
            "visit_date":        visit.visit_date.isoformat() if visit.visit_date else None,
            "date":              visit.visit_date.strftime("%d-%b-%Y") if visit.visit_date else None,
            "closed_at":         visit.closed_at.isoformat() if getattr(visit, "closed_at", None) else None,
            # ── Billing / clinical snapshot (written at close time) ──
            "billing_note":      getattr(visit, "billing_note",   None) or "",
            "diagnosis":         getattr(visit, "diagnosis",      None) or "",
            "treatment_done":    getattr(visit, "treatment_done", None) or "",
            "treatment_plan":    getattr(visit, "treatment_plan", None) or "",
            "advice":            getattr(visit, "advice",         None) or "",
        },

        "patient": {
            "id":              patient.id,
            "case_number":     patient.case_number,
            "name":            patient.name,
            "date":            patient.date.isoformat() if patient.date else None,
            "date_of_birth":   patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "age":             resolve_age(patient.date_of_birth, patient.age),
            "gender":          patient.gender,
            "marital_status":  patient.marital_status,
            "mobile":          patient.mobile,
            "email":           patient.email,
            "blood_group":     patient.blood_group,
            "address":         patient.address,
            "profession":      patient.profession,
            "referred_by":     patient.referred_by,
            "chief_complaint": patient.chief_complaint,
        },

        "medical": row_to_dict(medical, ["id", "patient_id", "updated_at"]),

        "allergy": {
            "rows": [
                {
                    "id":       a.id,
                    "type":     a.type,
                    "allergen": a.allergen,
                    "reaction": a.reaction,
                    "severity": a.severity,
                    "notes":    a.notes,
                }
                for a in allergies
            ]
        },

        "habits": [
            {
                "id":             h.id,
                "habit_type":     h.habit_type,
                "has_habit":      h.has_habit,
                "frequency":      h.frequency,
                "duration_years": h.duration_years,
                "remarks":        h.remarks,
            }
            for h in habits
        ],

        "women": {
            "pregnant":      women.pregnant      if women else False,
            "due_date":      women.due_date.isoformat() if women and women.due_date else None,
            "nursing_child": women.nursing_child if women else False,
        },

        "family_doctor": row_to_dict(family_doc, ["id", "patient_id"]),

        "consent": row_to_dict(consent, ["id", "patient_id"]),

    }), 200


# ---------------------------------
# UPLOAD CBCT
# POST /api/visits/<visit_id>/cbct
# ---------------------------------
@visits_bp.route("/visits/<int:visit_id>/cbct", methods=["POST"])
def upload_cbct(visit_id):
    from models import CBCTFile

    visit = Visit.query.get_or_404(visit_id)

    if "file" not in request.files:
        return jsonify({"error": "No file part in request. Send file under key 'file'."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_cbct(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_CBCT_EXTENSIONS))}"
        }), 400

    original_name = file.filename
    ext           = original_name.rsplit(".", 1)[1].lower()
    unique_name   = f"visit_{visit_id}_cbct_{uuid.uuid4().hex}.{ext}"
    safe_name     = secure_filename(unique_name)

    upload_folder = current_app.config.get("CBCT_UPLOAD_FOLDER") or \
                    os.path.join(current_app.config.get("UPLOAD_FOLDER", "/tmp"), "cbct")
    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, safe_name)
    file.save(save_path)

    file_size = os.path.getsize(save_path)
    uploaded_by = request.form.get("uploaded_by") or request.headers.get("X-Username")

    cbct = CBCTFile(
        visit_id      = visit_id,
        filename      = safe_name,
        original_name = original_name,
        file_path     = save_path,
        file_size     = file_size,
        uploaded_by   = uploaded_by,
    )
    db.session.add(cbct)
    db.session.commit()

    return jsonify({
        "message":   "CBCT uploaded successfully",
        "cbct":      cbct.to_dict(),
    }), 200


# ---------------------------------
# GET CBCT FILES FOR A VISIT
# GET /api/visits/<visit_id>/cbct
# ---------------------------------
@visits_bp.route("/visits/<int:visit_id>/cbct", methods=["GET"])
def get_cbct(visit_id):
    from models import CBCTFile

    Visit.query.get_or_404(visit_id)  # 404 if visit doesn't exist
    files = CBCTFile.query.filter_by(visit_id=visit_id).order_by(CBCTFile.uploaded_at.desc()).all()

    return jsonify({
        "visit_id": visit_id,
        "cbct_files": [f.to_dict() for f in files],
    }), 200


# ---------------------------------
# DELETE A CBCT FILE
# DELETE /api/visits/<visit_id>/cbct/<cbct_id>
# ---------------------------------
@visits_bp.route("/visits/<int:visit_id>/cbct/<int:cbct_id>", methods=["DELETE"])
def delete_cbct(visit_id, cbct_id):
    from models import CBCTFile

    cbct = CBCTFile.query.filter_by(id=cbct_id, visit_id=visit_id).first_or_404()

    # Remove file from disk (best-effort)
    try:
        if os.path.exists(cbct.file_path):
            os.remove(cbct.file_path)
    except OSError:
        pass

    db.session.delete(cbct)
    db.session.commit()

    return jsonify({"message": "CBCT file deleted", "cbct_id": cbct_id}), 200


# ---------------------------------
# CLOSE VISIT
# PUT /api/visits/<visit_id>/close
# ---------------------------------
@visits_bp.route("/visits/<int:visit_id>/close", methods=["PUT"])
def close_visit(visit_id):
    from models import Consultation
    visit = Visit.query.get_or_404(visit_id)

    if (visit.status or "").lower() == "closed":
        return jsonify({"message": "Visit already closed", "visit_id": visit_id}), 200

    # force=True  → parse even without Content-Type: application/json
    # silent=True → return None instead of raising 400 when body is empty
    data = request.get_json(force=True, silent=True) or {}

    # Mark closed
    visit.status    = "closed"
    visit.closed_at = datetime.utcnow()

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

    db.session.commit()

    return jsonify({
        "message":        "Visit closed successfully",
        "visit_id":       visit_id,
        "status":         visit.status,
        "closed_at":      visit.closed_at.strftime("%d-%b-%Y %H:%M"),
        "billing_note":   visit.billing_note   or "",
        "diagnosis":      visit.diagnosis      or "",
        "treatment_done": visit.treatment_done or "",
        "treatment_plan": visit.treatment_plan or "",
        "advice":         visit.advice         or "",
    }), 200