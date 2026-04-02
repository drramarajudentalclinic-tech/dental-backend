from flask import Blueprint, request, jsonify
from database import db
from models import Consent
from datetime import datetime

consent_bp = Blueprint("consent", __name__)

@consent_bp.route("/consent/<int:patient_id>", methods=["GET", "PUT", "OPTIONS"])
def save_consent(patient_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json() or {}

    consent = Consent.query.filter_by(patient_id=patient_id).first()
    if not consent:
        consent = Consent(patient_id=patient_id)
        db.session.add(consent)

    consent.agreed       = bool(data.get("agreed", False))
    consent.signature    = data.get("signature")    or None
    consent.relationship = data.get("relationship") or None

    # Parse date safely
    raw_date = data.get("consent_date")
    if raw_date:
        try:
            consent.consent_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            consent.consent_date = None
    else:
        consent.consent_date = None

    db.session.commit()
    return jsonify({"patient_id": patient_id, "status": "consent saved"}), 200