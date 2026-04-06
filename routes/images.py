from flask import Blueprint, request, jsonify, send_from_directory, Response
import os
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

from database import db
from models import Image

images_bp = Blueprint("images", __name__)

ALLOWED_TYPES = ["IOPA", "OPG", "CBCT", "INTRAORAL"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_image_migrations(app):
    with app.app_context():
        from sqlalchemy import text, inspect
        conn = db.engine.connect()
        try:
            insp = inspect(db.engine)
            cols = {c["name"]: c for c in insp.get_columns("images")}

            if "image_type" in cols:
                col_type = str(cols["image_type"]["type"]).upper()
                if "ENUM" in col_type and "postgresql" in str(db.engine.url):
                    try:
                        conn.execute(text("ALTER TABLE images ALTER COLUMN image_type TYPE VARCHAR(30)"))
                        conn.commit()
                        print("[images migration] image_type -> VARCHAR(30)")
                    except Exception as e:
                        print(f"[images migration] image_type skipped: {e}")

            if "image_date" not in cols:
                try:
                    conn.execute(text("ALTER TABLE images ADD COLUMN image_date DATE"))
                    conn.commit()
                    print("[images migration] Added image_date")
                except Exception as e:
                    print(f"[images migration] image_date skipped: {e}")

            if "image_data" not in cols:
                try:
                    conn.execute(text("ALTER TABLE images ADD COLUMN image_data TEXT"))
                    conn.commit()
                    print("[images migration] Added image_data (base64 storage)")
                except Exception as e:
                    print(f"[images migration] image_data skipped: {e}")

            if "mime_type" not in cols:
                try:
                    conn.execute(text("ALTER TABLE images ADD COLUMN mime_type VARCHAR(50)"))
                    conn.commit()
                    print("[images migration] Added mime_type")
                except Exception as e:
                    print(f"[images migration] mime_type skipped: {e}")

        finally:
            conn.close()


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

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use JPG, PNG, WEBP, or PDF"}), 400

    # Read and encode as base64 — stored in DB, persists across Render deploys
    file_bytes = file.read()
    b64_data   = base64.b64encode(file_bytes).decode("utf-8")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png",  "webp": "image/webp",
        "gif": "image/gif",  "bmp": "image/bmp",
        "pdf": "application/pdf",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    parsed_date = datetime.utcnow().date()
    if image_date:
        try:
            parsed_date = datetime.strptime(image_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    filename = secure_filename(file.filename)
    record = Image(
        visit_id    = visit_id,
        image_path  = filename,
        image_type  = image_type,
        description = description,
        uploaded_by = uploaded_by,
        image_date  = parsed_date,
    )
    record.image_data = b64_data
    record.mime_type  = mime_type

    db.session.add(record)
    db.session.commit()
    return jsonify(_serialize(record)), 201


@images_bp.route("/visits/<int:visit_id>/images", methods=["GET"])
def list_images(visit_id):
    images = Image.query.filter_by(visit_id=visit_id).order_by(
        Image.image_date.desc().nullslast(),
        Image.uploaded_at.desc()
    ).all()
    return jsonify([_serialize(img) for img in images])


@images_bp.route("/images/<int:id>/data", methods=["GET"])
def serve_image_data(id):
    img  = Image.query.get_or_404(id)
    b64  = getattr(img, "image_data", None)
    mime = getattr(img, "mime_type", "image/jpeg") or "image/jpeg"

    if b64:
        return Response(base64.b64decode(b64), mimetype=mime)

    # Fallback: old disk-based images
    FLASK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if img.image_path and os.path.exists(os.path.join(FLASK_ROOT, img.image_path)):
        full_path = os.path.join(FLASK_ROOT, img.image_path)
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))

    return jsonify({"error": "Image not found"}), 404


FLASK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@images_bp.route("/images/file/<path:filepath>", methods=["GET"])
def serve_image(filepath):
    full_path = os.path.join(FLASK_ROOT, filepath)
    return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))


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


@images_bp.route("/images/<int:id>", methods=["DELETE"])
def delete_image(id):
    image = Image.query.get_or_404(id)
    db.session.delete(image)
    db.session.commit()
    return jsonify({"status": "deleted"})


def _serialize(img):
    mime = getattr(img, "mime_type", "image/jpeg") or "image/jpeg"
    url  = f"/api/images/{img.id}/data"
    return {
        "id":          img.id,
        "visit_id":    img.visit_id,
        "type":        img.image_type,
        "path":        img.image_path,
        "url":         url,
        "mime_type":   mime,
        "description": img.description,
        "uploaded_by": img.uploaded_by,
        "image_date":  img.image_date.strftime("%Y-%m-%d") if getattr(img, "image_date", None) else None,
        "uploaded_at": img.uploaded_at.strftime("%d-%b-%Y %H:%M") if getattr(img, "uploaded_at", None) else None,
    }