from flask import Blueprint, request, jsonify
from database import db
from models import Consultation
from datetime import datetime
from sqlalchemy import text

consult_bp = Blueprint("consult", __name__)


# ─── ensure follow_up_time column exists (safe migration) ───────────────────
def _ensure_follow_up_time_column():
    """
    Add follow_up_time TEXT column to consultations table if it doesn't exist.
    Runs once at startup — safe to call multiple times (catches the error).
    """
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE consultations ADD COLUMN follow_up_time TEXT"))
            conn.commit()
    except Exception:
        pass  # Column already exists — that's fine


# ─── helper: safely parse a date string → date object or None ───────────────
def parse_date(value):
    if not value or not str(value).strip():
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


# ─── helper: sanitise incoming JSON before passing to the model ─────────────
def sanitise(data: dict) -> dict:
    """
    Convert any date-like keys from empty string / raw string
    to a proper Python date object (or None) so SQLite doesn't crash.
    follow_up_time is a plain TIME string (e.g. "11:00") — do NOT parse as date.
    """
    DATE_FIELDS = {"follow_up_date", "date", "created_at"}
    # TIME fields must pass through as plain strings — never treat as dates
    TIME_FIELDS = {"follow_up_time"}
    clean = {}
    for k, v in data.items():
        if k in DATE_FIELDS:
            clean[k] = parse_date(v)
        elif k in TIME_FIELDS:
            # Store as plain string; convert empty string to None
            clean[k] = str(v).strip() if v and str(v).strip() else None
        else:
            clean[k] = v
    return clean


# ─── helper: serialise a consultation row including follow_up_time ───────────
def _row_to_dict(c) -> dict:
    """
    Serialise a Consultation ORM object to a plain dict.
    Always includes follow_up_time, falling back to direct SQL if the ORM
    attribute is missing (e.g. column added after model was compiled).
    """
    row = {
        k: (v.isoformat() if hasattr(v, "isoformat") else v)
        for k, v in c.__dict__.items()
        if not k.startswith("_")
    }
    # Guarantee follow_up_time is always present in the response
    if "follow_up_time" not in row:
        try:
            with db.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT follow_up_time FROM consultations WHERE id = :id"),
                    {"id": c.id}
                ).fetchone()
            row["follow_up_time"] = result[0] if result else None
        except Exception:
            row["follow_up_time"] = None
    return row


# -----------------------------
# ADD CONSULTATION
# POST /api/visits/<visit_id>/consultations
# -----------------------------
@consult_bp.route("/visits/<int:visit_id>/consultations", methods=["POST"])
def add_consult(visit_id):
    _ensure_follow_up_time_column()

    raw  = request.get_json() or {}
    data = sanitise(raw)

    # Separate follow_up_time before ORM filtering (column may not be in model yet)
    follow_up_time = data.pop("follow_up_time", None)

    valid_columns = {col.name for col in Consultation.__table__.columns}
    data = {k: v for k, v in data.items() if k in valid_columns}

    c = Consultation(visit_id=visit_id, **data)
    db.session.add(c)
    db.session.flush()  # get c.id before commit

    # Write follow_up_time directly via SQL so it's always persisted
    if follow_up_time:
        db.session.execute(
            text("UPDATE consultations SET follow_up_time = :t WHERE id = :id"),
            {"t": follow_up_time, "id": c.id}
        )

    db.session.commit()

    # Return the full record (including follow_up_time) so the frontend
    # can update immediately without a separate GET
    return jsonify({
        "status": "added",
        "id": c.id,
        "follow_up_time": follow_up_time,
        "follow_up_date": data.get("follow_up_date").isoformat()
            if data.get("follow_up_date") and hasattr(data.get("follow_up_date"), "isoformat")
            else data.get("follow_up_date") or "",
    }), 201


# -----------------------------
# LIST CONSULTATIONS
# GET /api/visits/<visit_id>/consultations
# -----------------------------
@consult_bp.route("/visits/<int:visit_id>/consultations", methods=["GET"])
def list_consult(visit_id):
    _ensure_follow_up_time_column()
    data = Consultation.query.filter_by(visit_id=visit_id).all()
    return jsonify([_row_to_dict(c) for c in data]), 200


# -----------------------------
# UPDATE CONSULTATION
# PUT /api/consultations/<id>
# -----------------------------
@consult_bp.route("/consultations/<int:id>", methods=["PUT"])
def edit_consult(id):
    _ensure_follow_up_time_column()

    c    = Consultation.query.get_or_404(id)
    raw  = request.get_json() or {}
    data = sanitise(raw)

    # Separate follow_up_time — write via SQL to guarantee persistence
    follow_up_time = data.pop("follow_up_time", None)

    valid_columns = {col.name for col in Consultation.__table__.columns}
    for k, v in data.items():
        if k in valid_columns and k != "id":
            setattr(c, k, v)

    if follow_up_time is not None:
        db.session.execute(
            text("UPDATE consultations SET follow_up_time = :t WHERE id = :id"),
            {"t": follow_up_time, "id": id}
        )

    db.session.commit()
    return jsonify({"status": "updated", "follow_up_time": follow_up_time}), 200


# -----------------------------
# DELETE CONSULTATION
# DELETE /api/consultations/<id>
# -----------------------------
@consult_bp.route("/consultations/<int:id>", methods=["DELETE"])
def delete_consult(id):
    c = Consultation.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200