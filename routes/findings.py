from flask import Blueprint, request, jsonify
from database import db
from models import OtherFinding
from datetime import datetime

findings_bp = Blueprint("findings", __name__)


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
# ADD SINGLE FINDING
# POST /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["POST"])
def add_finding(visit_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # ── Support bulk save: frontend may send a list ──────────────────────────
    if isinstance(data, list):
        created = []
        for item in data:
            finding_type = item.get("finding_type", "").strip()
            if not finding_type:
                continue                          # skip rows without a type
            entry = OtherFinding(
                visit_id=visit_id,
                finding_type=finding_type,
                value=item.get("value") or None,
                notes=item.get("notes") or None,
            )
            db.session.add(entry)
            created.append(entry)
        db.session.commit()
        return jsonify([serialize(e) for e in created]), 201

    # ── Single object ────────────────────────────────────────────────────────
    finding_type = (data.get("finding_type") or "").strip()

    # If finding_type is empty, treat the whole payload as key→value pairs
    # (some frontends send { "BP": "120/80", "Sugar": "Normal" } style)
    if not finding_type:
        entries = []
        for key, val in data.items():
            if key in ("visit_id",):
                continue
            entry = OtherFinding(
                visit_id=visit_id,
                finding_type=key,
                value=str(val) if val not in (None, "") else None,
                notes=None,
            )
            db.session.add(entry)
            entries.append(entry)

        if not entries:
            return jsonify({"error": "No valid finding data provided"}), 400

        db.session.commit()
        return jsonify([serialize(e) for e in entries]), 201

    entry = OtherFinding(
        visit_id=visit_id,
        finding_type=finding_type,
        value=data.get("value") or None,
        notes=data.get("notes") or None,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(serialize(entry)), 201


# -----------------------------------------------------------------------------
# BULK REPLACE ALL FINDINGS FOR A VISIT
# PUT /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["PUT"])
def replace_findings(visit_id):
    """
    Replaces all findings for a visit in one shot.
    Accepts either a list:  [ { finding_type, value, notes }, ... ]
    or a dict:              { "BP": "120/80", "Sugar": "Normal" }
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "No data provided"}), 400

    # Delete existing findings for this visit
    OtherFinding.query.filter_by(visit_id=visit_id).delete()

    created = []

    if isinstance(data, list):
        for item in data:
            finding_type = (item.get("finding_type") or "").strip()
            if not finding_type:
                continue
            entry = OtherFinding(
                visit_id=visit_id,
                finding_type=finding_type,
                value=item.get("value") or None,
                notes=item.get("notes") or None,
            )
            db.session.add(entry)
            created.append(entry)

    elif isinstance(data, dict):
        for key, val in data.items():
            if key in ("visit_id",):
                continue
            entry = OtherFinding(
                visit_id=visit_id,
                finding_type=key,
                value=str(val) if val not in (None, "") else None,
                notes=None,
            )
            db.session.add(entry)
            created.append(entry)

    db.session.commit()
    return jsonify([serialize(e) for e in created]), 200


# -----------------------------------------------------------------------------
# LIST ALL FINDINGS FOR A VISIT
# GET /api/visits/<visit_id>/findings
# -----------------------------------------------------------------------------
@findings_bp.route("/visits/<int:visit_id>/findings", methods=["GET"])
def list_findings(visit_id):
    findings = OtherFinding.query.filter_by(visit_id=visit_id).all()
    return jsonify([serialize(f) for f in findings]), 200


# -----------------------------------------------------------------------------
# UPDATE SINGLE FINDING
# PUT /api/findings/<id>
# -----------------------------------------------------------------------------
@findings_bp.route("/findings/<int:id>", methods=["PUT"])
def edit_finding(id):
    entry = OtherFinding.query.get_or_404(id)
    data  = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    allowed = {"finding_type", "value", "notes"}
    for field in allowed:
        if field in data:
            setattr(entry, field, data[field] or None)

    db.session.commit()
    return jsonify(serialize(entry)), 200


# -----------------------------------------------------------------------------
# DELETE SINGLE FINDING
# DELETE /api/findings/<id>
# -----------------------------------------------------------------------------
@findings_bp.route("/findings/<int:id>", methods=["DELETE"])
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
def clear_findings(visit_id):
    deleted = OtherFinding.query.filter_by(visit_id=visit_id).delete()
    db.session.commit()
    return jsonify({"status": "cleared", "deleted": deleted}), 200