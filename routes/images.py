from flask import Blueprint, request, jsonify, send_from_directory, Response
import os
import base64
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from database import db
from models import Image

images_bp = Blueprint("images", __name__)

ALLOWED_TYPES = ["IOPA", "OPG", "CBCT", "INTRAORAL"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "pdf"}

# Files are stored on disk under <project_root>/uploads/images/<visit_id>/...
# NOTE: on hosts with an ephemeral filesystem (e.g. Render's default free/
# standard web service disk), anything written here is WIPED on every
# deploy/restart. If you deploy there, attach a Render "Persistent Disk"
# (or point UPLOAD_ROOT at mounted network/object storage) or images will
# disappear the next time you push code.
FLASK_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_ROOT  = os.path.join(FLASK_ROOT, "uploads", "images")

MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png",  "webp": "image/webp",
    "gif": "image/gif",  "bmp": "image/bmp",
    "pdf": "application/pdf",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _visit_upload_dir(visit_id):
    """Directory that holds all images for one visit, e.g. uploads/images/42/"""
    path = os.path.join(UPLOAD_ROOT, str(visit_id))
    os.makedirs(path, exist_ok=True)
    return path


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

            if "image_path" in cols:
                # SQLite doesn't enforce VARCHAR length, so this only matters
                # (and only runs) on Postgres/MySQL-style engines.
                if "postgresql" in str(db.engine.url):
                    try:
                        conn.execute(text("ALTER TABLE images ALTER COLUMN image_path TYPE VARCHAR(500)"))
                        conn.commit()
                        print("[images migration] image_path -> VARCHAR(500)")
                    except Exception as e:
                        print(f"[images migration] image_path widen skipped: {e}")
                elif "mysql" in str(db.engine.url):
                    try:
                        conn.execute(text("ALTER TABLE images MODIFY COLUMN image_path VARCHAR(500) NOT NULL"))
                        conn.commit()
                        print("[images migration] image_path -> VARCHAR(500)")
                    except Exception as e:
                        print(f"[images migration] image_path widen skipped: {e}")

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

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    mime_type = MIME_MAP.get(ext, "image/jpeg")

    # Build a collision-proof filename: <uuid>_<original-name>.<ext>
    # (secure_filename alone isn't enough — two uploads named "xray.jpg" for
    # the same visit would otherwise overwrite each other on disk.)
    safe_name     = secure_filename(file.filename) or f"upload.{ext}"
    unique_name   = f"{uuid.uuid4().hex}_{safe_name}"
    visit_dir     = _visit_upload_dir(visit_id)
    full_path     = os.path.join(visit_dir, unique_name)

    file.save(full_path)

    # Path stored in the DB, relative to FLASK_ROOT, so it's portable and
    # matches what serve_image_data()/serve_image() expect to join back on.
    relative_path = os.path.relpath(full_path, FLASK_ROOT)

    parsed_date = datetime.utcnow().date()
    if image_date:
        try:
            parsed_date = datetime.strptime(image_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    record = Image(
        visit_id    = visit_id,
        image_path  = relative_path,
        image_type  = image_type,
        description = description,
        uploaded_by = uploaded_by,
        image_date  = parsed_date,
    )
    record.mime_type = mime_type

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
    mime = getattr(img, "mime_type", "image/jpeg") or "image/jpeg"

    # Primary path: file on disk (current storage method)
    if img.image_path:
        full_path = os.path.join(FLASK_ROOT, img.image_path)
        if os.path.exists(full_path):
            return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))

    # Fallback: legacy rows uploaded before the switch to disk storage,
    # which still have their bytes sitting in the old base64 column.
    b64 = getattr(img, "image_data", None)
    if b64:
        return Response(base64.b64decode(b64), mimetype=mime)

    return jsonify({"error": "Image not found"}), 404


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

    if image.image_path:
        full_path = os.path.join(FLASK_ROOT, image.image_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError as e:
                # Don't block the DB delete if the file is already gone/locked
                print(f"[images] could not remove file {full_path}: {e}")

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