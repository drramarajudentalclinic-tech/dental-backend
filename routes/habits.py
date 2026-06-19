from flask import Blueprint, request, jsonify
from database import db
from models import Habit
from datetime import datetime

habits_bp = Blueprint("habits", __name__)

KNOWN_HABIT_KEYS = {"smoking", "alcohol", "tobacco", "pan", "gutka", "drugs"}


# ══════════════════════════════════════════════════════
#  PUT /api/habits/<patient_id>
#  Accepts flat checkbox dict from frontend:
#  {
#    smoking: true/false,
#    smoking_detail: "...",
#    alcohol: true/false,
#    alcohol_detail: "...",
#    tobacco: true/false,
#    tobacco_detail: "...",
#    no_known_habits: true/false
#  }
# ══════════════════════════════════════════════════════
@habits_bp.route("/habits/<int:patient_id>", methods=["PUT", "POST"])
def save_habits(patient_id):
    data = request.get_json() or {}

    record = Habit.query.filter_by(patient_id=patient_id).first()
    if not record:
        record = Habit(patient_id=patient_id)
        db.session.add(record)

    no_known = bool(data.get("no_known_habits", False))
    record.no_known_habits = no_known

    if no_known:
        record.smoking   = None
        record.alcohol   = None
        record.tobacco   = None
        record.other_habit = None
    else:
        # smoking
        if data.get("smoking"):
            detail = (data.get("smoking_detail") or "").strip()
            record.smoking = detail if detail else "Yes"
        else:
            record.smoking = None

        # alcohol
        if data.get("alcohol"):
            detail = (data.get("alcohol_detail") or "").strip()
            record.alcohol = detail if detail else "Yes"
        else:
            record.alcohol = None

        # tobacco
        if data.get("tobacco"):
            detail = (data.get("tobacco_detail") or "").strip()
            record.tobacco = detail if detail else "Yes"
        else:
            record.tobacco = None

        record.other_habit = data.get("other_habit") or None

    record.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "habits saved"}), 200


# ══════════════════════════════════════════════════════
#  GET /api/habits/<patient_id>
#  Returns flat dict matching what the frontend sends
# ══════════════════════════════════════════════════════
@habits_bp.route("/habits/<int:patient_id>", methods=["GET"])
def list_habits(patient_id):
    record = Habit.query.filter_by(patient_id=patient_id).first()
    if not record:
        return jsonify({}), 200

    return jsonify({
        "smoking":         bool(record.smoking) if record.smoking else False,
        "smoking_detail":  record.smoking if record.smoking and record.smoking != "Yes" else "",
        "alcohol":         bool(record.alcohol) if record.alcohol else False,
        "alcohol_detail":  record.alcohol if record.alcohol and record.alcohol != "Yes" else "",
        "tobacco":         bool(record.tobacco) if record.tobacco else False,
        "tobacco_detail":  record.tobacco if record.tobacco and record.tobacco != "Yes" else "",
        "no_known_habits": bool(record.no_known_habits),
    }), 200