from flask import Blueprint, request, jsonify
from database import db
from models import Consent, Patient
from datetime import datetime

consent_bp = Blueprint("consent", __name__)


@consent_bp.route("/consent/<int:patient_id>", methods=["GET", "PUT", "OPTIONS"])
def save_consent(patient_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    Patient.query.get_or_404(patient_id)
    consent = Consent.query.filter_by(patient_id=patient_id).first()

    # ── GET: return the current record, never write anything ──
    # NOTE: previously there was no method branch at all — a GET request
    # fell through to the same code as PUT, which read an empty request
    # body and used it to overwrite every field (agreed=False,
    # signature=None, relationship=None, consent_date=None), then
    # committed that wipe to the database. Simply viewing consent status
    # was silently erasing it.
    if request.method == "GET":
        if not consent:
            return jsonify({
                "agreed": False, "signature": "", "relationship": "",
                "consent_date": "",
            }), 200
        return jsonify({
            "agreed":       bool(consent.agreed),
            "signature":    consent.signature or "",
            "relationship": consent.relationship or "",
            "consent_date": consent.consent_date.isoformat() if consent.consent_date else "",
        }), 200

    # ── PUT: save ──
    data = request.get_json() or {}

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