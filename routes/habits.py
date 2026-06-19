from flask import Blueprint, request, jsonify
from database import db
from models import Habit
from datetime import datetime

habits_bp = Blueprint("habits", __name__)


@habits_bp.route("/habits/<int:patient_id>", methods=["GET"])
def get_habits(patient_id):

    record = Habit.query.filter_by(patient_id=patient_id).first()

    if not record:
        return jsonify({}), 200

    return jsonify({
        "smoking": bool(record.smoking),
        "smoking_detail": record.smoking or "",

        "alcohol": bool(record.alcohol),
        "alcohol_detail": record.alcohol or "",

        "tobacco": bool(record.tobacco),
        "tobacco_detail": record.tobacco or "",

        "pan_chewing": bool(record.pan_chewing),
        "pan_chewing_detail": record.pan_chewing or "",

        "spicy_foods": bool(record.spicy_foods),
        "spicy_foods_detail": record.spicy_foods or "",

        "no_habits": bool(record.no_habits),
    })


@habits_bp.route("/habits/<int:patient_id>", methods=["POST", "PUT"])
def save_habits(patient_id):

    data = request.get_json()

    record = Habit.query.filter_by(patient_id=patient_id).first()

    if not record:
        record = Habit(patient_id=patient_id)
        db.session.add(record)

    no_habits = data.get("no_habits", False)

    record.no_habits = no_habits

    if no_habits:

        record.smoking = None
        record.alcohol = None
        record.tobacco = None
        record.pan_chewing = None
        record.spicy_foods = None

    else:

        record.smoking = (
            data.get("smoking_detail")
            if data.get("smoking")
            else None
        )

        record.alcohol = (
            data.get("alcohol_detail")
            if data.get("alcohol")
            else None
        )

        record.tobacco = (
            data.get("tobacco_detail")
            if data.get("tobacco")
            else None
        )

        record.pan_chewing = (
            data.get("pan_chewing_detail")
            if data.get("pan_chewing")
            else None
        )

        record.spicy_foods = (
            data.get("spicy_foods_detail")
            if data.get("spicy_foods")
            else None
        )

    record.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": "Habits saved successfully"
    }), 200