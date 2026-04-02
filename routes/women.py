from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import WomanHistory

women_bp = Blueprint("women", __name__)

# -----------------------------
# GET / CREATE / UPDATE WOMEN HISTORY
# /api/women/<patient_id>
# -----------------------------
@women_bp.route("/women/<int:patient_id>", methods=["GET", "POST", "PUT"])
def save_women_history(patient_id):
    record = WomanHistory.query.filter_by(patient_id=patient_id).first()

    if request.method == "GET":
        if not record:
            return jsonify({}), 200
        return jsonify({
            "pregnant": record.pregnant,
            "due_date": record.due_date.isoformat() if record.due_date else "",
            "nursing_child": record.nursing_child
        }), 200

    data = request.get_json() or {}

    if not record:
        record = WomanHistory(patient_id=patient_id)
        db.session.add(record)

    record.pregnant = bool(data.get("pregnant", False))
    record.nursing_child = bool(data.get("nursing_child", False))

    if record.pregnant and data.get("due_date"):
        record.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
    else:
        record.due_date = None

    db.session.commit()
    return jsonify({"status": "women history saved"}), 200
