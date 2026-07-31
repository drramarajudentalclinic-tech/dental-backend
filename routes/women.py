from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import WomanHistory, Patient
import traceback

women_bp = Blueprint("women", __name__)


def parse_flexible_date(value):
    """Accepts YYYY-MM-DD, DD-MM-YYYY, or DD/MM/YYYY. Returns a date or None."""
    if not value or not str(value).strip():
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


@women_bp.route("/women/<int:patient_id>", methods=["GET", "POST", "PUT"])
def save_women_history(patient_id):
    try:
        patient = Patient.query.get_or_404(patient_id)
        record = WomanHistory.query.filter_by(patient_id=patient_id).first()

        if request.method == "GET":
            if not record:
                return jsonify({}), 200
            return jsonify({
                "pregnant":      record.pregnant,
                "due_date":      record.due_date.isoformat() if record.due_date else "",
                "nursing_child": record.nursing_child,
            }), 200

        # Women's health history only applies to female patients.
        if patient.gender != "Female":
            return jsonify({"error": "Not a female patient"}), 400

        data = request.get_json() or {}

        # PatientWomen.jsx marks both "Are you pregnant?" and "Are you
        # nursing a child?" as mandatory Yes/No questions — require both
        # to actually be answered (key present) rather than requiring a
        # "no known conditions" flag the UI doesn't have a control for.
        # NOTE: an earlier version of this check (in patients.py) required
        # data.get("no_known_women_conditions") to be true when neither
        # pregnant nor nursing applied — but the frontend never sends that
        # field, so it silently rejected every legitimate "No to both"
        # answer for an unaffected patient. Requiring the keys be present
        # fixes that without losing the mandatory-answer intent.
        if "pregnant" not in data or "nursing_child" not in data:
            return jsonify({
                "error": "Please answer both pregnancy and nursing questions."
            }), 400

        if not record:
            record = WomanHistory(patient_id=patient_id)
            db.session.add(record)

        record.pregnant      = bool(data.get("pregnant"))
        record.nursing_child = bool(data.get("nursing_child"))
        record.due_date       = parse_flexible_date(data.get("due_date")) if record.pregnant else None

        db.session.commit()
        return jsonify({"status": "women history saved"}), 200

    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500