from flask import Blueprint, request, jsonify
from functools import wraps
import json

from werkzeug.exceptions import HTTPException

from datetime import datetime

from database import db
from models import Prescription

try:
    from auth_utils import require_login
except ImportError:                      # the app keeps it in routes/
    try:
        from routes.auth_utils import require_login
    except ImportError:                  # pragma: no cover
        def require_login(fn):
            return fn

try:                                    # used to find every prescription of the same patient
    from models import Visit
except Exception:                       # pragma: no cover
    Visit = None

presc_bp = Blueprint("prescription", __name__)

# ─────────────────────────────────────────────────────────────
#  PRESCRIPTIONS
#
#  Every address that existed before still exists and answers in the
#  same shape. What is new:
#    * GET /api/visits/<visit_id>/prescriptions/history
#        every prescription of the SAME PATIENT (all visits), newest first.
#        The screen used to download every prescription of the whole
#        clinic and pick this patient's by name - slow, and it showed
#        nothing until the current visit had a prescription of its own.
#    * "medicines" is checked before saving: it must be a list of
#      medicines (sent as JSON text, as before, or as a plain list).
#      A medicine keeps  name / times / days  exactly as before and may
#      also carry  when  ("After food" ...) and  note  (instructions).
#    * A prescription needs a patient name.
#    * If the database refuses a save, the change is rolled back cleanly
#      and a readable message is returned.
#    * The doctor's name is recorded from the login, when available.
#    * MY MEDICINES — the clinic's own medicine list (table
#      prescription_medicines): medicines that are not in the built-in list,
#      saved once with their usual frequency / when / days / instructions,
#      and offered on every prescription after that.
#        GET    /api/prescription-medicines         the saved medicines + how often
#                                                   each medicine has been prescribed
#        POST   /api/prescription-medicines         add   {name, category, times, when, days, note}
#        PUT    /api/prescription-medicines/<id>    change
#        DELETE /api/prescription-medicines/<id>    remove from the list (prescriptions
#                                                   already written keep the medicine)
# ─────────────────────────────────────────────────────────────


class PrescriptionError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _guard(fn):
    """Readable JSON errors, and never a half-finished database change."""
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PrescriptionError as exc:
            db.session.rollback()
            return jsonify({"error": exc.message}), exc.status
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, HTTPException):
                message = "This prescription no longer exists." if exc.code == 404 else (exc.description or "Request failed")
                return jsonify({"error": message}), exc.code or 500
            print("[prescription] request failed:", type(exc).__name__, str(exc)[:300])
            return jsonify({"error": "The server could not save this. Nothing was changed - please try again."}), 500
    return wrapped


def _doctor_name():
    """Name of the signed-in person, when the login system can tell us. Never blocks a save."""
    try:
        try:
            from medical_history import current_actor
        except ImportError:
            from routes.medical_history import current_actor
        name = (current_actor() or {}).get("name")
        return str(name).strip() if name else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# HELPER — medicines: always stored as JSON text holding a list
# ─────────────────────────────────────────────────────────────
def _clean_medicines(value):
    """
    Accepts JSON text (what the screens send) or a plain list.
    Returns JSON text. Keeps every key of every medicine, so nothing a
    screen sends is lost; only tidies name / times and drops unnamed rows.
    """
    if value is None or value == "":
        return "[]"
    items = value
    if isinstance(value, str):
        try:
            items = json.loads(value)
        except ValueError:
            raise PrescriptionError("The list of medicines could not be read. Please re-enter the medicines.")
    if not isinstance(items, list):
        raise PrescriptionError("The list of medicines could not be read. Please re-enter the medicines.")

    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        med = dict(item)
        med["name"] = name[:200]
        for key in ("times", "when", "note"):
            if key in med and med[key] is not None:
                med[key] = str(med[key]).strip()[:300]
        cleaned.append(med)
    return json.dumps(cleaned)


# ─────────────────────────────────────────────────────────────
# HELPER — strip keys that are not real columns on Prescription
# so we never hit TypeError on unknown fields
# ─────────────────────────────────────────────────────────────
def _safe_data(data: dict, exclude=("id", "visit_id", "created_at")) -> dict:
    # The frontend (Reception + Doctor) sends "treatment_done", but the
    # actual column on the Prescription table is "treatment_done_today".
    # Without this alias, _safe_data silently drops "treatment_done" on
    # every create/update since it isn't a recognized column name, so
    # reception's edits never reach the database.
    if "treatment_done" in data and "treatment_done_today" not in data:
        data = {**data, "treatment_done_today": data["treatment_done"]}

    valid = {c.key for c in Prescription.__table__.columns} - set(exclude)
    safe = {k: v for k, v in data.items() if k in valid}

    if "medicines" in safe:
        safe["medicines"] = _clean_medicines(safe["medicines"])
    if "patient_name" in safe:
        safe["patient_name"] = str(safe["patient_name"] or "").strip()
        if not safe["patient_name"]:
            raise PrescriptionError("Please enter the patient's name.")

    # Short text columns: refuse politely instead of failing inside the database.
    for col in Prescription.__table__.columns:
        length = getattr(col.type, "length", None)
        value = safe.get(col.key)
        if length and isinstance(value, str) and len(value) > length:
            raise PrescriptionError("'%s' is too long (%d characters; the limit is %d)."
                                    % (col.key.replace("_", " "), len(value), length))
        if length and value is not None and not isinstance(value, str):
            safe[col.key] = str(value)          # e.g. age sent as a number
    return safe


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PrescriptionError("No data provided")
    return data


# ─────────────────────────────────────────────────────────────
# LIST ALL PRESCRIPTIONS  (reception dashboard)
# GET /api/prescriptions
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/prescriptions", methods=["GET"])
def list_all_prescriptions():
    rows = Prescription.query.order_by(Prescription.id.desc()).all()
    return jsonify([p.to_dict() for p in rows]), 200


# ─────────────────────────────────────────────────────────────
# ADD PRESCRIPTION
# POST /api/visits/<visit_id>/prescriptions
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/visits/<int:visit_id>/prescriptions", methods=["POST"])
@_guard
def add_prescription(visit_id):
    raw  = _json_body()
    safe = _safe_data(raw)          # strips visit_id + unknown keys

    if Visit is not None and db.session.get(Visit, visit_id) is None:
        raise PrescriptionError("This visit no longer exists.", 404)
    if not (safe.get("patient_name") or "").strip():
        raise PrescriptionError("Please enter the patient's name.")
    if "doctor" in {c.key for c in Prescription.__table__.columns} and not safe.get("doctor"):
        name = _doctor_name()
        if name:
            safe["doctor"] = name[:100]

    p    = Prescription(visit_id=visit_id, **safe)
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


# ─────────────────────────────────────────────────────────────
# LIST PRESCRIPTIONS FOR A VISIT
# GET /api/visits/<visit_id>/prescriptions
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/visits/<int:visit_id>/prescriptions", methods=["GET"])
def list_prescriptions(visit_id):
    rows = (Prescription.query.filter_by(visit_id=visit_id)
            .order_by(Prescription.id).all())
    return jsonify([p.to_dict() for p in rows]), 200


# ─────────────────────────────────────────────────────────────
# ALL PRESCRIPTIONS OF THE SAME PATIENT (every visit), newest first
# GET /api/visits/<visit_id>/prescriptions/history
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/visits/<int:visit_id>/prescriptions/history", methods=["GET"])
@_guard
def patient_prescription_history(visit_id):
    if Visit is None:
        rows = Prescription.query.filter_by(visit_id=visit_id).order_by(Prescription.id.desc()).all()
        return jsonify([p.to_dict() for p in rows]), 200

    visit = db.session.get(Visit, visit_id)
    if visit is None:
        raise PrescriptionError("This visit no longer exists.", 404)

    rows = (Prescription.query
            .join(Visit, Prescription.visit_id == Visit.id)
            .filter(Visit.patient_id == visit.patient_id)
            .order_by(Prescription.id.desc())
            .all())
    return jsonify([p.to_dict() for p in rows]), 200


# ─────────────────────────────────────────────────────────────
# UPDATE PRESCRIPTION
# PUT /api/prescriptions/<id>
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/prescriptions/<int:id>", methods=["PUT"])
@_guard
def edit_prescription(id):
    p    = Prescription.query.get_or_404(id)
    safe = _safe_data(_json_body())
    for k, v in safe.items():
        setattr(p, k, v)
    db.session.commit()
    return jsonify(p.to_dict()), 200


# ─────────────────────────────────────────────────────────────
# DELETE PRESCRIPTION
# DELETE /api/prescriptions/<id>
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/prescriptions/<int:id>", methods=["DELETE"])
@_guard
def delete_prescription(id):
    p = Prescription.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200



# ─────────────────────────────────────────────────────────────
# MY MEDICINES — the clinic's own medicine list
# ─────────────────────────────────────────────────────────────
class CustomMedicine(db.Model):
    __tablename__ = "prescription_medicines"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    category   = db.Column(db.String(60))
    times      = db.Column(db.String(60))
    when       = db.Column("when_to_take", db.String(60))
    days       = db.Column(db.Integer)
    note       = db.Column(db.String(300))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "category": self.category or "My medicines",
                "times": self.times or "", "when": self.when or "", "days": self.days if self.days is not None else "",
                "note": self.note or "", "created_by": self.created_by or ""}


_medicine_table_ready = False


def _medicine_table():
    global _medicine_table_ready
    if not _medicine_table_ready:
        CustomMedicine.__table__.create(bind=db.engine, checkfirst=True)
        _medicine_table_ready = True


def _medicine_fields(data, current=None):
    if not isinstance(data, dict):
        raise PrescriptionError("The medicine could not be read. Please try again.")
    pick = lambda key: data.get(key) if key in data else (getattr(current, key) if current is not None else None)
    name = " ".join(str(pick("name") or "").split())[:200]
    if not name:
        raise PrescriptionError("Please enter the medicine's name (with strength, e.g. Doxycycline 100mg).")
    raw_days = pick("days")
    if raw_days in (None, ""):
        days = None
    else:
        try:
            days = int(float(raw_days))
        except (TypeError, ValueError):
            raise PrescriptionError("Days must be a number.")
        if days < 0 or days > 365:
            raise PrescriptionError("Days must be between 1 and 365.")
    clean = lambda key, n: (str(pick(key) or "").strip()[:n] or None)
    return {"name": name, "category": clean("category", 60), "times": clean("times", 60),
            "when": clean("when", 60), "days": days, "note": clean("note", 300)}


def _same_name_exists(name, other_id=None):
    q = CustomMedicine.query.filter(db.func.lower(CustomMedicine.name) == name.lower())
    if other_id:
        q = q.filter(CustomMedicine.id != other_id)
    return q.first() is not None


def _usage_counts(limit=1500):
    """How often each medicine was prescribed (latest prescriptions), by lower-case name."""
    counts = {}
    for (raw,) in db.session.query(Prescription.medicines).order_by(Prescription.id.desc()).limit(limit).all():
        try:
            items = json.loads(raw or "[]")
        except (TypeError, ValueError):
            continue
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and str(item.get("name") or "").strip():
                key = str(item["name"]).strip().lower()
                counts[key] = counts.get(key, 0) + 1
    return counts


@presc_bp.route("/prescription-medicines", methods=["GET"])
@require_login
@_guard
def list_custom_medicines():
    _medicine_table()
    rows = CustomMedicine.query.order_by(db.func.lower(CustomMedicine.name)).all()
    return jsonify({"medicines": [m.to_dict() for m in rows], "usage": _usage_counts()}), 200


@presc_bp.route("/prescription-medicines", methods=["POST"])
@require_login
@_guard
def add_custom_medicine():
    _medicine_table()
    fields = _medicine_fields(_json_body())
    if _same_name_exists(fields["name"]):
        raise PrescriptionError(f"“{fields['name']}” is already in My medicines.", 409)
    m = CustomMedicine(created_by=(_doctor_name() or "")[:100] or None, **fields)
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict()), 201


@presc_bp.route("/prescription-medicines/<int:med_id>", methods=["PUT"])
@require_login
@_guard
def edit_custom_medicine(med_id):
    _medicine_table()
    m = db.session.get(CustomMedicine, med_id)
    if m is None:
        raise PrescriptionError("This medicine is no longer in the list.", 404)
    fields = _medicine_fields(_json_body(), current=m)
    if _same_name_exists(fields["name"], other_id=m.id):
        raise PrescriptionError(f"“{fields['name']}” is already in My medicines.", 409)
    for k, v in fields.items():
        setattr(m, k, v)
    m.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(m.to_dict()), 200


@presc_bp.route("/prescription-medicines/<int:med_id>", methods=["DELETE"])
@require_login
@_guard
def delete_custom_medicine(med_id):
    _medicine_table()
    m = db.session.get(CustomMedicine, med_id)
    if m is None:
        raise PrescriptionError("This medicine is no longer in the list.", 404)
    name = m.name
    db.session.delete(m)
    db.session.commit()
    return jsonify({"status": "deleted", "name": name}), 200