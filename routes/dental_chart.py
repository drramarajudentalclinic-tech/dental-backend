from flask import Blueprint, request, jsonify
from database import db
from models import DentalChart

dental_bp = Blueprint("dental", __name__)


# -----------------------------
# ADD OR UPDATE DENTAL FINDING  (upsert — no more 409)
# POST /api/visits/<visit_id>/dental-chart
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart", methods=["POST"])
def add_dental(visit_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    tooth_number = data.get("tooth_number")
    condition    = data.get("condition")

    if not tooth_number or not condition:
        return jsonify({"error": "tooth_number and condition are required"}), 400

    # ── Upsert: update if tooth already exists for this visit ──
    entry = DentalChart.query.filter_by(
        visit_id=visit_id,
        tooth_number=tooth_number
    ).first()

    if entry:
        # Update existing record instead of rejecting
        entry.condition    = condition
        entry.severity     = data.get("severity",     entry.severity)
        entry.surface      = data.get("surface",      entry.surface)
        entry.notes        = data.get("notes",        entry.notes)
        entry.other_text   = data.get("other_text",   entry.other_text)
        entry.custom_color = data.get("custom_color", entry.custom_color)
        db.session.commit()
        return jsonify(_serialize(entry)), 200
    else:
        # Insert new record
        entry = DentalChart(
            visit_id     = visit_id,
            tooth_number = tooth_number,
            condition    = condition,
            severity     = data.get("severity"),
            surface      = data.get("surface"),
            notes        = data.get("notes"),
            other_text   = data.get("other_text"),
            custom_color = data.get("custom_color"),
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify(_serialize(entry)), 201


# -----------------------------
# LIST FULL DENTAL CHART FOR A VISIT
# GET /api/visits/<visit_id>/dental-chart
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart", methods=["GET"])
def list_dental(visit_id):
    entries = DentalChart.query.filter_by(visit_id=visit_id).all()
    return jsonify([_serialize(e) for e in entries])


# -----------------------------
# UPDATE SINGLE TOOTH ENTRY
# PUT /api/visits/<visit_id>/dental-chart/<id>
# -----------------------------
@dental_bp.route("/visits/<int:visit_id>/dental-chart/<int:id>", methods=["PUT"])
def edit_dental(visit_id, id):
    entry = DentalChart.query.filter_by(id=id, visit_id=visit_id).first_or_404()
    data  = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    allowed_fields = [
        "tooth_number", "condition", "severity",
        "surface", "notes", "other_text", "custom_color",
    ]
    for field in allowed_fields:
        if field in data:
            setattr(entry, field, data[field])

    db.session.commit()
    return jsonify(_serialize(entry))


# -----------------------------
# DELETE SINGLE TOOTH ENTRY
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
def _serialize(e):
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
    }