from flask import Blueprint, jsonify, request
from models import (
    Visit,
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
    Payment,   # <-- add this
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
            "visit_id": v.id,
            "patient_id": patient.id,
            "case_number": patient.case_number,
            "patient_name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "mobile": patient.mobile,
            "chief_complaint": v.chief_complaint,
            "visit_date": (
                v.visit_date.isoformat()
                if v.visit_date else None
            ),
            "status": v.status,
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
@doctor_bp.route("/patients/search", methods=["GET"])
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

        results.append({
            "patient_id": patient.id,
            "case_number": patient.case_number,
            "name": patient.name,
            "mobile": patient.mobile,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "visits": [
                {
                    "visit_id": v.id,
                    "visit_date": (
                        v.visit_date.isoformat()
                        if v.visit_date else None
                    ),
                    "status": v.status,
                    "chief_complaint": v.chief_complaint,
                }
                for v in visits
            ]
        })

    return jsonify(results)

@doctor_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
def full_patient_history(patient_id):

    patient = Patient.query.get_or_404(patient_id)

    visits = (
        Visit.query
        .filter_by(patient_id=patient.id)
        .order_by(Visit.visit_date.desc())
        .all()
    )

    history = []

    for visit in visits:

        consultations = Consultation.query.filter_by(
            visit_id=visit.id
        ).all()

        prescriptions = Prescription.query.filter_by(
            visit_id=visit.id
        ).all()

        images = Image.query.filter_by(
            visit_id=visit.id
        ).all()

        cbct_files = CBCTFile.query.filter_by(
            visit_id=visit.id
        ).all()

        cbct_volumes = CBCTVolume.query.filter_by(
            visit_id=visit.id
        ).all()

        payments = Payment.query.filter_by(
            visit_id=visit.id
        ).all()

        history.append({

            "visit_id": visit.id,

            "visit_date":
                visit.visit_date.isoformat()
                if visit.visit_date else None,

            "status": visit.status,

            "chief_complaint": visit.chief_complaint,

            "diagnosis": visit.diagnosis,

            "treatment_done": visit.treatment_done,

            "treatment_plan": visit.treatment_plan,

            "advice": visit.advice,

            "consultations": [
                {
                    "id": c.id,
                    "diagnosis": c.diagnosis,
                    "treatment_done_today": c.treatment_done_today,
                    "treatment_plan": c.treatment_plan,
                    "advice": c.advice,
                    "doctor": c.doctor,
                }
                for c in consultations
            ],

            "prescriptions": [
                p.to_dict()
                for p in prescriptions
            ],

            "images": [
                {
                    "id": i.id,
                    "image_path": i.image_path,
                    "image_type": i.image_type,
                    "description": i.description,
                }
                for i in images
            ],

            "cbct_files": [
                f.to_dict()
                for f in cbct_files
            ],

            "cbct_volumes": [
                {
                    "id": c.id,
                    "study_date": c.study_date,
                    "institution": c.institution,
                    "num_slices": c.num_slices,
                }
                for c in cbct_volumes
            ],

            "payments": [
                {
                    "id": p.id,
                    "fee": p.fee,
                    "discount": p.discount,
                    "paid_amount": p.paid_amount,
                    "balance": p.balance,
                    "payment_method": p.payment_method,
                    "receipt_number": p.receipt_number,
                }
                for p in payments
            ]
        })

    return jsonify({
        "patient": {
            "id": patient.id,
            "case_number": patient.case_number,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "mobile": patient.mobile,
            "blood_group": patient.blood_group,
            "address": patient.address,
            "profession": patient.profession,
        },
        "history": history
    })