from flask import Blueprint, request, jsonify
from database import db
from models import OtherFinding
from datetime import datetime
from functools import wraps
from sqlalchemy import text

findings_bp = Blueprint("findings", __name__)

# ─────────────────────────────────────────────────────────────────────────────
#  OTHER FINDINGS
#
#  One row per finding:
#      finding_type = the text of the finding   ("Gingivitis - generalised")
#      value        = the date it was noted     ("2026-10-07")
#      notes        = spare column (not used by the screens)
#
#  Every route and every response looks exactly as before. What is new:
#    * The finding text used to be limited to 100 characters by the database.
#      On PostgreSQL a longer finding failed with a server error. The column is
#      now widened once, automatically (only the size limit changes - no data is
#      touched), so long findings save normally.
#    * Empty findings are refused with a clear message instead of a server error.
#    * If the database refuses a save, the change is rolled back cleanly and a
#      readable error is returned, so the next request is not affected.
#    * Findings are always returned in the order they were added.
# ─────────────────────────────────────────────────────────────────────────────

MAX_FINDING_CHARS = 1000        # generous upper limit once the column is widened
OLD_COLUMN_LIMIT  = 100         # the original VARCHAR(100)

_column_state = {"checked": False, "limit": OLD_COLUMN_LIMIT}


class FindingError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# ─── one-time: let finding_type hold long text ───────────────────────────────
def _ensure_long_finding_text():
    """
    other_findings.finding_type was created as VARCHAR(100).
    PostgreSQL enforces that limit, so widen it to TEXT (once per server start).
    Changing VARCHAR to TEXT only removes the size limit; existing rows are untouched.
    SQLite never enforced the limit, so nothing needs doing there.
    If the change cannot be made right now (table busy), the old 100-character
    limit keeps being checked and the change is tried again on the next request.
    """
    if _column_state["checked"]:
        return
    try:
        dialect = db.engine.dialect.name
        if dialect == "sqlite":
            _column_state.update(checked=True, limit=MAX_FINDING_CHARS)
            return
        if dialect != "postgresql":
            _column_state.update(checked=True, limit=OLD_COLUMN_LIMIT)
            return
        with db.engine.begin() as conn:
            row = conn.execute(text(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'other_findings' AND column_name = 'finding_type'"
            )).fetchone()
            if row is not None and row[0] is not None:
                conn.execute(text("SET LOCAL lock_timeout = '5s'"))
                conn.execute(text("ALTER TABLE other_findings ALTER COLUMN finding_type TYPE TEXT"))
                print("[findings] other_findings.finding_type widened to TEXT (long findings now allowed)")
        _column_state.update(checked=True, limit=MAX_FINDING_CHARS)
    except Exception as exc:                       # keep serving with the old limit
        print("[findings] could not widen finding_type yet:", type(exc).__name__)


@findings_bp.before_request
def _prepare():
    _ensure_long_finding_text()


# ─── helper: safely parse date strings ──────────────────────────────────────
def parse_date(value):
    if not value or not str(value).strip():
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


# ─── helper: sanitise a dict — convert date fields, strip unknown keys ───────
def sanitise(data: dict) -> dict:
    DATE_FIELDS = {"date", "created_at", "finding_date"}
    valid_columns = {col.name for col in OtherFinding.__table__.columns}
    clean = {}
    for k, v in data.items():
        if k not in valid_columns:
            continue
        if k in DATE_FIELDS:
            clean[k] = parse_date(v)
        else:
            clean[k] = v
    return clean


# ─── helper: tidy and check the finding text ────────────────────────────────
def _finding_text(value, required=True):
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        if required:
            raise FindingError("Please enter the finding.")
        return ""
    limit = _column_state["limit"]
    if len(cleaned) > limit:
        raise FindingError(
            "This finding is too long (%d characters). Please keep it under %d characters."
            % (len(cleaned), limit)
        )
    return cleaned


def _optional(value):
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _new_entry(visit_id, finding_type, value=None, notes=None):
    return OtherFinding(
        visit_id=visit_id,
        finding_type=_finding_text(finding_type),
        value=_optional(value),
        notes=_optional(notes),
    )


# ─── helper: never leave a half-finished save behind ────────────────────────
def _guard(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FindingError as exc:
            db.session.rollback()
            return jsonify({"error": exc.message}), exc.status
        except Exception as exc:
            db.session.rollback()
            if hasattr(exc, "code") and hasattr(exc, "get_response"):
                raise                                # normal 404 etc.
            print("[findings] save failed:", type(exc).__name__, str(exc)[:300])
            return jsonify({"error": "The server could not save this. Nothing was changed - please try again."}), 500
    return wrapped


# ─── serialise a single OtherFinding row ────────────────────────────────────
def serialize(f):
    return {
        "id":           f.id,
        "visit_id":     f.visit_id,
        "finding_type": f.finding_type,
        "value":        f.value,
        "notes":        f.notes,
    }


# -----------------------------------------------------------------------------
# ADD FINDING(S)
# POST /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["POST"])
@_guard
def add_finding(visit_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # ── Support bulk save: frontend may send a list ──────────────────────────
    if isinstance(data, list):
        created = []
        for item in data:
            if not isinstance(item, dict):
                continue
            finding_type = (item.get("finding_type") or "")
            if not str(finding_type).strip():
                continue                          # skip rows without a type
            entry = _new_entry(visit_id, finding_type, item.get("value"), item.get("notes"))
            db.session.add(entry)
            created.append(entry)
        if not created:
            return jsonify({"error": "Please enter the finding."}), 400
        db.session.commit()
        return jsonify([serialize(e) for e in created]), 201

    if not isinstance(data, dict):
        return jsonify({"error": "No valid finding data provided"}), 400

    # ── Single object ────────────────────────────────────────────────────────
    finding_type = str(data.get("finding_type") or "").strip()

    # If finding_type is empty, treat the whole payload as key→value pairs
    # (some frontends send { "BP": "120/80", "Sugar": "Normal" } style)
    if not finding_type:
        entries = []
        for key, val in data.items():
            if key in ("visit_id", "finding_type", "value", "notes"):
                continue
            entry = _new_entry(visit_id, key, str(val) if val not in (None, "") else None)
            db.session.add(entry)
            entries.append(entry)

        if not entries:
            return jsonify({"error": "No valid finding data provided"}), 400

        db.session.commit()
        return jsonify([serialize(e) for e in entries]), 201

    entry = _new_entry(visit_id, finding_type, data.get("value"), data.get("notes"))
    db.session.add(entry)
    db.session.commit()
    return jsonify(serialize(entry)), 201


# -----------------------------------------------------------------------------
# BULK REPLACE ALL FINDINGS FOR A VISIT
# PUT /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["PUT"])
@_guard
def replace_findings(visit_id):
    """
    Replaces all findings for a visit in one shot.
    Accepts either a list:  [ { finding_type, value, notes }, ... ]
    or a dict:              { "BP": "120/80", "Sugar": "Normal" }
    Everything is checked first: if any row is not acceptable nothing is
    deleted and nothing is saved.
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "No data provided"}), 400

    created = []

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            finding_type = (item.get("finding_type") or "")
            if not str(finding_type).strip():
                continue
            created.append(_new_entry(visit_id, finding_type, item.get("value"), item.get("notes")))

    elif isinstance(data, dict):
        for key, val in data.items():
            if key in ("visit_id",):
                continue
            created.append(_new_entry(visit_id, key, str(val) if val not in (None, "") else None))

    else:
        return jsonify({"error": "No valid finding data provided"}), 400

    # Delete existing findings for this visit, then add the new set
    OtherFinding.query.filter_by(visit_id=visit_id).delete()
    for entry in created:
        db.session.add(entry)

    db.session.commit()
    return jsonify([serialize(e) for e in created]), 200


# -----------------------------------------------------------------------------
# LIST ALL FINDINGS FOR A VISIT
# GET /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["GET"])
def list_findings(visit_id):
    findings = (OtherFinding.query
                .filter_by(visit_id=visit_id)
                .order_by(OtherFinding.id)
                .all())
    return jsonify([serialize(f) for f in findings]), 200


# -----------------------------------------------------------------------------
# UPDATE SINGLE FINDING
# PUT /api/findings/<id>
# -----------------------------------------------------------------------------
@findings_bp.route("/findings/<int:id>", methods=["PUT"])
@_guard
def edit_finding(id):
    entry = OtherFinding.query.get_or_404(id)
    data  = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "No data provided"}), 400

    if "finding_type" in data:
        entry.finding_type = _finding_text(data["finding_type"])   # may not be emptied
    if "value" in data:
        entry.value = _optional(data["value"])
    if "notes" in data:
        entry.notes = _optional(data["notes"])

    db.session.commit()
    return jsonify(serialize(entry)), 200


# -----------------------------------------------------------------------------
# DELETE SINGLE FINDING
# DELETE /api/findings/<id>
# -----------------------------------------------------------------------------
@findings_bp.route("/findings/<int:id>", methods=["DELETE"])
@_guard
def delete_finding(id):
    entry = OtherFinding.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"status": "deleted", "id": id}), 200


# -----------------------------------------------------------------------------
# DELETE ALL FINDINGS FOR A VISIT
# DELETE /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["DELETE"])
@_guard
def clear_findings(visit_id):
    deleted = OtherFinding.query.filter_by(visit_id=visit_id).delete()
    db.session.commit()
    return jsonify({"status": "cleared", "deleted": deleted}), 200