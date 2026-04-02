from flask import Blueprint, request, jsonify, send_from_directory
import os
from datetime import datetime
from werkzeug.utils import secure_filename

from database import db
from models import Image
from utils.folders import ensure_image_folder

images_bp = Blueprint("images", __name__)

ALLOWED_TYPES = ["IOPA", "OPG", "CBCT", "INTRAORAL"]


# ─────────────────────────────────────────────
# AUTO-MIGRATION
# Handles two cases on existing databases:
#   1. image_type was ENUM("XRAY","INTRAORAL") — convert to VARCHAR(30)
#   2. image_date column may not exist yet     — add DATE column
# Safe to call every startup; skips steps already done.
# Call this from app.py after db.init_app(app):
#     from routes.images import run_image_migrations
#     run_image_migrations(app)
# ─────────────────────────────────────────────
def run_image_migrations(app):
    with app.app_context():
        from sqlalchemy import text, inspect
        conn = db.engine.connect()
        try:
            insp = inspect(db.engine)
            cols = {c["name"]: c for c in insp.get_columns("images")}

            # Fix image_type ENUM → VARCHAR for PostgreSQL
            if "image_type" in cols:
                col_type = str(cols["image_type"]["type"]).upper()
                if "ENUM" in col_type and "postgresql" in str(db.engine.url):
                    try:
                        conn.execute(text(
                            "ALTER TABLE images ALTER COLUMN image_type TYPE VARCHAR(30)"
                        ))
                        conn.commit()
                        print("[images migration] image_type → VARCHAR(30) ✓")
                    except Exception as e:
                        print(f"[images migration] image_type alter skipped: {e}")

            # Add image_date if missing (works for SQLite + PostgreSQL)
            if "image_date" not in cols:
                try:
                    conn.execute(text("ALTER TABLE images ADD COLUMN image_date DATE"))
                    conn.commit()
                    print("[images migration] Added image_date column ✓")
                except Exception as e:
                    print(f"[images migration] image_date skipped: {e}")

        finally:
            conn.close()


# ─────────────────────────────────────────────
# UPLOAD IMAGE
# POST /api/visits/<visit_id>/images
# ─────────────────────────────────────────────
@images_bp.route("/visits/<int:visit_id>/images", methods=["POST"])
def upload_image(visit_id):
    if "image" not in request.files:
        return jsonify({"error": "Image file required"}), 400

    file        = request.files["image"]
    image_type  = request.form.get("type", "").upper()
    description = request.form.get("description", "")
    uploaded_by = request.form.get("uploaded_by", "SYSTEM")
    image_date  = request.form.get("image_date", "")

    if image_type not in ALLOWED_TYPES:
        return jsonify({"error": f"Invalid image type. Must be one of: {', '.join(ALLOWED_TYPES)}"}), 400

    folder    = ensure_image_folder(visit_id, image_type)
    filename  = secure_filename(file.filename)
    file_path = os.path.join(folder, filename)
    file.save(file_path)

    if image_date:
        try:
            parsed_date = datetime.strptime(image_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = datetime.utcnow().date()
    else:
        parsed_date = datetime.utcnow().date()

    record = Image(
        visit_id    = visit_id,
        image_path  = file_path,
        image_type  = image_type,
        description = description,
        uploaded_by = uploaded_by,
        image_date  = parsed_date,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(_serialize(record)), 201


# ─────────────────────────────────────────────
# LIST IMAGES FOR A VISIT
# GET /api/visits/<visit_id>/images
# ─────────────────────────────────────────────
@images_bp.route("/visits/<int:visit_id>/images", methods=["GET"])
def list_images(visit_id):
    images = Image.query.filter_by(visit_id=visit_id).order_by(
        Image.image_date.desc().nullslast(),
        Image.uploaded_at.desc()
    ).all()
    return jsonify([_serialize(img) for img in images])


# ─────────────────────────────────────────────
# EDIT IMAGE METADATA
# PUT /api/images/<id>
# ─────────────────────────────────────────────
@images_bp.route("/images/<int:id>", methods=["PUT"])
def edit_image(id):
    image = Image.query.get_or_404(id)
    data  = request.get_json(force=True) or {}

    if "description" in data:
        image.description = data["description"]
    if "image_date" in data and data["image_date"]:
        try:
            image.image_date = datetime.strptime(data["image_date"], "%Y-%m-%d").date()
        except ValueError:
            pass
    if "type" in data and data["type"].upper() in ALLOWED_TYPES:
        image.image_type = data["type"].upper()

    db.session.commit()
    return jsonify(_serialize(image))


# ─────────────────────────────────────────────
# DELETE IMAGE
# DELETE /api/images/<id>
# ─────────────────────────────────────────────
@images_bp.route("/images/<int:id>", methods=["DELETE"])
def delete_image(id):
    image = Image.query.get_or_404(id)
    if image.image_path and os.path.exists(image.image_path):
        os.remove(image.image_path)
    db.session.delete(image)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ─────────────────────────────────────────────
# SERVE IMAGE FILE
# GET /api/images/file/<path:filepath>
# filepath is the relative path stored in DB,
# e.g. "uploads/visits/69/intraoral/photo.jpg"
# BASE_UPLOAD_DIR lives next to app.py (Flask root)
# ─────────────────────────────────────────────
FLASK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@images_bp.route("/images/file/<path:filepath>", methods=["GET"])
def serve_image(filepath):
    # filepath arrives as "uploads/visits/69/intraoral/photo.jpg"
    full_path = os.path.join(FLASK_ROOT, filepath)
    directory = os.path.dirname(full_path)
    filename  = os.path.basename(full_path)
    return send_from_directory(directory, filename)


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def _serialize(img):
    # Build a clean URL the browser can load:
    # /api/images/file/uploads/visits/69/intraoral/photo.jpg
    if img.image_path:
        # Normalise Windows backslashes just in case
        clean_path = img.image_path.replace("\\", "/")
        url = f"/api/images/file/{clean_path}"
    else:
        url = None

    return {
        "id":          img.id,
        "visit_id":    img.visit_id,
        "type":        img.image_type,
        "path":        img.image_path,
        "url":         url,
        "description": img.description,
        "uploaded_by": img.uploaded_by,
        "image_date":  img.image_date.strftime("%Y-%m-%d") if getattr(img, "image_date", None) else None,
        "uploaded_at": img.uploaded_at.strftime("%d-%b-%Y %H:%M") if getattr(img, "uploaded_at", None) else None,
    }