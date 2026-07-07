from flask import Blueprint, request, jsonify
from database import db
import uuid

class Appointment(db.Model):
    __tablename__ = "appointments"

    appt_id     = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = db.Column(db.String(200), nullable=False)
    date        = db.Column(db.String(20),  nullable=False)
    time        = db.Column(db.String(10),  nullable=True)
    mobile      = db.Column(db.String(20),  nullable=True)   # nullable — auto-bookings from consultation may not have mobile
    case_number = db.Column(db.String(50),  nullable=True)
    treatment   = db.Column(db.String(200), nullable=True)
    notes       = db.Column(db.Text,        nullable=True)
    status      = db.Column(db.String(20),  nullable=False, default="pending")

    def to_dict(self):
        return {
            "appt_id":     self.appt_id,
            "name":        self.name,
            "date":        self.date,
            "time":        self.time,
            "mobile":      self.mobile,
            "case_number": self.case_number,
            "treatment":   self.treatment,
            "notes":       self.notes,
            "status":      self.status,
        }

appointments_bp = Blueprint("appointments", __name__)

@appointments_bp.route("/appointments", methods=["GET"])
def get_appointments():
    appts = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    return jsonify([a.to_dict() for a in appts]), 200

@appointments_bp.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    # name, date, time always required
    # mobile optional for auto-bookings from consultation
    # case_number required only when booking comes from consultation (source="consultation")
    #
    # NOTE: an explicit null (e.g. {"name": null}) used to slip past this
    # check — str(None).strip() is the non-empty string "None", which is
    # truthy, so validation passed and then crashed later at
    # data["name"].strip() since the real value was still None. Checking
    # the raw value first (before stringifying) closes that gap.
    for field in ["name", "date", "time"]:
        raw = data.get(field)
        if raw is None or not str(raw).strip():
            return jsonify({"error": f"'{field}' is required"}), 422
    if data.get("source") == "consultation":
        if not str(data.get("case_number") or "").strip():
            return jsonify({"error": "'case_number' is required for consultation bookings"}), 422
    appt = Appointment(
        name        = data["name"].strip(),
        date        = data["date"].strip(),
        time        = data["time"].strip(),
        mobile      = (data.get("mobile") or "").strip() or None,
        case_number = (data.get("case_number") or "").strip() or None,
        treatment   = (data.get("treatment") or "").strip() or None,
        notes       = (data.get("notes") or "").strip() or None,
        status      = data.get("status") or "pending",
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify(appt.to_dict()), 201

@appointments_bp.route("/appointments/<appt_id>", methods=["PUT"])
def update_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    data = request.get_json() or {}

    # Required fields: only overwrite if a real, non-empty value was sent —
    # never let an explicit null wipe out name/date/time (the DB column is
    # nullable=False, so that would otherwise crash at commit time).
    for field in ["name", "date", "time"]:
        if field in data:
            val = data.get(field)
            if val is not None and str(val).strip():
                setattr(appt, field, str(val).strip())

    # Optional fields: null explicitly clears them; a real value updates them.
    for field in ["mobile", "case_number", "treatment", "notes"]:
        if field in data:
            val = data.get(field)
            setattr(appt, field, (str(val).strip() or None) if val is not None else None)

    if data.get("status"):
        appt.status = data["status"]

    db.session.commit()
    return jsonify(appt.to_dict()), 200

@appointments_bp.route("/appointments/<appt_id>", methods=["DELETE"])
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    return jsonify({"deleted": appt_id}), 200