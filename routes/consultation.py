from flask import Blueprint, request, jsonify
from database import db
from models import Consultation
from datetime import datetime
from sqlalchemy import text, inspect

consult_bp = Blueprint("consult", __name__)

# ══════════════════════════════════════════════════════════════
#  CONSULTATIONS
#
#  consultation_date = the date the doctor chose for this consultation
#  (today by default). It is shown in the consultation history instead
#  of the day the record happened to be saved. Records saved before this
#  change have no consultation_date and keep showing their saved day.
#
#  The extra columns (follow_up_time, consultation_date) are added to the
#  consultations table automatically, once per server start.
# ══════════════════════════════════════════════════════════════

EXTRA_COLUMNS = {"follow_up_time": "TEXT", "consultation_date": "DATE"}
_columns = {"checked": False, "present": set()}


def _ensure_columns():
    """Adds follow_up_time / consultation_date if the table lacks them.
    Runs once per server start; safe to call on every request."""
    if _columns["checked"]:
        return _columns["present"]
    present = set()
    try:
        cols = {c["name"] for c in inspect(db.engine).get_columns("consultations")}
        for name, kind in EXTRA_COLUMNS.items():
            if name in cols:
                present.add(name)
                continue
            try:
                with db.engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE consultations ADD COLUMN {name} {kind}"))
                present.add(name)
                print(f"[consultations] Added {name} column")
            except Exception as exc:
                print(f"[consultations] could not add {name}: {type(exc).__name__}")
    except Exception as exc:
        print(f"[consultations] could not inspect table: {type(exc).__name__}")
    _columns["present"] = present
    _columns["checked"] = True
    return present


# Kept for any other module that imports it.
def _ensure_follow_up_time_column():
    _ensure_columns()


# ─── helper: safely parse a date string → date object or None ───────────────
def parse_date(value):
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None


# ─── helper: sanitise incoming JSON before passing to the model ─────────────
def sanitise(data: dict) -> dict:
    """
    Convert any date-like keys from empty string / raw string
    to a proper Python date object (or None) so the database doesn't crash.
    follow_up_time is a plain TIME string (e.g. "11:00") — do NOT parse as date.
    """
    DATE_FIELDS = {"follow_up_date", "date", "created_at", "consultation_date"}
    TIME_FIELDS = {"follow_up_time"}
    clean = {}
    for k, v in data.items():
        if k in DATE_FIELDS:
            clean[k] = parse_date(v)
        elif k in TIME_FIELDS:
            clean[k] = str(v).strip() if v and str(v).strip() else None
        else:
            clean[k] = v
    return clean


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def _extras_for(ids):
    """{id: {"follow_up_time": ..., "consultation_date": ...}} read straight
    from the table (these columns may not be in the model)."""
    present = _ensure_columns()
    names = [n for n in EXTRA_COLUMNS if n in present]
    ids = [int(i) for i in ids if i is not None]
    if not names or not ids:
        return {}
    try:
        rows = db.session.execute(text(
            f"SELECT id, {', '.join(names)} FROM consultations "
            f"WHERE id IN ({','.join(str(i) for i in ids)})"
        )).fetchall()
    except Exception:
        db.session.rollback()
        return {}
    out = {}
    for r in rows:
        out[r[0]] = {name: (_iso(r[i + 1]) if name == "consultation_date" else r[i + 1])
                     for i, name in enumerate(names)}
    return out


# ─── helper: serialise a consultation row ───────────────────────────────────
def _row_to_dict(c, extras=None) -> dict:
    row = {
        k: (v.isoformat() if hasattr(v, "isoformat") else v)
        for k, v in c.__dict__.items()
        if not k.startswith("_")
    }
    if extras is None:
        extras = _extras_for([c.id])
    for name in EXTRA_COLUMNS:
        if row.get(name) in (None, ""):
            row[name] = extras.get(c.id, {}).get(name)
    return row


def _write_extras(cid, values):
    """Writes follow_up_time / consultation_date with plain SQL in the
    current transaction. Only keys present in `values` are written."""
    present = _ensure_columns()
    for name, value in values.items():
        if name in present:
            db.session.execute(
                text(f"UPDATE consultations SET {name} = :v WHERE id = :id"),
                {"v": value, "id": cid},
            )


# -----------------------------
# ADD CONSULTATION
# POST /api/visits/<visit_id>/consultations
# -----------------------------
@consult_bp.route("/visits/<int:visit_id>/consultations", methods=["POST"])
def add_consult(visit_id):
    _ensure_columns()

    raw  = request.get_json() or {}
    data = sanitise(raw)

    # These two may not be in the model: written with SQL below
    follow_up_time    = data.pop("follow_up_time", None)
    consultation_date = data.pop("consultation_date", None)

    valid_columns = {col.name for col in Consultation.__table__.columns}
    data = {k: v for k, v in data.items() if k in valid_columns}

    c = Consultation(visit_id=visit_id, **data)
    db.session.add(c)
    db.session.flush()  # get c.id before commit

    extras = {}
    if follow_up_time:
        extras["follow_up_time"] = follow_up_time
    if consultation_date:
        extras["consultation_date"] = consultation_date
    _write_extras(c.id, extras)

    db.session.commit()

    return jsonify({
        "status": "added",
        "id": c.id,
        "follow_up_time": follow_up_time,
        "consultation_date": _iso(consultation_date),
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
    _ensure_columns()
    data = Consultation.query.filter_by(visit_id=visit_id).order_by(Consultation.id.asc()).all()
    extras = _extras_for([c.id for c in data])
    return jsonify([_row_to_dict(c, extras) for c in data]), 200


# -----------------------------
# UPDATE CONSULTATION
# PUT /api/consultations/<id>
# -----------------------------
@consult_bp.route("/consultations/<int:id>", methods=["PUT"])
def edit_consult(id):
    _ensure_columns()

    c    = Consultation.query.get_or_404(id)
    raw  = request.get_json() or {}
    data = sanitise(raw)

    follow_up_time    = data.pop("follow_up_time", None)
    has_date          = "consultation_date" in data
    consultation_date = data.pop("consultation_date", None)

    valid_columns = {col.name for col in Consultation.__table__.columns}
    for k, v in data.items():
        if k in valid_columns and k != "id":
            setattr(c, k, v)

    extras = {}
    if follow_up_time is not None:
        extras["follow_up_time"] = follow_up_time
    if has_date and consultation_date:
        extras["consultation_date"] = consultation_date
    _write_extras(id, extras)

    db.session.commit()
    return jsonify({
        "status": "updated",
        "follow_up_time": follow_up_time,
        "consultation_date": _iso(consultation_date) if has_date else None,
    }), 200


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