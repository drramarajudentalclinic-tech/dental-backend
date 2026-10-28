from flask import Blueprint, request, jsonify, send_file, Response, current_app, stream_with_context
import os
import re
import io
import base64
import binascii
import threading
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from werkzeug.exceptions import HTTPException

from database import db
from models import Image

try:                                    # only used for a friendlier "visit not found" message
    from models import Visit
except Exception:                       # pragma: no cover
    Visit = None

images_bp = Blueprint("images", __name__)

# ═════════════════════════════════════════════════════════════════════════════
#  CLINICAL IMAGES  (X-rays, OPGs, intra-oral photos, implant details)
#
#  ANY FILE TYPE CAN BE UPLOADED (up to IMAGE_MAX_MB):
#    shown on screen      JPG, PNG, WEBP, GIF, BMP, AVIF, PDF
#    shown as a preview   iPhone HEIC/HEIF, TIFF (RVG sensors), DICOM X-rays (.dcm)
#                         - a JPG preview is made by the server the first time the
#                           file is opened and kept next to it; the original is kept
#                           unchanged and is what "Download" gives.
#                           Needs in requirements.txt:  Pillow  pillow-heif  pydicom  numpy
#                           (without them the file is still saved and can be downloaded)
#    downloaded to open   STL/PLY/OBJ scans, Word, Excel, ZIP, text ... anything else
#    refused              programs and web pages (.exe, .bat, .js, .html, .svg ...)
#                         because opening them could harm the computer
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
#    Cloud (IMAGE_STORAGE=s3) -> object storage: Cloudflare R2 (used by this
#                         clinic), or Amazon S3, DigitalOcean Spaces, Backblaze B2,
#                         MinIO ... anything S3-compatible.
#                         The database then stores "s3://<bucket>/<key>", and each
#                         patient has one folder in the bucket:
#                           patients/<case no.>/xrays/<date>_v<visit>_<name>.jpg   (IOPA, OPG)
#                           patients/<case no.>/photos/...                        (intra-oral)
#                           patients/<case no.>/cbct/...                          (CBCT pictures)
#                           patients/<case no.>/implants/...                      (implant box / sticker)
#                         so every file of a patient is in one place.
#
#  CLOUDFLARE R2 - settings in Render -> dental-backend -> Environment:
#      IMAGE_STORAGE=s3
#      S3_BUCKET=sssohc-clinic-files
#      S3_ENDPOINT_URL=https://<account id>.r2.cloudflarestorage.com
#      S3_REGION=auto
#      S3_ACCESS_KEY_ID=...   S3_SECRET_ACCESS_KEY=...   (only in Render, never in code)
#  and the line  boto3  in requirements.txt.
#  Then Doctor dashboard -> Cloud storage -> "Check connection" and
#  "Move pictures to the cloud" (copies every older picture into the bucket,
#  checks it byte for byte, and only then frees the old copy).
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

# IMPLANT = photo of the implant box / sticker; its system, size and torque are in the description
ALLOWED_TYPES = ["IOPA", "OPG", "CBCT", "INTRAORAL", "IMPLANT"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "pdf"}   # old /images/file/ links only

# programs / web pages: never stored (they could run when opened)
BLOCKED_EXTENSIONS = {"exe", "msi", "bat", "cmd", "com", "scr", "pif", "cpl", "ps1", "psm1", "vbs", "vbe", "wsf",
                      "js", "mjs", "jse", "jar", "sh", "bash", "php", "py", "pl", "rb", "html", "htm", "xhtml",
                      "shtml", "svg", "svgz", "hta", "dll", "sys", "lnk", "reg", "apk", "app", "dmg", "iso"}

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
                "image/gif": "gif", "image/bmp": "bmp", "application/pdf": "pdf",
                "image/avif": "avif", "image/tiff": "tif", "image/heic": "heic", "image/heif": "heif",
                "application/dicom": "dcm"}

# by file name, for files whose first bytes do not say what they are
MIME_FOR_EXT = {
    "stl": "model/stl", "ply": "model/ply", "obj": "model/obj", "3mf": "model/3mf", "dcm": "application/dicom",
    "dicom": "application/dicom", "zip": "application/zip", "rar": "application/vnd.rar", "7z": "application/x-7z-compressed",
    "doc": "application/msword", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text", "rtf": "application/rtf", "txt": "text/plain", "csv": "text/csv",
    "mp4": "video/mp4", "mov": "video/quicktime", "mp3": "audio/mpeg", "wav": "audio/wav",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif",
    "bmp": "image/bmp", "pdf": "application/pdf", "avif": "image/avif", "tif": "image/tiff", "tiff": "image/tiff",
    "heic": "image/heic", "heif": "image/heif",
}

BROWSER_SHOWS = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp", "image/avif", "application/pdf"}
PREVIEW_MIMES = {"image/heic", "image/heif", "image/tiff", "application/dicom"}   # a JPG preview is made

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


def _ext_of(filename):
    name = os.path.basename(str(filename or "").replace("\\", "/"))
    return name.rsplit(".", 1)[1].lower()[:10] if "." in name else ""


def detect_type(head, filename):
    """(mime type, file extension) for any file - from its first bytes, else from its name.
    Raises ImageError for programs / web pages, which are never stored."""
    ext = _ext_of(filename)
    if ext in BLOCKED_EXTENSIONS:
        raise ImageError(f"“.{ext}” files cannot be uploaded (programs and web pages could harm the computer). "
                         "Pictures, PDFs, scans and documents are fine.", 400)
    head = bytes(head or b"")
    if head[:2] == b"MZ" or head[:4] == b"\x7fELF":
        raise ImageError("This file is a program, and programs cannot be uploaded.", 400)
    low = head[:64].lstrip().lower()
    if low.startswith((b"<!doctype html", b"<html", b"<svg", b"<?xml", b"<script")) and ext not in ("txt", "csv"):
        raise ImageError("Web pages and SVG drawings cannot be uploaded. Please save it as PNG or PDF.", 400)

    mime = sniff_mime(head)
    if mime is None:
        if head[4:8] == b"ftyp":
            brand = head[8:12]
            if brand in (b"avif", b"avis"):
                mime = "image/avif"
            elif brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"hevx"):
                mime = "image/heic"
            elif brand in (b"mif1", b"msf1"):
                mime = "image/heif"
            elif brand in (b"qt  ",):
                mime = "video/quicktime"
            else:
                mime = MIME_FOR_EXT.get(ext) or "video/mp4"
        elif head[:4] in (b"II*\x00", b"MM\x00*"):
            mime = "image/tiff"
        elif head[128:132] == b"DICM":
            mime = "application/dicom"
    if mime is None:
        mime = MIME_FOR_EXT.get(ext)
    if mime is None:
        import mimetypes
        guessed = mimetypes.guess_type("x." + ext)[0] if ext else None
        mime = guessed if guessed and not guessed.startswith(("text/html", "application/javascript", "image/svg")) else "application/octet-stream"
    out_ext = EXT_FOR_MIME.get(mime) or (ext if ext and ext.isalnum() else "") or "bin"
    if mime == "image/jpeg" and ext in ("jpeg", "jpg"):
        out_ext = ext
    return mime[:120], out_ext


def file_kind(mime):
    """image (shown as it is) | pdf | preview (shown through a JPG preview) | file (downloaded)"""
    if mime == "application/pdf":
        return "pdf"
    if mime in BROWSER_SHOWS:
        return "image"
    if mime in PREVIEW_MIMES:
        return "preview"
    return "file"


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

    def new_locator(self, visit_id, filename, image_type=None, image_date=None):
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


def _s3_config():
    """Short waits (a slow network must not hang an upload) and the checksum setting
    Cloudflare R2 accepts with every boto3 version."""
    from botocore.config import Config
    base = dict(connect_timeout=5, read_timeout=60, retries={"max_attempts": 3})
    try:
        return Config(request_checksum_calculation="when_required",
                      response_checksum_validation="when_required", **base)
    except TypeError:                       # older botocore: no such setting, nothing to change
        return Config(**base)


def _safe_part(text, fallback):
    """A case number etc. as one safe folder name (letters, digits, - _ .)."""
    cleaned = "".join(ch if (ch.isalnum() or ch in "-_.") else "-" for ch in str(text or "").strip())
    cleaned = cleaned.strip(".-")[:60]
    return cleaned or fallback


FOLDER_FOR_TYPE = {"IOPA": "xrays", "OPG": "xrays", "CBCT": "cbct", "INTRAORAL": "photos", "IMPLANT": "implants"}


def _patient_key(visit_id, filename, image_type=None, image_date=None):
    """patients/<case no.>/<xrays|photos|cbct>/<YYYY-MM-DD>_v<visit>_<filename>"""
    case = None
    try:
        from models import Patient
        v = db.session.get(Visit, int(visit_id)) if Visit is not None else None
        p = db.session.get(Patient, v.patient_id) if v is not None else None
        case = p.case_number if p is not None else None
    except Exception:
        case = None
    folder = f"patients/{_safe_part(case, 'no-case')}" if case else f"patients/no-case/visit-{visit_id}"
    kind = FOLDER_FOR_TYPE.get(str(image_type or "").upper(), "other")
    day = image_date.strftime("%Y-%m-%d") if hasattr(image_date, "strftime") else (datetime.utcnow() + IST_OFFSET).strftime("%Y-%m-%d")
    return f"{folder}/{kind}/{day}_v{visit_id}_{filename}"


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
                kwargs = {"config": _s3_config()}
                endpoint = os.environ.get("S3_ENDPOINT_URL", "").strip()
                if endpoint:
                    kwargs["endpoint_url"] = endpoint
                region = os.environ.get("S3_REGION", "").strip() or ("auto" if "r2.cloudflarestorage.com" in endpoint else "")
                if region:
                    kwargs["region_name"] = region
                if os.environ.get("S3_ACCESS_KEY_ID") and os.environ.get("S3_SECRET_ACCESS_KEY"):
                    kwargs["aws_access_key_id"] = os.environ["S3_ACCESS_KEY_ID"]
                    kwargs["aws_secret_access_key"] = os.environ["S3_SECRET_ACCESS_KEY"]
                self._client = boto3.client("s3", **kwargs)
            return self._client

    def new_locator(self, visit_id, filename, image_type=None, image_date=None):
        prefix = os.environ.get("S3_PREFIX", "").strip().strip("/")
        key = _patient_key(visit_id, filename, image_type, image_date)
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

    def presign(self, locator, mime=None, download_name=None, expires=3600):
        """A private link to one object that works for `expires` seconds only.
        The browser loads the file straight from the bucket (R2 downloads are free),
        so the picture does not pass through the server."""
        bucket, key = self._split(locator)
        params = {"Bucket": bucket, "Key": key, "ResponseCacheControl": f"private, max-age={int(expires)}"}
        if mime:
            params["ResponseContentType"] = mime
        if download_name:
            safe = "".join(ch for ch in download_name if ch not in '"\\\r\n')
            params["ResponseContentDisposition"] = f'attachment; filename="{safe}"'
        return self.client().generate_presigned_url("get_object", Params=params, ExpiresIn=int(expires))


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

        if dialect == "postgresql":
            # an old CHECK rule may allow only IOPA/OPG/CBCT/INTRAORAL - remove it so "IMPLANT" can be saved
            # (the server itself still checks the kind against ALLOWED_TYPES)
            try:
                with db.engine.connect() as conn:
                    names = [r[0] for r in conn.execute(text(
                        "SELECT conname FROM pg_constraint WHERE conrelid = 'images'::regclass AND contype = 'c' "
                        "AND pg_get_constraintdef(oid) ILIKE '%image_type%' "
                        "AND pg_get_constraintdef(oid) NOT ILIKE '%IMPLANT%'")).fetchall()]
            except Exception as e:
                names = []
                print(f"[images migration] could not read image_type rules: {type(e).__name__}")
            for name in names:
                run(f'ALTER TABLE images DROP CONSTRAINT "{name}"', f"Removed old image_type rule {name} (allows IMPLANT)")

        if "image_date" not in cols:
            run("ALTER TABLE images ADD COLUMN image_date DATE", "Added image_date")
        if "image_data" not in cols:
            run("ALTER TABLE images ADD COLUMN image_data TEXT", "Added image_data (only read for old base64 pictures)")
        if "mime_type" not in cols:
            run("ALTER TABLE images ADD COLUMN mime_type VARCHAR(120)", "Added mime_type")
        else:
            length = getattr(cols["mime_type"]["type"], "length", None)
            if length is not None and length < 120 and dialect in ("postgresql", "mysql"):
                # Word / Excel types are longer than 50 letters
                sql = ("ALTER TABLE images ALTER COLUMN mime_type TYPE VARCHAR(120)" if dialect == "postgresql"
                       else "ALTER TABLE images MODIFY COLUMN mime_type VARCHAR(120)")
                run(sql, "mime_type -> VARCHAR(120)")
    _ensure_imaging_table(app)


# ─────────────────────────────────────────────────────────────────────────────
#  Old base64 pictures  ->  real files
# ─────────────────────────────────────────────────────────────────────────────
def _store_bytes(visit_id, data, mime, original_name="image", image_type=None, image_date=None, store=None, ext=None):
    """Save bytes with the active storage. Returns the locator to keep in images.image_path."""
    ext = ext or EXT_FOR_MIME.get(mime) or _ext_of(original_name) or "bin"
    store = store or active_storage()
    locator = store.new_locator(visit_id, _unique_filename(original_name, ext), image_type, image_date)
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
        mime = sniff_mime(data[:256]) or getattr(img, "mime_type", None) or "image/jpeg"
        original = os.path.basename(str(img.image_path or "").replace("\\", "/")) or "image"
        img.image_path = _store_bytes(img.visit_id, data, mime, original,
                                      img.image_type, getattr(img, "image_date", None))
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
    _ensure_imaging_table()


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
        return jsonify({"error": "Please choose a file to upload."}), 400

    if Visit is not None and db.session.get(Visit, visit_id) is None:
        return jsonify({"error": "This visit no longer exists."}), 404

    # ── size ──
    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size == 0:
        return jsonify({"error": "This file is empty (0 bytes). Please choose it again."}), 400
    limit = _max_bytes()
    if size > limit:
        return jsonify({"error": "This file is too large (%.1f MB). The limit is %d MB."
                                 % (size / 1048576.0, limit // 1048576)}), 413

    # ── what it really is (first bytes, then the name); programs are refused ──
    head = stream.read(512)
    stream.seek(0)
    mime_type, ext = detect_type(head, file.filename)

    parsed_date = (datetime.utcnow() + IST_OFFSET).date()
    if image_date:
        try:
            parsed_date = datetime.strptime(image_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # ── save the file (in the cloud: in this patient's folder) ──
    store    = active_storage()
    locator  = store.new_locator(visit_id, _unique_filename(file.filename, ext), image_type, parsed_date)
    if store is _S3:
        try:
            store.save(locator, stream, mime_type)
        except ImageError:
            raise
        except Exception as exc:
            print("[images] cloud upload failed:", type(exc).__name__, str(exc)[:200])
            raise ImageError("The file could not be saved in cloud storage (" + _s3_problem(exc) + "). "
                             "Nothing was saved - please try again in a minute.", 502)
    else:
        store.save(locator, stream)

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
    ext = EXT_FOR_MIME.get(mime) or _ext_of(img.image_path) or "bin"
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
                             as_attachment=as_download or file_kind(mime) == "file", download_name=name)
            resp.headers["Cache-Control"] = "private, max-age=3600"
            resp.headers["X-Content-Type-Options"] = "nosniff"
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
            headers = {"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"}
            if length is not None:
                headers["Content-Length"] = str(length)
            if as_download or file_kind(mime) == "file":
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


# ─────────────────────────────────────────────────────────────────────────────
#  DIRECT LINK (pictures in the cloud)
#  GET /api/images/<id>/link  -> { url, download_url, mime_type, expires_in }
#  url is a private link to the file in the bucket, valid for one hour; the screen
#  shows the picture from there. For a picture not in the cloud: { url: null } and
#  the screen loads it through /data as before.
# ─────────────────────────────────────────────────────────────────────────────
LINK_SECONDS = 3600


@images_bp.route("/images/<int:id>/link", methods=["GET"])
@_guard
def image_link(id):
    if not _current_role():
        return jsonify({"error": "Please sign in again."}), 401
    img  = Image.query.get_or_404(id)
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    if storage_for(img.image_path) is not _S3:
        return jsonify({"url": None, "mime_type": mime})
    try:
        return jsonify({
            "url":          _S3.presign(img.image_path, mime, None, LINK_SECONDS),
            "download_url": _S3.presign(img.image_path, mime, _download_name(img, mime), LINK_SECONDS),
            "mime_type":    mime,
            "expires_in":   LINK_SECONDS,
        })
    except Exception as exc:                 # the screen then loads it through /data
        print(f"[images] could not make a link for picture {id}:", type(exc).__name__, str(exc)[:200])
        return jsonify({"url": None, "mime_type": mime})


# ─────────────────────────────────────────────────────────────────────────────
#  PREVIEW for files the browser cannot show (HEIC, TIFF, DICOM)
#  GET /api/images/<id>/preview  -> a JPG made from the file (made once, then kept
#  next to it as "<file>.preview.jpg"). The original file is never changed.
# ─────────────────────────────────────────────────────────────────────────────
PREVIEW_MAX_SIDE = 2400


def _preview_locator(locator):
    return f"{locator}.preview.jpg"


def _to_8bit(arr, invert=False):
    """numpy array of any depth -> 0..255 bytes, using the 0.5 % - 99.5 % range (good for X-rays)."""
    import numpy as np
    a = np.asarray(arr, dtype="float32")
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        return np.zeros(a.shape, dtype="uint8")
    lo, hi = np.percentile(finite, [0.5, 99.5])
    if hi <= lo:
        lo, hi = float(finite.min()), float(finite.max()) or 1.0
    a = np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) * 255.0
    if invert:
        a = 255.0 - a
    return a.astype("uint8")


def make_preview(data, mime):
    """JPG bytes of a HEIC / TIFF / DICOM file. Raises ImageError with a plain reason."""
    try:
        from PIL import Image as PILImage, ImageOps
    except ImportError:
        raise ImageError("The server cannot make previews yet (add Pillow to requirements.txt). "
                         "Use Download to open the file.", 501)
    try:
        if mime == "application/dicom":
            try:
                import pydicom
                import numpy as np  # noqa: F401
            except ImportError:
                raise ImageError("The server cannot show DICOM files yet (add pydicom and numpy to requirements.txt). "
                                 "Use Download to open the file.", 501)
            ds = pydicom.dcmread(io.BytesIO(data), force=True)
            arr = ds.pixel_array
            if getattr(ds, "NumberOfFrames", 1) and int(getattr(ds, "NumberOfFrames", 1) or 1) > 1:
                arr = arr[len(arr) // 2]                       # several frames: the middle one
            if arr.ndim == 3 and arr.shape[-1] in (3, 4):
                pic = PILImage.fromarray(arr.astype("uint8")).convert("RGB")
            else:
                slope = float(getattr(ds, "RescaleSlope", 1) or 1)
                intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
                invert = str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1"
                pic = PILImage.fromarray(_to_8bit(arr * slope + intercept, invert))
        else:
            if mime in ("image/heic", "image/heif"):
                try:
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                except ImportError:
                    raise ImageError("The server cannot show iPhone HEIC photos yet (add pillow-heif to requirements.txt). "
                                     "Use Download to open the file.", 501)
            pic = PILImage.open(io.BytesIO(data))
            try:
                pic.seek(0)                                  # multi-page TIFF: the first page
            except Exception:
                pass
            pic = ImageOps.exif_transpose(pic)
            if pic.mode in ("I;16", "I;16B", "I;16L", "I", "F"):  # 16-bit X-ray sensors
                import numpy as np
                pic = PILImage.fromarray(_to_8bit(np.array(pic)))
        if pic.mode not in ("RGB", "L"):
            pic = pic.convert("RGB")
        pic.thumbnail((PREVIEW_MAX_SIDE, PREVIEW_MAX_SIDE))
        out = io.BytesIO()
        pic.save(out, "JPEG", quality=88)
        return out.getvalue()
    except ImageError:
        raise
    except Exception as exc:
        print("[images] preview failed:", type(exc).__name__, str(exc)[:200])
        raise ImageError("A preview could not be made from this file (it may be compressed in a way the server "
                         "cannot read). Use Download to open it.", 422)


@images_bp.route("/images/<int:id>/preview", methods=["GET"])
@_guard
def image_preview(id):
    img  = Image.query.get_or_404(id)
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    if file_kind(mime) in ("image", "pdf"):
        return serve_image_data(id)
    if mime not in PREVIEW_MIMES:
        raise ImageError("This kind of file cannot be shown here. Use Download to open it.", 415)
    store = storage_for(img.image_path)
    ploc = _preview_locator(img.image_path)
    jpg = None
    try:
        jpg = store.read(ploc) if (store is _LOCAL or store.exists(ploc)) else None
    except ImageError:
        raise
    except Exception:
        jpg = None
    if not jpg:
        original = store.read(img.image_path) or _decode_base64(_base64_of(img))
        if not original:
            raise ImageError("The file for this picture is missing on the server.", 404)
        jpg = make_preview(original, mime)
        try:                                              # keep it, so it is made only once
            if store is _S3:
                store.save(ploc, io.BytesIO(jpg), "image/jpeg")
            else:
                store.save(ploc, io.BytesIO(jpg))
        except Exception as exc:
            print(f"[images] could not keep the preview of {id}:", type(exc).__name__)
    return Response(jpg, mimetype="image/jpeg",
                    headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"})


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
        try:
            storage_for(locator).delete(_preview_locator(locator))   # its preview, if one was made
        except Exception:
            pass
    except Exception as e:
        # The record is gone; a leftover file is harmless and must not make the delete look failed.
        print(f"[images] could not remove file for deleted picture {id}: {type(e).__name__}")

    return jsonify({"status": "deleted"})


# ─────────────────────────────────────────────────────────────────────────────
#  CLOUD STORAGE - connection check and moving older pictures into the bucket
#  GET  /api/images/storage/check          writes, reads back and removes a tiny test file
#  POST /api/images/storage/move-to-cloud  (Doctor) copies every older picture into the
#                                          bucket, in the background; progress in /status
# ─────────────────────────────────────────────────────────────────────────────
def _s3_problem(exc):
    """A short, plain reason for a cloud storage failure (never shows a key)."""
    if isinstance(exc, ImageError):
        return exc.message
    if isinstance(exc, ImportError):
        return "the server is missing boto3 - add the line  boto3  to requirements.txt"
    name = type(exc).__name__
    code = ""
    if hasattr(exc, "response"):
        try:
            code = str(exc.response.get("Error", {}).get("Code", ""))
        except Exception:
            code = ""
    if code in ("InvalidAccessKeyId", "SignatureDoesNotMatch", "InvalidToken", "Unauthorized"):
        return "the access key or secret key is not right - copy them again into Render"
    if code in ("NoSuchBucket",):
        return "the bucket name in S3_BUCKET was not found"
    if code in ("AccessDenied", "403", "Forbidden"):
        return "the key is not allowed to use this bucket - give the API token Object Read & Write on it"
    if name in ("EndpointConnectionError", "ConnectTimeoutError", "ConnectionClosedError", "ReadTimeoutError"):
        return "the storage address (S3_ENDPOINT_URL) cannot be reached"
    if name == "NoRegionError":
        return "set S3_REGION=auto"
    if name in ("InvalidEndpoint", "ValueError") and "endpoint" in str(exc).lower():
        return "S3_ENDPOINT_URL is not a valid address"
    return f"{code or name}"


def _cloud_settings():
    endpoint = os.environ.get("S3_ENDPOINT_URL", "").strip()
    host = endpoint.split("://", 1)[-1].split("/", 1)[0]
    if ".r2.cloudflarestorage.com" in host:            # do not show the account id in full
        acc = host.split(".", 1)[0]
        host = f"{acc[:4]}…{acc[-4:]}.r2.cloudflarestorage.com" if len(acc) > 8 else host
    return {
        "configured":  bool(_S3.bucket and os.environ.get("S3_ACCESS_KEY_ID") and os.environ.get("S3_SECRET_ACCESS_KEY")),
        "bucket":      _S3.bucket or None,
        "endpoint":    host or None,
        "prefix":      os.environ.get("S3_PREFIX", "").strip().strip("/") or None,
        "switched_on": active_storage() is _S3,
    }


def _current_role():
    """'doctor' / 'reception' of the signed-in person ('' when it cannot be told)."""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request(optional=True)
        role = (get_jwt() or {}).get("role")
        if role:
            return str(role).strip().lower()
    except Exception:
        pass
    try:
        try:
            from auth_utils import get_current_role
        except ImportError:
            from routes.auth_utils import get_current_role
        return str(get_current_role() or "").strip().lower()
    except Exception:
        return ""


def check_cloud():
    """Write, read back and delete one tiny file. Returns {ok, ...}."""
    info = _cloud_settings()
    if not info["bucket"]:
        return {**info, "ok": False, "error": "Cloud storage is not set up yet: S3_BUCKET is missing in Render (Environment)."}
    if not info["configured"]:
        return {**info, "ok": False, "error": "S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY is missing in Render (Environment)."}
    started = datetime.utcnow()
    probe = f"s3://{_S3.bucket}/" + (f"{info['prefix']}/" if info["prefix"] else "") + f".connection-check/{uuid.uuid4().hex}.txt"
    payload = b"Sri Satya Sai Oral Health Center - storage check"
    try:
        _S3.save(probe, io.BytesIO(payload), "text/plain")
        back = _S3.read(probe)
        _S3.delete(probe)
    except Exception as exc:
        return {**info, "ok": False, "error": "Cloud storage could not be used: " + _s3_problem(exc) + "."}
    if back != payload:
        return {**info, "ok": False, "error": "A test file was saved but could not be read back the same."}
    return {**info, "ok": True, "seconds": round((datetime.utcnow() - started).total_seconds(), 2),
            "message": "Connected: a test file was saved, read back and removed."}


_move = {"running": False, "started_at": None, "finished_at": None, "total": 0, "done": 0,
         "moved": 0, "missing": 0, "failed": 0, "last_problem": None}
_move_lock = threading.Lock()


def _strip_old_id(name):
    """'3f2a…(32 hex)_my_opg.jpg' -> 'my_opg' (a new unique id is added again)."""
    stem = os.path.splitext(os.path.basename(str(name or "").replace("\\", "/")))[0]
    head, sep, rest = stem.partition("_")
    if sep and len(head) == 32 and all(c in "0123456789abcdef" for c in head.lower()):
        stem = rest
    return stem or "image"


def _move_one(image_id):
    """Copy one picture into the bucket and check it. 'moved' | 'already' | 'missing'."""
    img = db.session.get(Image, image_id)
    if img is None or str(img.image_path or "").startswith("s3://"):
        return "already"
    old_path = img.image_path
    data = _LOCAL.read(old_path) if old_path else None
    if data is None:
        data = _decode_base64(_base64_of(img))
    if not data:
        return "missing"
    mime = sniff_mime(data[:256]) or getattr(img, "mime_type", None) or "image/jpeg"
    locator = _store_bytes(img.visit_id, data, mime, _strip_old_id(old_path), img.image_type,
                           getattr(img, "image_date", None), store=_S3,
                           ext=EXT_FOR_MIME.get(mime) or _ext_of(old_path) or None)
    try:
        if _S3.read(locator) != data:                      # byte-for-byte check before anything is freed
            raise ImageError("the copy in the bucket did not match", 502)
        changes = {"image_path": locator}
        if hasattr(Image, "mime_type"):
            changes["mime_type"] = mime
        if hasattr(Image, "image_data"):
            changes["image_data"] = None                    # the bucket now holds it - free the database
        # only if nobody changed this picture meanwhile (another server worker, a delete)
        done = (db.session.query(Image)
                .filter(Image.id == image_id, Image.image_path == old_path)
                .update(changes, synchronize_session=False))
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            _S3.delete(locator)
        except Exception:
            pass
        raise
    if not done:
        try:
            _S3.delete(locator)
        except Exception:
            pass
        return "already"
    path = _LOCAL.path_for(old_path) if old_path and not str(old_path).startswith("s3://") else None
    if path and os.path.isfile(path):
        try:
            os.remove(path)                                 # the server disk copy is no longer needed
        except OSError:
            pass
    return "moved"


def move_pictures_to_cloud():
    ids = [row[0] for row in db.session.query(Image.id)
           .filter(or_(Image.image_path.is_(None), ~Image.image_path.like("s3://%")))
           .order_by(Image.id).all()]
    _move.update(total=len(ids), done=0, moved=0, missing=0, failed=0, last_problem=None)
    for image_id in ids:
        try:
            outcome = _move_one(image_id)
        except Exception as exc:
            db.session.rollback()
            outcome = "failed"
            _move["last_problem"] = f"picture {image_id}: " + _s3_problem(exc)
            print(f"[images] could not move picture {image_id} to the cloud:", type(exc).__name__, str(exc)[:200])
        if outcome in ("moved", "missing", "failed"):
            _move[outcome] += 1
        _move["done"] += 1
        db.session.expire_all()
    # pictures already in the bucket that still carry an old base64 copy in the database:
    # free it once the bucket copy is checked byte for byte
    if hasattr(Image, "image_data"):
        extra = [row[0] for row in db.session.query(Image.id)
                 .filter(Image.image_path.like("s3://%"), Image.image_data.isnot(None), Image.image_data != "")
                 .order_by(Image.id).all()]
        _move["total"] += len(extra)
        for image_id in extra:
            try:
                img = db.session.get(Image, image_id)
                data = _decode_base64(_base64_of(img)) if img is not None else None
                if data is not None and _S3.read(img.image_path) == data:
                    img.image_data = None
                    db.session.commit()
                    _move["moved"] += 1
            except Exception as exc:
                db.session.rollback()
                _move["failed"] += 1
                _move["last_problem"] = f"picture {image_id}: " + _s3_problem(exc)
            _move["done"] += 1
            db.session.expire_all()
    print("[images] move to cloud:", {k: _move[k] for k in ("total", "moved", "missing", "failed")})


@images_bp.route("/images/storage/check", methods=["GET"])
@_guard
def storage_check():
    return jsonify(check_cloud())


@images_bp.route("/images/storage/browser-check", methods=["GET"])
@_guard
def storage_browser_check():
    """A tiny file in the bucket + a private link to it: the Cloud storage panel reads it
    from the browser to check that the bucket's CORS rule lets the website read files
    directly (needed for CBCT scans to load straight from the cloud)."""
    if not _current_role():
        return jsonify({"error": "Please sign in again."}), 401
    if active_storage() is not _S3:
        return jsonify({"url": None})
    info = _cloud_settings()
    loc = f"s3://{_S3.bucket}/" + (f"{info['prefix']}/" if info["prefix"] else "") + ".connection-check/browser-read.txt"
    try:
        _S3.save(loc, io.BytesIO(b"ok"), "text/plain")
        return jsonify({"url": _S3.presign(loc, "text/plain", None, 300)})
    except Exception as exc:
        return jsonify({"url": None, "error": "Cloud storage could not be used: " + _s3_problem(exc) + "."})


@images_bp.route("/images/storage/move-to-cloud", methods=["POST"])
@_guard
def storage_move_to_cloud():
    if _current_role() not in ("doctor", "admin"):
        return jsonify({"error": "Only the doctor can move the pictures."}), 403
    if active_storage() is not _S3:
        return jsonify({"error": "Switch the cloud on first: set IMAGE_STORAGE=s3 in Render (Environment)."}), 400
    check = check_cloud()
    if not check["ok"]:
        return jsonify({"error": check["error"]}), 400
    with _move_lock:
        if _move["running"]:
            return jsonify({"started": False, "message": "Already moving.", "move": dict(_move)}), 200
        _move.update(running=True, started_at=datetime.utcnow().isoformat() + "Z", finished_at=None)
    app = current_app._get_current_object()

    def work():
        try:
            with app.app_context():
                for _ in range(600):                        # let the old-base64 conversion finish first
                    if _conversion["done"] or not _conversion["started"]:
                        break
                    threading.Event().wait(1)
                move_pictures_to_cloud()
        except Exception as exc:
            _move["last_problem"] = _s3_problem(exc)
            print("[images] move to cloud stopped:", type(exc).__name__, str(exc)[:200])
        finally:
            try:
                with app.app_context():
                    db.session.remove()
            except Exception:
                pass
            _move.update(running=False, finished_at=datetime.utcnow().isoformat() + "Z")

    threading.Thread(target=work, name="image-move-to-cloud", daemon=True).start()
    return jsonify({"started": True, "message": "Moving the pictures to the cloud in the background.",
                    "move": dict(_move)}), 202


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
        "cloud":                  _cloud_settings(),
        "move":                   dict(_move),
    })


# ═════════════════════════════════════════════════════════════════════════════
#  IMAGING QUEUE  (Doctor dashboard -> "X-rays & Scans")
#
#  X-rays, OPGs, intra-oral photos and CBCT scans are added AFTER the visit,
#  from the Doctor dashboard - often they are not ready during the visit.
#
#    * Every visit that is closed (Close Visit on the visit page, or Complete
#      on the dashboard) joins the queue as "pending" by itself.
#    * The doctor opens it, uploads the pictures / scans, and then
#        "Mark as uploaded"  (only when at least one file is there), or
#        "No images needed"  (only when nothing was uploaded)
#      - both take the visit off the queue. Either can be undone ("back to pending").
#    * Any older visit can be found with the search and opened the same way.
#
#  Table visit_imaging (one row per visit that has been in the queue), made
#  automatically at start-up / first use:
#    visit_id, status (pending | uploaded | none), note, queued_at, done_at, done_by
#
#  GET  /api/imaging/queue?status=pending|done&q=     list + summary
#  GET  /api/imaging/search?q=                        any patient's visits (older ones too)
#  GET  /api/imaging/<visit_id>                       one visit
#  POST /api/imaging/<visit_id>/status  {status: uploaded | none | pending, note}
#  (Doctor only.)
# ═════════════════════════════════════════════════════════════════════════════
class VisitImaging(db.Model):
    __tablename__ = "visit_imaging"
    __table_args__ = {"extend_existing": True}
    visit_id  = db.Column(db.Integer, primary_key=True, autoincrement=False)
    status    = db.Column(db.String(20), nullable=False, default="pending")
    note      = db.Column(db.Text)
    queued_at = db.Column(db.DateTime, default=datetime.utcnow)
    done_at   = db.Column(db.DateTime)
    done_by   = db.Column(db.String(120))


IMAGING_STATUSES = ("pending", "uploaded", "none")
OVERDUE_DAYS = 2
_imaging_ready = {"ok": False}
_imaging_lock = threading.Lock()


def _ensure_imaging_table(app=None):
    """Create visit_imaging once (safe to call often)."""
    if _imaging_ready["ok"]:
        return
    with _imaging_lock:
        if _imaging_ready["ok"]:
            return
        try:
            if app is not None:
                with app.app_context():
                    VisitImaging.__table__.create(bind=db.engine, checkfirst=True)
            else:
                VisitImaging.__table__.create(bind=db.engine, checkfirst=True)
            _imaging_ready["ok"] = True
        except Exception as exc:
            print("[imaging] could not prepare the visit_imaging table:", type(exc).__name__, str(exc)[:200])


_CLOSE_RX = re.compile(r"/visits/(\d+)/close/?$")


@images_bp.after_app_request
def _queue_closed_visit(response):
    """A visit was closed (Close Visit / Complete): put it in the imaging queue."""
    try:
        if request.method != "PUT" or response.status_code >= 300 or "/billing/" in request.path:
            return response
        m = _CLOSE_RX.search(request.path)
        if not m:
            return response
        _ensure_imaging_table()
        vid = int(m.group(1))
        if db.session.get(VisitImaging, vid) is None:
            db.session.add(VisitImaging(visit_id=vid, status="pending", queued_at=datetime.utcnow()))
            db.session.commit()
    except Exception as exc:                       # never spoil the close itself
        db.session.rollback()
        print("[imaging] could not add the closed visit to the queue:", type(exc).__name__, str(exc)[:200])
    return response


def _doctor_only():
    if _current_role() not in ("doctor", "admin"):
        raise ImageError("Only the doctor can use the X-rays & Scans section.", 403)


def _ist(dt, fmt):
    return (dt + IST_OFFSET).strftime(fmt) if dt else None


def _file_counts(visit_ids):
    """{visit_id: {IOPA, OPG, INTRAORAL, CBCT, scans, total, last}}"""
    out = {vid: {"IOPA": 0, "OPG": 0, "INTRAORAL": 0, "CBCT": 0, "IMPLANT": 0, "scans": 0, "total": 0, "last": None}
           for vid in visit_ids}
    if not visit_ids:
        return out
    for vid, kind, n, last in (db.session.query(Image.visit_id, Image.image_type, func.count(Image.id),
                                                func.max(Image.uploaded_at))
                               .filter(Image.visit_id.in_(visit_ids))
                               .group_by(Image.visit_id, Image.image_type).all()):
        c = out[vid]
        key = str(kind or "").upper()
        c[key if key in c else "INTRAORAL"] += n
        c["total"] += n
        if last and (c["last"] is None or last > c["last"]):
            c["last"] = last
    try:
        from models import CBCTVolume
        for vid, n, last in (db.session.query(CBCTVolume.visit_id, func.count(CBCTVolume.id),
                                              func.max(CBCTVolume.uploaded_at))
                             .filter(CBCTVolume.visit_id.in_(visit_ids))
                             .group_by(CBCTVolume.visit_id).all()):
            c = out[vid]
            c["scans"] += n
            c["total"] += n
            if last and (c["last"] is None or last > c["last"]):
                c["last"] = last
    except Exception:
        db.session.rollback()
    return out


def _imaging_item(row, visit, patient, counts):
    c = dict(counts.get(visit.id) or {"IOPA": 0, "OPG": 0, "INTRAORAL": 0, "CBCT": 0, "IMPLANT": 0, "scans": 0, "total": 0, "last": None})
    last = c.pop("last", None)
    now = datetime.utcnow()
    status = row.status if row is not None else None
    queued = row.queued_at if row is not None else None
    waiting = (now - queued).days if (queued and status == "pending") else None
    treatment = (getattr(visit, "treatment_done", None) or getattr(visit, "followup_treatment", None)
                 or getattr(visit, "diagnosis", None) or getattr(visit, "chief_complaint", None) or "")
    vstatus = str(getattr(visit, "status", "") or "")
    return {
        "visit_id":     visit.id,
        "patient_id":   patient.id,
        "patient_name": patient.name,
        "case_number":  patient.case_number,
        "mobile":       patient.mobile,
        "age":          patient.age,
        "gender":       patient.gender,
        "visit_date":   _ist(visit.visit_date, "%d %b %Y"),
        "visit_closed": vstatus.lower() == "closed" or bool(getattr(visit, "closed_at", None)),
        "closed_at":    _ist(getattr(visit, "closed_at", None), "%d %b %Y, %I:%M %p"),
        "doctor":       getattr(visit, "closed_by", None) or getattr(visit, "assigned_doctor", None) or "",
        "treatment":    str(treatment)[:160],
        "status":       status,                         # None = never in the queue (older visit)
        "note":         row.note if row is not None else None,
        "queued_at":    _ist(queued, "%d %b %Y, %I:%M %p"),
        "waiting_days": waiting,
        "overdue":      bool(waiting is not None and waiting >= OVERDUE_DAYS),
        "done_at":      _ist(row.done_at, "%d %b %Y, %I:%M %p") if row is not None else None,
        "done_by":      row.done_by if row is not None else None,
        "counts":       c,
        "last_upload":  _ist(last, "%d %b %Y, %I:%M %p"),
    }


def _patient_filter(query, q):
    from models import Patient
    like = f"%{q}%"
    return query.filter(or_(Patient.name.ilike(like), Patient.case_number.ilike(like), Patient.mobile.ilike(like)))


@images_bp.route("/imaging/queue", methods=["GET"])
@_guard
def imaging_queue():
    _doctor_only()
    from models import Patient
    status = (request.args.get("status") or "pending").strip().lower()
    q = (request.args.get("q") or "").strip()
    base = (db.session.query(VisitImaging, Visit, Patient)
            .join(Visit, Visit.id == VisitImaging.visit_id)
            .join(Patient, Patient.id == Visit.patient_id))
    if status == "pending":
        query = base.filter(VisitImaging.status == "pending").order_by(VisitImaging.queued_at.asc(), Visit.id.asc())
        limit = 300
    else:
        query = (base.filter(VisitImaging.status.in_(["uploaded", "none"]))
                 .order_by(VisitImaging.done_at.desc().nullslast(), Visit.id.desc()))
        limit = 80
    if q:
        query = _patient_filter(query, q)
    rows = query.limit(limit).all()
    counts = _file_counts([v.id for _r, v, _p in rows])

    now = datetime.utcnow()
    today_start = datetime.combine((now + IST_OFFSET).date(), datetime.min.time()) - IST_OFFSET
    pending = base.filter(VisitImaging.status == "pending")
    summary = {
        "pending":    pending.count(),
        "overdue":    pending.filter(VisitImaging.queued_at <= now - timedelta(days=OVERDUE_DAYS)).count(),
        "done_today": base.filter(VisitImaging.status.in_(["uploaded", "none"]), VisitImaging.done_at >= today_start).count(),
    }
    return jsonify({"items": [_imaging_item(r, v, p, counts) for r, v, p in rows], "summary": summary,
                    "overdue_days": OVERDUE_DAYS})


@images_bp.route("/imaging/search", methods=["GET"])
@_guard
def imaging_search():
    """Any patient's visits (also older ones that were never in the queue)."""
    _doctor_only()
    from models import Patient
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify({"items": []})
    patients = _patient_filter(Patient.query, q).order_by(Patient.name.asc()).limit(15).all()
    pairs = []
    for p in patients:
        for v in (Visit.query.filter(Visit.patient_id == p.id)
                  .order_by(Visit.visit_date.desc().nullslast(), Visit.id.desc()).limit(6).all()):
            if str(getattr(v, "status", "") or "").upper() == "CANCELLED":
                continue
            pairs.append((v, p))
    ids = [v.id for v, _p in pairs]
    rows = {r.visit_id: r for r in VisitImaging.query.filter(VisitImaging.visit_id.in_(ids)).all()} if ids else {}
    counts = _file_counts(ids)
    return jsonify({"items": [_imaging_item(rows.get(v.id), v, p, counts) for v, p in pairs]})


def _one_item(visit_id):
    from models import Patient
    visit = db.session.get(Visit, visit_id)
    if visit is None:
        raise ImageError("This visit no longer exists.", 404)
    patient = db.session.get(Patient, visit.patient_id)
    if patient is None:
        raise ImageError("The patient of this visit no longer exists.", 404)
    return _imaging_item(db.session.get(VisitImaging, visit_id), visit, patient, _file_counts([visit_id]))


@images_bp.route("/imaging/<int:visit_id>", methods=["GET"])
@_guard
def imaging_one(visit_id):
    _doctor_only()
    return jsonify(_one_item(visit_id))


@images_bp.route("/imaging/<int:visit_id>/status", methods=["POST"])
@_guard
def imaging_set_status(visit_id):
    _doctor_only()
    data = request.get_json(force=True, silent=True) or {}
    status = str(data.get("status") or "").strip().lower()
    if status not in IMAGING_STATUSES:
        raise ImageError("Choose: uploaded, none (no images needed) or pending.")
    item = _one_item(visit_id)                   # also checks the visit exists
    total = item["counts"]["total"]
    if status == "uploaded" and total == 0:
        raise ImageError("Nothing has been uploaded for this visit yet. Upload the pictures first, "
                         "or press “No images needed”.")
    if status == "none" and total > 0:
        raise ImageError(f"This visit already has {total} file{'s' if total != 1 else ''}. "
                         "Press “Mark as uploaded” instead.")
    row = db.session.get(VisitImaging, visit_id)
    if row is None:
        row = VisitImaging(visit_id=visit_id, queued_at=datetime.utcnow())
        db.session.add(row)
    row.status = status
    note = data.get("note")
    if note is not None:
        row.note = str(note).strip()[:500] or None
    if status == "pending":
        row.done_at, row.done_by = None, None
        if row.queued_at is None:
            row.queued_at = datetime.utcnow()
    else:
        row.done_at = datetime.utcnow()
        row.done_by = (_who_is_uploading() or _current_role() or "Doctor")[:120]
    db.session.commit()
    return jsonify(_one_item(visit_id))


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
        # how the screen shows it: image | pdf | preview (use preview_url) | file (download only)
        "kind":        file_kind(mime),
        "preview_url": f"/api/images/{img.id}/preview" if mime in PREVIEW_MIMES else None,
        "ext":         EXT_FOR_MIME.get(mime) or _ext_of(img.image_path) or "",
        "file_name":   _download_name(img, mime),
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