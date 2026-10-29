from datetime import date, datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, request, jsonify
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError

from database import db
from models import DentalChart, Visit

dental_bp = Blueprint("dental", __name__)

# ══════════════════════════════════════════════════════════════
#  DENTAL CHART
#
#  A tooth can carry SEVERAL findings in the same visit, for example
#  tooth 16 with Caries + Calculus + Stains. Each finding is its own
#  row with its own id:
#
#    POST   /api/visits/<visit_id>/dental-chart         add a finding
#    GET    /api/visits/<visit_id>/dental-chart         all findings of the visit
#    PUT    /api/visits/<visit_id>/dental-chart/<id>    change one finding
#    DELETE /api/visits/<visit_id>/dental-chart/<id>    remove one finding
#
#  POST rule:
#    * same tooth + SAME condition      -> that finding is updated
#                                          (no duplicates of one condition)
#    * same tooth + DIFFERENT condition -> a new finding is added; the
#                                          existing ones are left alone
#
#  Before this change POST replaced whatever was on the tooth, so
#  recording Calculus on a tooth silently wiped its Caries entry.
#
#  The response format is unchanged, so every screen that already reads
#  the chart (visit page, diagnosis panel, patient history) keeps working.
#
#  CHART DATE
#    Every finding has a date (chart_date). The chart fills in today's
#    date; the doctor can pick any other day. When nothing is sent (for
#    example from the Diagnosis panel) today's date in India is used.
#    Findings saved before this change show the day they were recorded.
#    The chart_date column is added to the table automatically the first
#    time the dental chart is used - nothing has to be done by hand.
# ══════════════════════════════════════════════════════════════

SEVERITIES = ("mild", "moderate", "severe", "critical")
SURFACE_ORDER = "MOIDBL"          # Mesial, Occlusal, Incisal, Distal, Buccal, Lingual
MAX_LEN = {"tooth_number": 10, "condition": 100, "severity": 20,
           "other_text": 200, "custom_color": 20, "surface": 50}


IST = timezone(timedelta(hours=5, minutes=30))     # India time, for "today"


def _today():
    return datetime.now(IST).date()


# ── chart_date column: added once, automatically ─────────────────
_date_column = {"checked": False, "ok": False}


def _table():
    return DentalChart.__table__.name


def _ensure_date_column():
    """Adds the chart_date column if the table does not have it yet.
    Runs once per server start; if it cannot be added, the chart keeps
    working exactly as before, just without chosen dates."""
    if _date_column["checked"]:
        return _date_column["ok"]
    try:
        cols = {c["name"] for c in inspect(db.engine).get_columns(_table())}
        if "chart_date" not in cols:
            with db.engine.begin() as conn:
                if db.engine.dialect.name == "postgresql":
                    conn.execute(text("SET LOCAL lock_timeout = '10s'"))
                conn.execute(text(f"ALTER TABLE {_table()} ADD COLUMN chart_date DATE"))
            print("[dental chart] Added chart_date column")
        _date_column["ok"] = True
    except Exception as exc:
        print(f"[dental chart] chart_date column not available: {type(exc).__name__}")
        _date_column["ok"] = False
    _date_column["checked"] = True
    return _date_column["ok"]


@dental_bp.before_request
def _before():
    _ensure_date_column()


def _parse_date(value):
    """'2026-10-29' (or a full ISO date-time) -> date. Empty -> None."""
    raw = _text(value)
    if not raw:
        return None
    try:
        day = date.fromisoformat(raw[:10])
    except ValueError:
        raise ChartError("The date is not valid. Please pick it again.")
    if day.year < 1900 or day > _today() + timedelta(days=366):
        raise ChartError("The date is not valid. Please pick it again.")
    return day


def _set_date(entry_id, day):
    if _date_column["ok"] and day is not None:
        db.session.execute(text(f"UPDATE {_table()} SET chart_date = :d WHERE id = :i"),
                           {"d": day, "i": entry_id})


def _dates_for(ids):
    """{id: 'YYYY-MM-DD'} for the given findings."""
    ids = [i for i in ids if i is not None]
    if not ids or not _date_column["ok"]:
        return {}
    try:
        rows = db.session.execute(
            text(f"SELECT id, chart_date FROM {_table()} WHERE id IN ({','.join(str(int(i)) for i in ids)})")
        ).fetchall()
    except Exception:
        db.session.rollback()
        return {}
    return {r[0]: (r[1].isoformat() if hasattr(r[1], "isoformat") else (str(r[1]) if r[1] else None)) for r in rows}


class ChartError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _text(value):
    return "" if value is None else str(value).strip()


def _clean_surface(value):
    """"m, o,D" / "MOD" / ["M","O"]  ->  "M,O,D" (fixed order, no repeats).
    Anything that is not made of surface letters is kept as typed."""
    if isinstance(value, (list, tuple)):
        value = ",".join(str(v) for v in value)
    raw = _text(value)
    if not raw:
        return ""
    letters = [c for c in raw.upper() if c.isalpha()]
    if letters and all(c in SURFACE_ORDER for c in letters):
        return ",".join(c for c in SURFACE_ORDER if c in letters)
    return raw


def _clean(data, partial=False):
    """Validated field values. With partial=True only the fields that were
    actually sent are returned, so an update never blanks anything else."""
    out = {}

    def take(name):
        return name in data if partial else True

    if take("tooth_number"):
        tooth = _text(data.get("tooth_number"))
        if not tooth:
            raise ChartError("tooth_number is required")
        out["tooth_number"] = tooth

    if take("condition"):
        condition = _text(data.get("condition"))
        if not condition:
            raise ChartError("condition is required")
        out["condition"] = condition

    if take("severity"):
        severity = _text(data.get("severity"))
        out["severity"] = severity.lower() if severity.lower() in SEVERITIES else severity

    if take("surface"):
        out["surface"] = _clean_surface(data.get("surface"))

    if take("notes"):
        out["notes"] = _text(data.get("notes"))

    if take("other_text"):
        out["other_text"] = _text(data.get("other_text"))

    if take("custom_color"):
        out["custom_color"] = _text(data.get("custom_color"))

    for name, limit in MAX_LEN.items():
        if name in out and len(out[name]) > limit:
            raise ChartError(f"{name} is too long (maximum {limit} characters)")
    return out


def _same_finding(visit_id, tooth_number, condition, other_text, exclude_id=None):
    """The finding on this tooth that has the same condition, if any.
    For "Other" the typed description is part of what makes it the same."""
    query = DentalChart.query.filter(
        DentalChart.visit_id == visit_id,
        DentalChart.tooth_number == tooth_number,
        func.lower(DentalChart.condition) == condition.lower(),
    )
    if exclude_id is not None:
        query = query.filter(DentalChart.id != exclude_id)
    for entry in query.order_by(DentalChart.id.asc()).all():
        if condition.lower() != "other":
            return entry
        if _text(entry.other_text).lower() == _text(other_text).lower():
            return entry
    return None


def _guard(fn):
    """ChartError -> clean JSON error; database errors -> rollback."""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ChartError as err:
            db.session.rollback()
            return jsonify({"error": err.message}), err.status
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "The database refused this dental chart entry."}), 409

    return wrapped


# -----------------------------
# ADD A FINDING
# POST /api/visits/<visit_id>/dental-chart
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart", methods=["POST"])
@_guard
def add_dental(visit_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400
    if db.session.get(Visit, visit_id) is None:
        return jsonify({"error": "Visit not found"}), 404

    if not _text(data.get("tooth_number")) or not _text(data.get("condition")):
        return jsonify({"error": "tooth_number and condition are required"}), 400

    fields = _clean(data)
    chosen = _parse_date(data.get("chart_date"))

    # Same tooth + same condition: update that finding (only what was sent).
    entry = _same_finding(visit_id, fields["tooth_number"], fields["condition"], fields["other_text"])
    if entry:
        sent = _clean(data, partial=True)
        for name, value in sent.items():
            if name not in ("tooth_number", "condition"):
                setattr(entry, name, value or None)
        _set_date(entry.id, chosen)
        db.session.commit()
        return jsonify(_serialize(entry)), 200

    # Otherwise this is a NEW finding. Whatever else is recorded on the
    # tooth stays exactly as it is.
    entry = DentalChart(
        visit_id=visit_id,
        tooth_number=fields["tooth_number"],
        condition=fields["condition"],
        **{k: (v or None) for k, v in fields.items() if k not in ("tooth_number", "condition")},
    )
    db.session.add(entry)
    db.session.flush()                              # gives the new finding its id
    _set_date(entry.id, chosen or _today())
    db.session.commit()
    return jsonify(_serialize(entry)), 201


# -----------------------------
# LIST FULL DENTAL CHART FOR A VISIT
# GET /api/visits/<visit_id>/dental-chart
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart", methods=["GET"])
def list_dental(visit_id):
    entries = (DentalChart.query
               .filter_by(visit_id=visit_id)
               .order_by(DentalChart.id.asc())
               .all())
    dates = _dates_for([e.id for e in entries])
    return jsonify([_serialize(e, dates) for e in entries])


# -----------------------------
# UPDATE ONE FINDING
# PUT /api/visits/<visit_id>/dental-chart/<id>
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart/<int:id>", methods=["PUT"])
@_guard
def edit_dental(visit_id, id):
    entry = DentalChart.query.filter_by(id=id, visit_id=visit_id).first_or_404()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400

    fields = _clean(data, partial=True)
    chosen = _parse_date(data.get("chart_date")) if "chart_date" in data else None

    # Changing the tooth or the condition must not create a second copy of
    # a finding that is already on that tooth.
    tooth = fields.get("tooth_number", entry.tooth_number)
    condition = fields.get("condition", entry.condition)
    other_text = fields.get("other_text", entry.other_text)
    if _same_finding(visit_id, tooth, condition, other_text, exclude_id=entry.id):
        label = other_text if condition.lower() == "other" and other_text else condition
        raise ChartError(f"Tooth {tooth} already has \"{label}\" recorded. Edit that entry instead.", 409)

    for name, value in fields.items():
        setattr(entry, name, value if name in ("tooth_number", "condition") else (value or None))

    _set_date(entry.id, chosen)
    db.session.commit()
    return jsonify(_serialize(entry))


# -----------------------------
# DELETE ONE FINDING
# DELETE /api/visits/<visit_id>/dental-chart/<id>
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart/<int:id>", methods=["DELETE"])
def delete_dental(visit_id, id):
    entry = DentalChart.query.filter_by(id=id, visit_id=visit_id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"status": "deleted", "id": id})


# -----------------------------
# HELPER
# -----------------------------
def _serialize(e, dates=None):
    if dates is None:
        dates = _dates_for([e.id])
    created = e.created_at
    return {
        "id":           e.id,
        "visit_id":     e.visit_id,
        "tooth_number": e.tooth_number,
        "condition":    e.condition,
        "severity":     getattr(e, "severity",     None),
        "surface":      e.surface,
        "notes":        e.notes,
        "other_text":   getattr(e, "other_text",   None),
        "custom_color": getattr(e, "custom_color", None),
        "created_at":   e.created_at.isoformat() if e.created_at else None,
        "updated_at":   e.updated_at.isoformat() if getattr(e, "updated_at", None) else None,
        # chosen date; older findings fall back to the day they were recorded
        "chart_date":   dates.get(e.id) or (created.date().isoformat() if created else None),
    }