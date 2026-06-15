from flask import Blueprint, request, jsonify
from database import db
from models import Habit
from datetime import datetime

habits_bp = Blueprint("habits", __name__)

VALID_FIELDS = {"habit_type", "has_habit", "frequency", "duration_years", "remarks", "consent"}


def row_to_dict(h):
    return {
        "id":             h.id,
        "habit_type":     h.habit_type,
        "has_habit":      h.has_habit,
        "frequency":      h.frequency,
        "duration_years": h.duration_years,
        "remarks":        h.remarks,
        "consent":        h.consent,
        "updated_at":     h.updated_at.strftime("%d-%b-%Y %H:%M") if h.updated_at else None,
    }


# ══════════════════════════════════════════════════════
#  PUT /api/habits/<patient_id>
#  Accepts THREE formats:
#
#  1. Array of habit objects (DB / standard format):
#     [ { habit_type, has_habit, frequency, duration_years, remarks }, ... ]
#
#  2. Flat dict with string values (reception form format):
#     { smoking: "yes/10/15", alcohol: "occasionally/5/daily", tobacco: "no" }
#     Value format: "<yes|no>/<duration_years>/<frequency>"
#     Also accepts plain "Yes" / "No" (any case) from the toggle UI,
#     with optional "<field>_detail" free-text alongside it.
#
#  3. Single habit object (legacy):
#     { habit_type: "smoking", frequency: "DAILY", duration_years: 10 }
# ══════════════════════════════════════════════════════
@habits_bp.route("/habits/<int:patient_id>", methods=["PUT", "POST"])
def save_habits(patient_id):
    data = request.get_json()

    # ── Parse into a normalised list ──────────────────────────────────────────
    habit_list = []

    if isinstance(data, list):
        # Format 1: array of objects
        habit_list = data

    elif isinstance(data, dict):
        # Check if it looks like Format 2 (flat key→string dict)
        # i.e. keys are habit names, values are strings like "yes/10/daily"
        known_habit_keys = {"smoking", "alcohol", "tobacco", "pan", "gutka", "drugs"}
        is_flat = any(k in known_habit_keys for k in data.keys())

        if is_flat:
            # Format 2: flat dict
            for habit_type, val in data.items():
                if habit_type not in known_habit_keys:
                    continue  # skip *_detail and other keys, handled below

                if val is None or val is False:
                    continue

                val_str = str(val).strip()
                val_lower = val_str.lower()

                if not val_str or val_lower in ("no", "false", "0"):
                    continue  # explicit "No" → skip, no habit recorded

                detail = data.get(f"{habit_type}_detail")

                if val_lower == "yes":
                    # Toggle-UI format: "Yes" + optional free-text detail
                    habit_list.append({
                        "habit_type":     habit_type,
                        "has_habit":      True,
                        "frequency":      detail or None,
                        "duration_years": None,
                        "remarks":        None,
                        "consent":        None,
                    })
                else:
                    # Legacy slash format: "<yes|no>/<duration_years>/<frequency>"
                    parts = val_str.split("/")
                    has_habit = parts[0].strip().lower() not in ("no", "false", "0", "")
                    duration  = parts[1].strip() if len(parts) > 1 else None
                    frequency = parts[2].strip() if len(parts) > 2 else None

                    if not has_habit:
                        continue

                    habit_list.append({
                        "habit_type":     habit_type,
                        "has_habit":      has_habit,
                        "frequency":      frequency,
                        "duration_years": int(duration) if duration and duration.isdigit() else None,
                        "remarks":        None,
                        "consent":        None,
                    })
        else:
            # Format 3: single habit object
            if data.get("habit_type"):
                habit_list = [data]

    # ── Full replace: delete all existing habits for this patient ─────────────
    Habit.query.filter_by(patient_id=patient_id).delete()

    for h in habit_list:
        if not h.get("habit_type"):
            continue
        row = Habit(
            patient_id    = patient_id,
            habit_type    = h.get("habit_type"),
            has_habit     = h.get("has_habit", True),
            frequency     = h.get("frequency"),
            duration_years= h.get("duration_years"),
            remarks       = h.get("remarks"),
            consent       = h.get("consent"),
            updated_at    = datetime.utcnow(),
        )
        db.session.add(row)

    db.session.commit()
    return jsonify({"status": "habits saved"}), 200


# ══════════════════════════════════════════════════════
#  GET /api/habits/<patient_id>
#  Returns array of habit rows
# ══════════════════════════════════════════════════════
@habits_bp.route("/habits/<int:patient_id>", methods=["GET"])
def list_habits(patient_id):
    habits = Habit.query.filter_by(patient_id=patient_id).all()
    return jsonify([row_to_dict(h) for h in habits]), 200