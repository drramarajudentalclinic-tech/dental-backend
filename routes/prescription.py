from flask import Blueprint, request, jsonify
from database import db
from models import Prescription

presc_bp = Blueprint("prescription", __name__)


# ─────────────────────────────────────────────────────────────
# HELPER — strip keys that are not real columns on Prescription
# so we never hit TypeError on unknown fields
# ─────────────────────────────────────────────────────────────
def _safe_data(data: dict, exclude=("id", "visit_id")) -> dict:
    valid = {c.key for c in Prescription.__table__.columns} - set(exclude)
    return {k: v for k, v in data.items() if k in valid}


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
def add_prescription(visit_id):
    raw  = request.get_json() or {}
    safe = _safe_data(raw)          # strips visit_id + unknown keys
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
    rows = Prescription.query.filter_by(visit_id=visit_id).all()
    return jsonify([p.to_dict() for p in rows]), 200


# ─────────────────────────────────────────────────────────────
# UPDATE PRESCRIPTION
# PUT /api/prescriptions/<id>
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/prescriptions/<int:id>", methods=["PUT"])
def edit_prescription(id):
    p    = Prescription.query.get_or_404(id)
    safe = _safe_data(request.get_json() or {})
    for k, v in safe.items():
        setattr(p, k, v)
    db.session.commit()
    return jsonify(p.to_dict()), 200


# ─────────────────────────────────────────────────────────────
# DELETE PRESCRIPTION
# DELETE /api/prescriptions/<id>
# ─────────────────────────────────────────────────────────────
@presc_bp.route("/prescriptions/<int:id>", methods=["DELETE"])
def delete_prescription(id):
    p = Prescription.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200