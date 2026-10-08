from flask import Blueprint, request, jsonify, send_file, Response, current_app, stream_with_context
import os
import io
import base64
import binascii
import threading
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

from database import db
from models import Image

try:                                    # only used for a friendlier "visit not found" message
    from models import Visit
except Exception:                       # pragma: no cover
    Visit = None

images_bp = Blueprint("images", __name__)

# ═════════════════════════════════════════════════════════════════════════════
#  CLINICAL IMAGES  (X-rays, OPGs, intra-oral photos)
#
#  HOW PICTURES ARE STORED
#  -----------------------
#  The picture itself is saved as an ordinary FILE. The database keeps only a
#  small record about it (which visit, type, date, description) plus WHERE the
#  file is - never the picture bytes.
#
#    Today (default)  ->  a folder on this computer:
#                         <backend>/uploads/images/<visit id>/<unique name>.jpg
#                         The database stores "uploads/images/<visit id>/<name>".
#
#    Later (optional) ->  object storage (Amazon S3, Cloudflare R2, DigitalOcean
#                         Spaces, Backblaze B2, MinIO ... anything S3-compatible).
#                         The database then stores "s3://<bucket>/<key>".
#
#  SWITCHING TO OBJECT STORAGE LATER - no code change, only settings:
#      pip install boto3
#      IMAGE_STORAGE=s3
#      S3_BUCKET=<bucket name>
#      S3_ACCESS_KEY_ID=<key>            S3_SECRET_ACCESS_KEY=<secret>
#      S3_REGION=<region>                (optional, e.g. ap-south-1)
#      S3_ENDPOINT_URL=<url>             (only for R2 / Spaces / B2 / MinIO)
#      S3_PREFIX=<folder inside bucket>  (optional)
#  Pictures uploaded before the switch stay in the local folder and keep
#  working: every record remembers where its own file is.
#
#  OTHER SETTINGS (all optional)
#      IMAGE_UPLOAD_ROOT=<folder>   keep the local files somewhere else
#                                   (for example a persistent disk on a host)
#      IMAGE_MAX_MB=25              biggest file accepted
#      IMAGE_PURGE_BASE64=1         see "OLD BASE64 PICTURES" below
#
#  OLD BASE64 PICTURES
#  -------------------
#  An earlier version kept the picture inside the database as base64 text
#  (column images.image_data). Those are copied out to real files
#  automatically, in the background, the first time this module is used.
#  The old text is NOT removed unless IMAGE_PURGE_BASE64=1 is set, and even
#  then only after the new file has been read back and matches byte for byte.
#  Nothing is ever lost by this conversion.
#
#  BACKUPS: because pictures are files, back up the uploads folder (or the
#  bucket) as well as the database.
# ═════════════════════════════════════════════════════════════════════════════

ALLOWED_TYPES = ["IOPA", "OPG", "CBCT", "INTRAORAL"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "pdf"}

FLASK_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_ROOT = os.path.abspath(os.environ.get("IMAGE_UPLOAD_ROOT") or os.path.join(FLASK_ROOT, "uploads", "images"))
LOCAL_PREFIX = "uploads/images/"          # how local files are written in images.image_path

MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png",  "webp": "image/webp",
    "gif": "image/gif",  "bmp": "image/bmp",
    "pdf": "application/pdf",
}
EXT_FOR_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
                "image/gif": "gif", "image/bmp": "bmp", "application/pdf": "pdf"}

IST_OFFSET = timedelta(hours=5, minutes=30)


def _max_bytes():
    try:
        return max(1, int(float(os.environ.get("IMAGE_MAX_MB", "25")))) * 1024 * 1024
    except ValueError:
        return 25 * 1024 * 1024


class ImageError(Exception):
    """A problem the person at the screen can understand and fix."""
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────────────────────────────────────
#  What kind of file is it really?  (looks at the first bytes, not the name)
# ─────────────────────────────────────────────────────────────────────────────
def sniff_mime(head):
    """Return the real type of a file from its first bytes, or None if unknown."""
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:2] == b"BM":
        return "image/bmp"
    if head[:5] == b"%PDF-":
        return "application/pdf"
    return None


def _unsupported_reason(head):
    if head[4:8] == b"ftyp" and head[8:12] in (b"heic", b"heix", b"hevc", b"mif1", b"msf1", b"heim", b"heis"):
        return ("This is an iPhone HEIC photo, which browsers cannot display. "
                "Please save or export it as JPG and upload that.")
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "TIFF pictures cannot be displayed in the browser. Please save it as JPG or PNG and upload that."
    if head[128:132] == b"DICM":
        return "This is a DICOM file. Please use the CBCT Volumes tab for DICOM, or export the X-ray as JPG."
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  STORAGE - one small class per place a file can live
# ─────────────────────────────────────────────────────────────────────────────
def _is_inside(path, root):
    path, root = os.path.abspath(path), os.path.abspath(root)
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:                     # different drives on Windows
        return False


class LocalStorage:
    """Files in a folder on this computer."""
    name = "local"

    def new_locator(self, visit_id, filename):
        return f"{LOCAL_PREFIX}{visit_id}/{filename}"

    def path_for(self, locator):
        """Absolute path for a stored locator, or None if it points outside the uploads area."""
        if not locator:
            return None
        rel = str(locator).replace("\\", "/").lstrip("/")      # rows written on Windows use "\"
        candidates = []
        if rel.startswith(LOCAL_PREFIX):
            candidates.append(os.path.join(UPLOAD_ROOT, *rel[len(LOCAL_PREFIX):].split("/")))
        candidates.append(os.path.join(FLASK_ROOT, *rel.split("/")))
        allowed_roots = (UPLOAD_ROOT, os.path.join(FLASK_ROOT, "uploads"))
        safe = [c for c in candidates if any(_is_inside(c, r) for r in allowed_roots)]
        for c in safe:
            if os.path.isfile(c):
                return c
        return safe[0] if safe else None

    def save(self, locator, stream):
        path = self.path_for(locator)
        if not path:
            raise ImageError("The picture could not be stored (bad file location).", 500)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".part"
        size = 0
        with open(tmp, "wb") as out:           # write fully, then rename: a half-written file is never served
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                size += len(chunk)
        os.replace(tmp, path)
        return size

    def exists(self, locator):
        path = self.path_for(locator)
        return bool(path and os.path.isfile(path))

    def size(self, locator):
        path = self.path_for(locator)
        try:
            return os.path.getsize(path) if path else None
        except OSError:
            return None

    def read(self, locator):
        path = self.path_for(locator)
        if not path or not os.path.isfile(path):
            return None
        with open(path, "rb") as fh:
            return fh.read()

    def delete(self, locator):
        path = self.path_for(locator)
        if path and os.path.isfile(path):
            os.remove(path)


class S3Storage:
    """Object storage (S3-compatible). Used only when IMAGE_STORAGE=s3."""
    name = "s3"

    def __init__(self):
        self._client = None
        self._lock = threading.Lock()

    @property
    def bucket(self):
        return os.environ.get("S3_BUCKET", "").strip()

    def client(self):
        with self._lock:
            if self._client is None:
                try:
                    import boto3
                except ImportError:
                    raise ImageError("Object storage is switched on but the 'boto3' package is not installed "
                                     "(run: pip install boto3).", 500)
                if not self.bucket:
                    raise ImageError("Object storage is switched on but S3_BUCKET is not set.", 500)
                kwargs = {}
                if os.environ.get("S3_ENDPOINT_URL"):
                    kwargs["endpoint_url"] = os.environ["S3_ENDPOINT_URL"]
                if os.environ.get("S3_REGION"):
                    kwargs["region_name"] = os.environ["S3_REGION"]
                if os.environ.get("S3_ACCESS_KEY_ID") and os.environ.get("S3_SECRET_ACCESS_KEY"):
                    kwargs["aws_access_key_id"] = os.environ["S3_ACCESS_KEY_ID"]
                    kwargs["aws_secret_access_key"] = os.environ["S3_SECRET_ACCESS_KEY"]
                self._client = boto3.client("s3", **kwargs)
            return self._client

    def new_locator(self, visit_id, filename):
        prefix = os.environ.get("S3_PREFIX", "").strip().strip("/")
        key = f"images/{visit_id}/{filename}"
        if prefix:
            key = f"{prefix}/{key}"
        if not self.bucket:
            raise ImageError("Object storage is switched on but S3_BUCKET is not set.", 500)
        return f"s3://{self.bucket}/{key}"

    @staticmethod
    def _split(locator):
        rest = str(locator)[len("s3://"):]
        bucket, _, key = rest.partition("/")
        return bucket, key

    def save(self, locator, stream, mime=None):
        bucket, key = self._split(locator)
        data = stream.read()
        extra = {"ContentType": mime} if mime else {}
        self.client().put_object(Bucket=bucket, Key=key, Body=data, **extra)
        return len(data)

    def exists(self, locator):
        bucket, key = self._split(locator)
        try:
            self.client().head_object(Bucket=bucket, Key=key)
            return True
        except ImageError:
            raise
        except Exception:
            return False

    def size(self, locator):
        return None                         # not looked up for lists (it would cost one request per picture)

    def open(self, locator):
        """(streaming body, size) or (None, None) when the object does not exist."""
        bucket, key = self._split(locator)
        try:
            obj = self.client().get_object(Bucket=bucket, Key=key)
            return obj["Body"], obj.get("ContentLength")
        except ImageError:
            raise
        except Exception as exc:
            print("[images] object storage read failed:", type(exc).__name__, str(exc)[:200])
            return None, None

    def read(self, locator):
        body, _ = self.open(locator)
        return body.read() if body is not None else None

    def delete(self, locator):
        bucket, key = self._split(locator)
        self.client().delete_object(Bucket=bucket, Key=key)


_LOCAL = LocalStorage()
_S3 = S3Storage()


def active_storage():
    """Where NEW uploads go."""
    return _S3 if os.environ.get("IMAGE_STORAGE", "local").strip().lower() == "s3" else _LOCAL


def storage_for(locator):
    """Which storage holds an EXISTING picture (each record remembers its own)."""
    return _S3 if str(locator or "").startswith("s3://") else _LOCAL


# ─────────────────────────────────────────────────────────────────────────────
#  Small helpers
# ─────────────────────────────────────────────────────────────────────────────
def _unique_filename(original_name, ext):
    """<32 hex chars>_<cleaned original name>.<ext> - can never collide, still readable in the folder."""
    stem = secure_filename(os.path.splitext(original_name or "")[0])[:60].strip("._-") or "image"
    return f"{uuid.uuid4().hex}_{stem}.{ext}"


def _who_is_uploading():
    """Name of the signed-in person, when the login system can tell us. Never blocks an upload."""
    try:
        try:
            from medical_history import current_actor
        except ImportError:
            from routes.medical_history import current_actor
        name = (current_actor() or {}).get("name")
        return str(name).strip() if name else None
    except Exception:
        return None


def _base64_of(img):
    return getattr(img, "image_data", None) or None


def _decode_base64(text):
    """bytes from stored base64 (accepts a 'data:image/png;base64,....' prefix). None if it is not valid."""
    if not text:
        return None
    raw = str(text).strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    raw = "".join(raw.split())
    try:
        data = base64.b64decode(raw + "=" * (-len(raw) % 4), validate=False)
    except (binascii.Error, ValueError):
        return None
    return data or None


def _guard(fn):
    """Turn problems into a readable JSON message and never leave a half-finished database change."""
    from functools import wraps

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ImageError as exc:
            db.session.rollback()
            return jsonify({"error": exc.message}), exc.status
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, HTTPException):          # e.g. picture id not found
                message = "This picture no longer exists." if exc.code == 404 else (exc.description or "Request failed")
                return jsonify({"error": message}), exc.code or 500
            print("[images] request failed:", type(exc).__name__, str(exc)[:300])
            return jsonify({"error": "The server could not complete this. Nothing was changed - please try again."}), 500
    return wrapped


# ─────────────────────────────────────────────────────────────────────────────
#  Database columns (unchanged list; safe to run at every start)
# ─────────────────────────────────────────────────────────────────────────────
def run_image_migrations(app):
    with app.app_context():
        from sqlalchemy import text, inspect
        insp = inspect(db.engine)
        try:
            cols = {c["name"]: c for c in insp.get_columns("images")}
        except Exception as e:
            print(f"[images migration] could not inspect images table: {e}")
            return
        dialect = db.engine.dialect.name

        def run(sql, message):
            # each change in its own short transaction, so one failure never blocks the others
            try:
                with db.engine.begin() as conn:
                    if dialect == "postgresql":
                        conn.execute(text("SET LOCAL lock_timeout = '10s'"))
                    conn.execute(text(sql))
                print(f"[images migration] {message}")
            except Exception as e:
                print(f"[images migration] {message} skipped: {type(e).__name__}")

        if "image_type" in cols and dialect == "postgresql":
            if "ENUM" in str(cols["image_type"]["type"]).upper():
                run("ALTER TABLE images ALTER COLUMN image_type TYPE VARCHAR(30)", "image_type -> VARCHAR(30)")

        if "image_path" in cols:
            length = getattr(cols["image_path"]["type"], "length", None)
            if length is not None and length < 500:
                if dialect == "postgresql":
                    run("ALTER TABLE images ALTER COLUMN image_path TYPE VARCHAR(500)", "image_path -> VARCHAR(500)")
                elif dialect == "mysql":
                    run("ALTER TABLE images MODIFY COLUMN image_path VARCHAR(500) NOT NULL", "image_path -> VARCHAR(500)")

        if "image_date" not in cols:
            run("ALTER TABLE images ADD COLUMN image_date DATE", "Added image_date")
        if "image_data" not in cols:
            run("ALTER TABLE images ADD COLUMN image_data TEXT", "Added image_data (only read for old base64 pictures)")
        if "mime_type" not in cols:
            run("ALTER TABLE images ADD COLUMN mime_type VARCHAR(50)", "Added mime_type")


# ─────────────────────────────────────────────────────────────────────────────
#  Old base64 pictures  ->  real files
# ─────────────────────────────────────────────────────────────────────────────
def _store_bytes(visit_id, data, mime, original_name="image"):
    """Save bytes with the active storage. Returns the locator to keep in images.image_path."""
    ext = EXT_FOR_MIME.get(mime, "jpg")
    store = active_storage()
    locator = store.new_locator(visit_id, _unique_filename(original_name, ext))
    if store is _S3:
        store.save(locator, io.BytesIO(data), mime)
    else:
        store.save(locator, io.BytesIO(data))
    return locator


def _convert_row(img):
    """
    Make sure one picture exists as a file. Returns one of:
      "file"      - already a file, nothing to do
      "converted" - was base64 only, a file has now been written
      "purged"    - file verified, old base64 text removed (only with IMAGE_PURGE_BASE64=1)
      "bad"       - base64 text is damaged and there is no file
      "missing"   - neither a file nor base64
    """
    b64 = _base64_of(img)
    store = storage_for(img.image_path)
    has_file = store.exists(img.image_path)
    purge = os.environ.get("IMAGE_PURGE_BASE64", "").strip() in ("1", "true", "yes")

    if not b64:
        return "file" if has_file else "missing"

    data = _decode_base64(b64)
    if not has_file:
        if data is None:
            return "bad"
        mime = sniff_mime(data[:16]) or getattr(img, "mime_type", None) or "image/jpeg"
        original = os.path.basename(str(img.image_path or "").replace("\\", "/")) or "image"
        img.image_path = _store_bytes(img.visit_id, data, mime, original)
        img.mime_type = mime
        db.session.commit()
        store = storage_for(img.image_path)
        result = "converted"
    else:
        result = "file"

    if purge and data is not None and store.read(img.image_path) == data:
        img.image_data = None               # the file is identical, so the copy in the database can go
        db.session.commit()
        return "purged"
    return result


def convert_base64_images():
    """Copy every base64-only picture out to a file. Safe to run any number of times."""
    if not hasattr(Image, "image_data"):
        return {}
    counts = {}
    ids = [row[0] for row in db.session.query(Image.id)
           .filter(Image.image_data.isnot(None), Image.image_data != "").order_by(Image.id).all()]
    for image_id in ids:
        try:
            img = db.session.get(Image, image_id)
            if img is None:
                continue
            outcome = _convert_row(img)
        except Exception as exc:
            db.session.rollback()
            outcome = "error"
            print(f"[images] could not convert picture {image_id}:", type(exc).__name__, str(exc)[:200])
        counts[outcome] = counts.get(outcome, 0) + 1
        db.session.expire_all()             # do not keep every picture's base64 text in memory
    if counts.get("converted") or counts.get("purged") or counts.get("bad") or counts.get("error"):
        print("[images] old base64 pictures:", ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    return counts


_conversion = {"started": False, "done": False, "counts": {}}
_conversion_lock = threading.Lock()


def _start_conversion_once():
    with _conversion_lock:
        if _conversion["started"]:
            return
        _conversion["started"] = True
    app = current_app._get_current_object()

    def work():
        try:
            with app.app_context():
                _conversion["counts"] = convert_base64_images()
        except Exception as exc:
            print("[images] base64 conversion stopped:", type(exc).__name__, str(exc)[:200])
        finally:
            try:
                with app.app_context():
                    db.session.remove()
            except Exception:
                pass
            _conversion["done"] = True

    threading.Thread(target=work, name="image-base64-conversion", daemon=True).start()


@images_bp.before_request
def _prepare():
    _start_conversion_once()


# ─────────────────────────────────────────────────────────────────────────────
#  UPLOAD
#  POST /api/visits/<visit_id>/images      (multipart form: image, type, description, image_date)
# ─────────────────────────────────────────────────────────────────────────────
@images_bp.route("/visits/<int:visit_id>/images", methods=["POST"])
@_guard
def upload_image(visit_id):
    if "image" not in request.files:
        return jsonify({"error": "Image file required"}), 400

    file        = request.files["image"]
    image_type  = (request.form.get("type") or "").strip().upper()
    description = (request.form.get("description") or "").strip()
    uploaded_by = (request.form.get("uploaded_by") or "").strip() or _who_is_uploading() or "SYSTEM"
    image_date  = (request.form.get("image_date") or "").strip()

    if image_type not in ALLOWED_TYPES:
        return jsonify({"error": f"Invalid image type. Must be one of: {', '.join(ALLOWED_TYPES)}"}), 400

    if not file or not file.filename:
        return jsonify({"error": "Please choose a picture to upload."}), 400

    if Visit is not None and db.session.get(Visit, visit_id) is None:
        return jsonify({"error": "This visit no longer exists."}), 404

    # ── size ──
    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size == 0:
        return jsonify({"error": "This file is empty (0 bytes). Please choose the picture again."}), 400
    limit = _max_bytes()
    if size > limit:
        return jsonify({"error": "This picture is too large (%.1f MB). The limit is %d MB."
                                 % (size / 1048576.0, limit // 1048576)}), 413

    # ── what it really is (first bytes), not what it is called ──
    head = stream.read(256)
    stream.seek(0)
    mime_type = sniff_mime(head)
    if mime_type is None:
        reason = _unsupported_reason(head) or "File type not allowed. Use JPG, PNG, WEBP, or PDF"
        return jsonify({"error": reason}), 400
    ext = EXT_FOR_MIME[mime_type]

    # ── save the file ──
    store    = active_storage()
    locator  = store.new_locator(visit_id, _unique_filename(file.filename, ext))
    if store is _S3:
        store.save(locator, stream, mime_type)
    else:
        store.save(locator, stream)

    parsed_date = (datetime.utcnow() + IST_OFFSET).date()
    if image_date:
        try:
            parsed_date = datetime.strptime(image_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # ── save the record; if that fails, do not leave an orphan file behind ──
    try:
        record = Image(
            visit_id    = visit_id,
            image_path  = locator,
            image_type  = image_type,
            description = description,
            uploaded_by = uploaded_by,
            image_date  = parsed_date,
        )
        record.mime_type = mime_type
        db.session.add(record)
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            store.delete(locator)
        except Exception:
            pass
        raise

    return jsonify(_serialize(record)), 201


# ─────────────────────────────────────────────────────────────────────────────
#  LIST
#  GET /api/visits/<visit_id>/images
# ─────────────────────────────────────────────────────────────────────────────
@images_bp.route("/visits/<int:visit_id>/images", methods=["GET"])
def list_images(visit_id):
    images = Image.query.filter_by(visit_id=visit_id).order_by(
        Image.image_date.desc().nullslast(),
        Image.uploaded_at.desc(),
        Image.id.desc(),
    ).all()
    return jsonify([_serialize(img) for img in images])


# ─────────────────────────────────────────────────────────────────────────────
#  THE PICTURE ITSELF
#  GET /api/images/<id>/data            -> the picture
#  GET /api/images/<id>/data?download=1 -> same, offered as a download
# ─────────────────────────────────────────────────────────────────────────────
def _download_name(img, mime):
    ext = EXT_FOR_MIME.get(mime, "jpg")
    date = img.image_date.strftime("%Y-%m-%d") if getattr(img, "image_date", None) else "undated"
    return f"{img.image_type or 'image'}_{date}_{img.id}.{ext}"


@images_bp.route("/images/<int:id>/data", methods=["GET"])
@_guard
def serve_image_data(id):
    img  = Image.query.get_or_404(id)
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    as_download = request.args.get("download") in ("1", "true", "yes")
    name = _download_name(img, mime)

    store = storage_for(img.image_path)

    # 1) A file in the local folder (normal case today)
    if store is _LOCAL:
        path = _LOCAL.path_for(img.image_path)
        if path and os.path.isfile(path):
            resp = send_file(path, mimetype=mime, conditional=True, max_age=3600,
                             as_attachment=as_download, download_name=name)
            resp.headers["Cache-Control"] = "private, max-age=3600"
            return resp

    # 2) An object in object storage
    else:
        body, length = _S3.open(img.image_path)
        if body is not None:
            def chunks():
                try:
                    for chunk in iter(lambda: body.read(256 * 1024), b""):
                        yield chunk
                finally:
                    try:
                        body.close()
                    except Exception:
                        pass
            headers = {"Cache-Control": "private, max-age=3600"}
            if length is not None:
                headers["Content-Length"] = str(length)
            if as_download:
                headers["Content-Disposition"] = f'attachment; filename="{name}"'
            return Response(stream_with_context(chunks()), mimetype=mime, headers=headers)

    # 3) An old picture still held as base64: show it, and write its file now
    data = _decode_base64(_base64_of(img))
    if data:
        real_mime = sniff_mime(data[:16]) or mime
        try:
            _convert_row(img)
        except Exception as exc:                         # showing the picture matters more than converting it
            db.session.rollback()
            print(f"[images] could not write file for picture {id}:", type(exc).__name__)
        headers = {"Cache-Control": "private, max-age=300"}
        if as_download:
            headers["Content-Disposition"] = f'attachment; filename="{_download_name(img, real_mime)}"'
        return Response(data, mimetype=real_mime, headers=headers)

    return jsonify({"error": "The file for this picture is missing on the server."}), 404


# Kept for old links. Only files inside the uploads folder can be fetched this way.
@images_bp.route("/images/file/<path:filepath>", methods=["GET"])
def serve_image(filepath):
    path = _LOCAL.path_for(filepath)
    if not path or not os.path.isfile(path):
        return jsonify({"error": "Image not found"}), 404
    ext = path.rsplit(".", 1)[-1].lower() if "." in os.path.basename(path) else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Image not found"}), 404
    return send_file(path, mimetype=MIME_MAP.get(ext, "application/octet-stream"), conditional=True)


# ─────────────────────────────────────────────────────────────────────────────
#  EDIT DETAILS
#  PUT /api/images/<id>      { description, image_date, type }
# ─────────────────────────────────────────────────────────────────────────────
@images_bp.route("/images/<int:id>", methods=["PUT"])
@_guard
def edit_image(id):
    image = Image.query.get_or_404(id)
    data  = request.get_json(force=True, silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "No data provided"}), 400

    if "description" in data:
        image.description = (str(data["description"]).strip() if data["description"] is not None else "")
    if "image_date" in data and data["image_date"]:
        try:
            image.image_date = datetime.strptime(str(data["image_date"])[:10], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "The date is not valid. Please choose it again."}), 400
    if "type" in data and data["type"]:
        new_type = str(data["type"]).strip().upper()
        if new_type not in ALLOWED_TYPES:
            return jsonify({"error": f"Invalid image type. Must be one of: {', '.join(ALLOWED_TYPES)}"}), 400
        image.image_type = new_type

    db.session.commit()
    return jsonify(_serialize(image))


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE
#  DELETE /api/images/<id>
# ─────────────────────────────────────────────────────────────────────────────
@images_bp.route("/images/<int:id>", methods=["DELETE"])
@_guard
def delete_image(id):
    image   = Image.query.get_or_404(id)
    locator = image.image_path

    # Record first: if this fails the picture is untouched and can simply be deleted again.
    db.session.delete(image)
    db.session.commit()

    try:
        storage_for(locator).delete(locator)
    except Exception as e:
        # The record is gone; a leftover file is harmless and must not make the delete look failed.
        print(f"[images] could not remove file for deleted picture {id}: {type(e).__name__}")

    return jsonify({"status": "deleted"})


# ─────────────────────────────────────────────────────────────────────────────
#  STATUS (for checking the storage at a glance)
#  GET /api/images/storage/status
# ─────────────────────────────────────────────────────────────────────────────
@images_bp.route("/images/storage/status", methods=["GET"])
@_guard
def storage_status():
    total = db.session.query(Image.id).count()
    with_base64 = 0
    if hasattr(Image, "image_data"):
        with_base64 = (db.session.query(Image.id)
                       .filter(Image.image_data.isnot(None), Image.image_data != "").count())
    in_object_storage = db.session.query(Image.id).filter(Image.image_path.like("s3://%")).count()
    return jsonify({
        "new_uploads_go_to":      active_storage().name,
        "pictures":               total,
        "in_local_folder":        total - in_object_storage,
        "in_object_storage":      in_object_storage,
        "still_holding_base64":   with_base64,
        "base64_conversion_done": _conversion["done"],
        "last_conversion":        _conversion["counts"],
        "max_upload_mb":          _max_bytes() // 1048576,
    })


def _serialize(img):
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    url  = f"/api/images/{img.id}/data"

    store = storage_for(img.image_path)
    if store is _LOCAL:
        available = _LOCAL.exists(img.image_path)
        size = _LOCAL.size(img.image_path) if available else None
        where = "local" if available else ("database" if _base64_of(img) else "missing")
        if where == "database":
            available = True
    else:
        available, size, where = True, None, "s3"

    uploaded_at = getattr(img, "uploaded_at", None)
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
        # stored in UTC, shown in Indian time
        "uploaded_at": (uploaded_at + IST_OFFSET).strftime("%d-%b-%Y %H:%M") if uploaded_at else None,
        # new, extra information (older screens simply ignore these)
        "storage":     where,          # "local" | "s3" | "database" (old base64, not yet converted) | "missing"
        "available":   available,      # False = the record exists but its file cannot be found
        "size":        size,           # bytes, when known
    }