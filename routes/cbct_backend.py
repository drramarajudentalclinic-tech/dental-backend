"""
cbct_backend.py  –  Complete CBCT Flask Blueprint

Endpoints:
  POST   /visits/<id>/cbct                – Upload DICOM ZIP, generate all slice PNGs
  GET    /visits/<id>/cbct                – List volumes for a visit
  GET    /cbct/<id>                       – Volume metadata
  GET    /cbct/<id>/slices                – All slice base64 images (axial/coronal/sagittal)
  GET    /cbct/<id>/slices/<view>/<n>     – Single slice image (direct JPEG)
  POST   /cbct/<id>/annotations           – Save annotations
  GET    /cbct/<id>/annotations           – Load annotations
  DELETE /cbct/<id>                       – Delete volume + annotations
  GET    /cbct/<id>/export/png            – Export composite screenshot PNG
  GET    /cbct/<id>/link                  – Private one-hour link to a cloud scan's slices
  GET    /cbct/storage/status             – How many scans are in the cloud / in the database
  POST   /cbct/storage/move-to-cloud      – (Doctor) move older scans' slices into the cloud

Where a scan is kept
  Cloud storage ON (IMAGE_STORAGE=s3, the same Cloudflare R2 settings as images.py):
      patients/<case no.>/cbct/<date>_v<visit>_scan<id>/slices.json         all slice pictures
      patients/<case no.>/cbct/<date>_v<visit>_scan<id>/original-dicom.zip  the uploaded ZIP
      (CBCT_KEEP_ORIGINAL=0 in Render stops keeping the ZIP)
      cbct_volumes.slice_data then holds only "s3://<bucket>/<…>/slices.json".
  Cloud storage OFF: as before, all slices inside cbct_volumes.slice_data.
  Both kinds open the same way, so older scans keep working.

Registration in app factory:
    from cbct_backend import cbct_bp, run_cbct_migrations
    app.register_blueprint(cbct_bp, url_prefix="/api")
    run_cbct_migrations(app)      # safe to call on every startup
"""

import os
import io
import json
import base64
import zipfile
import traceback
import tempfile
import numpy as np

from datetime import datetime
from flask import Blueprint, request, jsonify, Response, send_file
from sqlalchemy import create_engine, text
import os

# Somewhere near the top of the file, defined once
DATABASE_URL = os.environ.get("DATABASE_URL")  # or however you store it
engine = create_engine(DATABASE_URL)
# Optional: pydicom for real DICOM; gracefully degrade to synthetic data
try:
    import pydicom
    from pydicom.errors import InvalidDicomError
    HAS_PYDICOM = True
except ImportError:
    HAS_PYDICOM = False

# PIL for image processing
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Import models from the single merged models.py ────────────────────────────
from database import db
from models import CBCTVolume, CBCTAnnotation

cbct_bp = Blueprint("cbct", __name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://your-app.com",
]


# ══════════════════════════════════════════════════════════════════════════════
#  Internal utilities
# ══════════════════════════════════════════════════════════════════════════════

def _apply_wl(pixel_array, window=2500, level=500):
    """Window/level transform → uint8."""
    lo = level - window / 2
    hi = level + window / 2
    arr = np.clip(pixel_array.astype(np.float32), lo, hi)
    arr = ((arr - lo) / (hi - lo) * 255).astype(np.uint8)
    return arr


def _array_to_base64_jpeg(arr_2d, quality=75):
    """2-D uint8 numpy array → base64 JPEG string."""
    if not HAS_PIL:
        return ""
    img = PILImage.fromarray(arr_2d, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _generate_synthetic_volume(num_slices=80, size=256):
    """
    Generate a synthetic CBCT-like volume for demo / fallback.
    Returns a 3-D float32 numpy array (depth × rows × cols).
    """
    z = np.linspace(-1, 1, num_slices)
    y = np.linspace(-1, 1, size)
    x = np.linspace(-1, 1, size)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    jaw_mask = ((X**2 + (Y - 0.3)**2 < 0.6**2) & (np.abs(Z) < 0.8))
    teeth = np.zeros_like(X)
    for tx in np.linspace(-0.7, 0.7, 14):
        teeth += np.exp(-((X - tx)**2 / 0.003 + Y**2 / 0.005 + Z**2 / 0.01)) * 1500

    vol = np.where(jaw_mask, 800 + np.random.randn(*X.shape) * 50, -500)
    vol += teeth
    return vol.astype(np.float32)


def _extract_dicom_volume(zip_path):
    """
    Extract DICOM files from ZIP, sort by InstanceNumber, stack into volume.
    Returns (volume_3d, metadata_dict) or (None, {}) on failure.
    """
    if not (HAS_PYDICOM and HAS_PIL):
        return None, {}

    datasets = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith("/") or "__MACOSX" in name:
                continue
            try:
                data = zf.read(name)
                ds = pydicom.dcmread(io.BytesIO(data), force=True)
                if hasattr(ds, "pixel_array"):
                    datasets.append(ds)
            except Exception:
                continue

    if not datasets:
        return None, {}

    def _sort_key(ds):
        if hasattr(ds, "InstanceNumber"):
            try: return int(ds.InstanceNumber)
            except: pass
        if hasattr(ds, "SliceLocation"):
            try: return float(ds.SliceLocation)
            except: pass
        return 0

    datasets.sort(key=_sort_key)

    arrays = []
    for ds in datasets:
        try:
            arr = ds.pixel_array.astype(np.float32)
            slope     = float(getattr(ds, "RescaleSlope",     1))
            intercept = float(getattr(ds, "RescaleIntercept", 0))
            arr = arr * slope + intercept
            arrays.append(arr)
        except Exception:
            continue

    if not arrays:
        return None, {}

    target_h, target_w = arrays[0].shape
    normalised = []
    for a in arrays:
        if a.shape != (target_h, target_w):
            try:
                img = PILImage.fromarray(a.astype(np.float32))
                img = img.resize((target_w, target_h))
                a = np.array(img, dtype=np.float32)
            except Exception:
                a = np.zeros((target_h, target_w), dtype=np.float32)
        normalised.append(a)

    volume = np.stack(normalised, axis=0)  # (depth, rows, cols)

    first = datasets[0]
    meta = {
        "patient_name":    str(getattr(first, "PatientName",     "Unknown")),
        "patient_id":      str(getattr(first, "PatientID",       "")),
        "study_date":      str(getattr(first, "StudyDate",       "")),
        "modality":        str(getattr(first, "Modality",        "CT")),
        "institution":     str(getattr(first, "InstitutionName", "Unknown")),
        "rows":            int(getattr(first, "Rows",             target_h)),
        "cols":            int(getattr(first, "Columns",          target_w)),
        "num_slices":      len(normalised),
        "pixel_spacing":   [float(v) for v in getattr(first, "PixelSpacing", [0.3, 0.3])],
        "slice_thickness": float(getattr(first, "SliceThickness", 0.3)),
    }
    return volume, meta


def _build_slice_store(volume, window=2500, level=500):
    """
    Build base64 JPEG slices for all three planes.

    Returns:
        { "axial": [...], "coronal": [...], "sagittal": [...] }
    """
    depth, rows, cols = volume.shape
    result = {"axial": [], "coronal": [], "sagittal": []}

    for i in range(depth):
        result["axial"].append(_array_to_base64_jpeg(_apply_wl(volume[i], window, level)))
    for r in range(rows):
        result["coronal"].append(_array_to_base64_jpeg(_apply_wl(volume[:, r, :], window, level)))
    for c in range(cols):
        result["sagittal"].append(_array_to_base64_jpeg(_apply_wl(volume[:, :, c], window, level)))

    return result


def _store_slice_images(cbct_id, slice_store):
    """Persist slice JSON into CBCTVolume.slice_data."""
    vol = db.session.get(CBCTVolume, cbct_id)
    if not vol:
        return
    try:
        vol.slice_data = json.dumps(slice_store)
        db.session.commit()
    except Exception as e:
        print(f"[CBCT] Failed to store slices: {e}")
        db.session.rollback()


# ══════════════════════════════════════════════════════════════════════════════
#  Cloud storage (Cloudflare R2) - shares the bucket and settings of images.py
# ══════════════════════════════════════════════════════════════════════════════
def _images_module():
    """images.py (same routes folder) - it holds the cloud connection. None if it cannot be loaded."""
    try:
        try:
            import images as mod
        except ImportError:
            from routes import images as mod          # type: ignore
        return mod
    except Exception as exc:
        print("[CBCT] cloud storage helpers not available:", type(exc).__name__)
        return None


def _cloud_on():
    mod = _images_module()
    return mod if (mod is not None and mod.active_storage() is mod._S3) else None


def _in_cloud(vol):
    return str(getattr(vol, "slice_data", "") or "").startswith("s3://")


def _scan_locator(mod, vol, name):
    """s3://bucket/[prefix/]patients/<case>/cbct/<date>_v<visit>_scan<id>/<name>"""
    day = vol.uploaded_at or datetime.utcnow()
    return mod._S3.new_locator(vol.visit_id, f"scan{vol.id}/{name}", "CBCT", day)


def _sibling(locator, name):
    return locator.rsplit("/", 1)[0] + "/" + name


_slice_cache = {}            # cbct id -> parsed slices (the last 2 opened), so single-slice views stay fast


def _slices_bytes(vol):
    """The slices JSON as bytes (from the cloud or the database), or None."""
    if not vol.slice_data:
        return None
    if _in_cloud(vol):
        mod = _images_module()
        return mod._S3.read(vol.slice_data) if mod is not None else None
    return vol.slice_data.encode("utf-8")


def _slices(vol):
    """Parsed slices {axial, coronal, sagittal} or {}."""
    hit = _slice_cache.get(vol.id)
    if hit is not None and hit[0] == vol.slice_data:
        return hit[1]
    raw = _slices_bytes(vol)
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}
    if data and _in_cloud(vol):
        if len(_slice_cache) >= 2:
            _slice_cache.pop(next(iter(_slice_cache)))
        _slice_cache[vol.id] = (vol.slice_data, data)
    return data


def _put_scan(mod, vol, slice_json_bytes, zip_path=None):
    """Upload slices (+ the original ZIP) and check the slices byte for byte. Returns the slices locator."""
    loc = _scan_locator(mod, vol, "slices.json")
    mod._S3.save(loc, io.BytesIO(slice_json_bytes), "application/json")
    if mod._S3.read(loc) != slice_json_bytes:
        try:
            mod._S3.delete(loc)
        except Exception:
            pass
        raise RuntimeError("the slices in the cloud did not match")
    keep = (os.environ.get("CBCT_KEEP_ORIGINAL") or "1").strip().lower() not in ("0", "false", "no", "off")
    if zip_path and keep:
        bucket, key = mod._S3._split(_sibling(loc, "original-dicom.zip"))
        mod._S3.client().upload_file(zip_path, bucket, key, ExtraArgs={"ContentType": "application/zip"})
    return loc


def _delete_scan_objects(locator):
    mod = _images_module()
    if mod is None or not str(locator or "").startswith("s3://"):
        return
    for name in ("slices.json", "original-dicom.zip"):
        try:
            mod._S3.delete(_sibling(locator, name))
        except Exception as exc:
            print("[CBCT] could not remove", name, "from the cloud:", type(exc).__name__)


def _role():
    mod = _images_module()
    return mod._current_role() if mod is not None else ""


def _serialize_vol(v):
    """Serialise a CBCTVolume ORM object to a JSON-safe dict."""
    return {
        "id":              v.id,
        "visit_id":        v.visit_id,
        "patient_name":    v.patient_name,
        "patient_id":      v.patient_id or "",
        "study_date":      v.study_date  or "",
        "modality":        v.modality    or "CT",
        "institution":     v.institution or "",
        "num_slices":      v.num_slices,
        "coronal_slices":  v.coronal_slices,
        "sagittal_slices": v.sagittal_slices,
        "dimensions": {
            "depth": v.num_slices,
            "rows":  v.rows,
            "cols":  v.cols,
        },
        "voxel_spacing": {
            "x": v.pixel_spacing_x,
            "y": v.pixel_spacing_y,
            "z": v.slice_thickness,
        },
        "uploaded_by": v.uploaded_by or "",
        "notes":       v.notes       or "",
        "uploaded_at": v.uploaded_at.strftime("%d-%b-%Y %H:%M") if v.uploaded_at else "",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Routes
# ══════════════════════════════════════════════════════════════════════════════

# ── Upload ─────────────────────────────────────────────────────────────────────

@cbct_bp.route("/visits/<int:visit_id>/cbct", methods=["POST"])
def upload_cbct(visit_id):
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename.lower().endswith(".zip"):
        return jsonify({"error": "Only .zip files containing DICOM data are accepted"}), 400

    uploaded_by = request.form.get("uploaded_by", "USER")
    notes       = request.form.get("notes", "")

    # Save to temp file so pydicom can seek
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        f.save(tmp.name)
        zip_path = tmp.name

    try:
        volume_3d, dicom_meta = _extract_dicom_volume(zip_path)

        if volume_3d is None:
            # Fallback: synthetic demo volume
            volume_3d = _generate_synthetic_volume()
            dicom_meta = {
                "patient_name":    "Demo Patient",
                "patient_id":      "",
                "study_date":      datetime.utcnow().strftime("%Y-%m-%d"),
                "modality":        "CT",
                "institution":     "",
                "num_slices":      volume_3d.shape[0],
                "rows":            volume_3d.shape[1],
                "cols":            volume_3d.shape[2],
                "pixel_spacing":   [0.3, 0.3],
                "slice_thickness": 0.3,
            }

        depth, rows, cols = volume_3d.shape
        px = dicom_meta.get("pixel_spacing", [0.3, 0.3])

        cbct = CBCTVolume(
            visit_id         = visit_id,
            patient_name     = dicom_meta.get("patient_name",    "Unknown"),
            patient_id       = dicom_meta.get("patient_id",      ""),
            study_date       = dicom_meta.get("study_date",      ""),
            modality         = dicom_meta.get("modality",        "CT"),
            institution      = dicom_meta.get("institution",     ""),
            num_slices       = depth,
            coronal_slices   = rows,
            sagittal_slices  = cols,
            rows             = rows,
            cols             = cols,
            slice_thickness  = dicom_meta.get("slice_thickness", 0.3),
            pixel_spacing_x  = px[0] if len(px) > 0 else 0.3,
            pixel_spacing_y  = px[1] if len(px) > 1 else 0.3,
            uploaded_by      = uploaded_by,
            notes            = notes,
        )
        db.session.add(cbct)
        db.session.flush()   # get cbct.id before commit

        slice_store = _build_slice_store(volume_3d)
        cloud = _cloud_on()
        if cloud is not None:
            # cloud: the slices (and the original ZIP) go to the patient's cbct folder
            if cbct.uploaded_at is None:
                cbct.uploaded_at = datetime.utcnow()
            payload = json.dumps(slice_store).encode("utf-8")
            del slice_store
            try:
                cbct.slice_data = _put_scan(cloud, cbct, payload, zip_path)
            except Exception as exc:
                db.session.rollback()
                print("[CBCT] cloud upload failed:", type(exc).__name__, str(exc)[:200])
                return jsonify({"error": "The scan could not be saved in cloud storage ("
                                         + cloud._s3_problem(exc) + "). Nothing was saved - please try again."}), 502
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                _delete_scan_objects(cbct.slice_data)
                raise
        else:
            _store_slice_images(cbct.id, slice_store)
            db.session.commit()
        return jsonify({"cbct": _serialize_vol(cbct), "num_slices": depth}), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    finally:
        try:
            os.unlink(zip_path)
        except Exception:
            pass


# ── List volumes for a visit ───────────────────────────────────────────────────

@cbct_bp.route("/visits/<int:visit_id>/cbct", methods=["GET"])
def list_cbct(visit_id):
    vols = (
        CBCTVolume.query
        .filter_by(visit_id=visit_id)
        .order_by(CBCTVolume.uploaded_at.desc())
        .all()
    )
    return jsonify({
        "visit_id":   visit_id,
        "cbct_files": [_serialize_vol(v) for v in vols],
    })


# ── Volume metadata ────────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>", methods=["GET"])
def get_cbct(cbct_id):
    vol = db.get_or_404(CBCTVolume, cbct_id)
    return jsonify(_serialize_vol(vol))


# ── All slices (JSON) ──────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>/slices", methods=["GET"])
def get_slices(cbct_id):
    """
    Returns { slices: { axial: [...base64...], coronal: [...], sagittal: [...] } }
    The frontend renders each entry as:
        <img src="data:image/jpeg;base64,<entry>" />
    """
    vol = db.get_or_404(CBCTVolume, cbct_id)

    if _in_cloud(vol):
        try:
            raw = _slices_bytes(vol)
        except Exception as exc:
            mod = _images_module()
            reason = mod._s3_problem(exc) if mod is not None else type(exc).__name__
            return jsonify({"error": "This scan is in cloud storage, which cannot be reached now (" + reason + ")."}), 502
        if raw:
            # sent as it is stored - no need to unpack tens of MB just to pack them again
            return Response(b'{"slices":' + raw + b'}', mimetype="application/json",
                            headers={"Cache-Control": "private, max-age=3600"})
        return jsonify({"error": "The slices of this scan are missing in cloud storage."}), 404

    if vol.slice_data:
        try:
            data = json.loads(vol.slice_data)
            return jsonify({"slices": data})
        except Exception:
            pass

    # Regenerate synthetic slices when slice_data is missing
    volume_3d = _generate_synthetic_volume()
    store = _build_slice_store(volume_3d)
    return jsonify({"slices": store})


# ── Single slice (direct JPEG) ─────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>/slices/<view>/<int:n>", methods=["GET"])
def get_single_slice(cbct_id, view, n):
    if view not in ("axial", "coronal", "sagittal"):
        return jsonify({"error": "Invalid view. Use axial | coronal | sagittal"}), 400

    vol = db.get_or_404(CBCTVolume, cbct_id)

    try:
        data   = _slices(vol)
        slices = data.get(view, [])
        if not slices or n >= len(slices):
            return jsonify({"error": "Slice index out of range"}), 404
        img_bytes = base64.b64decode(slices[n])
        return Response(img_bytes, mimetype="image/jpeg")
    except Exception:
        return jsonify({"error": "Failed to retrieve slice"}), 500


# ── Save annotations ───────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>/annotations", methods=["POST"])
def save_annotations(cbct_id):
    db.get_or_404(CBCTVolume, cbct_id)   # 404 guard
    payload = request.get_json(force=True) or []

    # Replace all annotations for this volume
    CBCTAnnotation.query.filter_by(cbct_id=cbct_id).delete()
    for item in payload:
        ann = CBCTAnnotation(
            cbct_id  = cbct_id,
            ann_type = item.get("type", ""),
            ann_view = item.get("view", "axial"),
            data     = json.dumps(item),
        )
        db.session.add(ann)

    db.session.commit()
    return jsonify({"saved": len(payload)}), 200


# ── Load annotations ───────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>/annotations", methods=["GET"])
def load_annotations(cbct_id):
    anns = CBCTAnnotation.query.filter_by(cbct_id=cbct_id).all()
    result = []
    for a in anns:
        try:
            result.append(json.loads(a.data))
        except Exception:
            pass
    return jsonify(result)


# ── Delete volume ──────────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>", methods=["DELETE"])
def delete_cbct(cbct_id):
    vol = db.get_or_404(CBCTVolume, cbct_id)
    locator = vol.slice_data if _in_cloud(vol) else None
    # CBCTAnnotation has cascade="all, delete-orphan" on the relationship,
    # so deleting the volume also removes annotations automatically.
    db.session.delete(vol)
    db.session.commit()
    _slice_cache.pop(cbct_id, None)
    _delete_scan_objects(locator)          # record first; a leftover file is harmless
    return jsonify({"status": "deleted", "id": cbct_id})


# ── Direct link to a cloud scan's slices ───────────────────────────────────────
# GET /cbct/<id>/link -> { url, expires_in }  (url: null when the scan is not in the cloud)
# The viewer downloads the slices straight from the bucket with this private link
# (valid one hour), so tens of MB do not pass through the server. The bucket needs
# a CORS rule allowing the clinic website to read (see the setup notes).

@cbct_bp.route("/cbct/<int:cbct_id>/link", methods=["GET"])
def cbct_link(cbct_id):
    if not _role():
        return jsonify({"error": "Please sign in again."}), 401
    vol = db.get_or_404(CBCTVolume, cbct_id)
    if not _in_cloud(vol):
        return jsonify({"url": None})
    mod = _images_module()
    if mod is None:
        return jsonify({"url": None})
    try:
        return jsonify({"url": mod._S3.presign(vol.slice_data, "application/json", None, 3600), "expires_in": 3600})
    except Exception as exc:                  # the viewer then loads through /slices
        print(f"[CBCT] could not make a link for scan {cbct_id}:", type(exc).__name__, str(exc)[:200])
        return jsonify({"url": None})


# ── Cloud storage: status and moving older scans ───────────────────────────────

_cbct_move = {"running": False, "total": 0, "done": 0, "moved": 0, "failed": 0, "last_problem": None}


@cbct_bp.route("/cbct/storage/status", methods=["GET"])
def cbct_storage_status():
    total = db.session.query(CBCTVolume.id).count()
    in_cloud = db.session.query(CBCTVolume.id).filter(CBCTVolume.slice_data.like("s3://%")).count()
    in_db = (db.session.query(CBCTVolume.id)
             .filter(CBCTVolume.slice_data.isnot(None), CBCTVolume.slice_data != "",
                     ~CBCTVolume.slice_data.like("s3://%")).count())
    return jsonify({"scans": total, "in_cloud": in_cloud, "in_database": in_db,
                    "cloud_on": _cloud_on() is not None, "move": dict(_cbct_move)})


def move_scans_to_cloud(mod):
    ids = [r[0] for r in db.session.query(CBCTVolume.id)
           .filter(CBCTVolume.slice_data.isnot(None), CBCTVolume.slice_data != "",
                   ~CBCTVolume.slice_data.like("s3://%")).order_by(CBCTVolume.id).all()]
    _cbct_move.update(total=len(ids), done=0, moved=0, failed=0, last_problem=None)
    for cid in ids:
        loc = None
        try:
            vol = db.session.get(CBCTVolume, cid)
            if vol is None or _in_cloud(vol) or not vol.slice_data:
                _cbct_move["done"] += 1
                continue
            json.loads(vol.slice_data)                      # only well-formed slices are moved
            loc = _put_scan(mod, vol, vol.slice_data.encode("utf-8"))
            n = (db.session.query(CBCTVolume)
                 .filter(CBCTVolume.id == cid, ~CBCTVolume.slice_data.like("s3://%"))
                 .update({"slice_data": loc}, synchronize_session=False))
            db.session.commit()
            if n:
                _cbct_move["moved"] += 1
            else:
                _delete_scan_objects(loc)
        except Exception as exc:
            db.session.rollback()
            if loc:
                _delete_scan_objects(loc)
            _cbct_move["failed"] += 1
            _cbct_move["last_problem"] = f"scan {cid}: " + mod._s3_problem(exc)
            print(f"[CBCT] could not move scan {cid}:", type(exc).__name__, str(exc)[:200])
        _cbct_move["done"] += 1
        db.session.expire_all()
    print("[CBCT] move to cloud:", dict(_cbct_move))


@cbct_bp.route("/cbct/storage/move-to-cloud", methods=["POST"])
def cbct_move_to_cloud():
    if _role() not in ("doctor", "admin"):
        return jsonify({"error": "Only the doctor can move the scans."}), 403
    mod = _cloud_on()
    if mod is None:
        return jsonify({"error": "Switch the cloud on first: set IMAGE_STORAGE=s3 in Render (Environment)."}), 400
    check = mod.check_cloud()
    if not check["ok"]:
        return jsonify({"error": check["error"]}), 400
    if _cbct_move["running"]:
        return jsonify({"started": False, "message": "Already moving.", "move": dict(_cbct_move)}), 200
    _cbct_move["running"] = True
    from flask import current_app
    import threading
    app = current_app._get_current_object()

    def work():
        try:
            with app.app_context():
                move_scans_to_cloud(mod)
        except Exception as exc:
            _cbct_move["last_problem"] = str(exc)[:200]
        finally:
            try:
                with app.app_context():
                    db.session.remove()
            except Exception:
                pass
            _cbct_move["running"] = False

    threading.Thread(target=work, name="cbct-move-to-cloud", daemon=True).start()
    return jsonify({"started": True, "move": dict(_cbct_move)}), 202


# ── Export composite PNG ───────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:cbct_id>/export/png", methods=["GET"])
def export_png(cbct_id):
    """
    Build a 3-panel composite (axial / coronal / sagittal) at the middle slice
    of each plane and return it as a downloadable PNG.

    Query params:
      ax  – axial   slice index  (default: middle)
      cor – coronal  slice index (default: middle)
      sag – sagittal slice index (default: middle)
      w   – window  (default 2500)
      l   – level   (default 500)
    """
    if not HAS_PIL:
        return jsonify({"error": "PIL not installed – export unavailable"}), 501

    vol = db.get_or_404(CBCTVolume, cbct_id)

    data = _slices(vol)
    if not data:
        return jsonify({"error": "No slice data available"}), 404

    ax_slices  = data.get("axial",    [])
    cor_slices = data.get("coronal",  [])
    sag_slices = data.get("sagittal", [])

    def _mid(lst):
        return max(0, len(lst) // 2) if lst else 0

    ax_idx  = int(request.args.get("ax",  _mid(ax_slices)))
    cor_idx = int(request.args.get("cor", _mid(cor_slices)))
    sag_idx = int(request.args.get("sag", _mid(sag_slices)))

    panels = []
    for lst, idx, label in [
        (ax_slices,  ax_idx,  "AXIAL"),
        (cor_slices, cor_idx, "CORONAL"),
        (sag_slices, sag_idx, "SAGITTAL"),
    ]:
        if not lst or idx >= len(lst):
            img = PILImage.new("L", (256, 256), color=0)
        else:
            img = PILImage.open(io.BytesIO(base64.b64decode(lst[idx]))).convert("L")
            img = img.resize((256, 256))
        panels.append((img, label))

    # Stitch side-by-side with a small header strip per panel
    panel_w, panel_h = 256, 256
    header_h = 20
    total_w  = panel_w * len(panels)
    total_h  = panel_h + header_h

    out = PILImage.new("RGB", (total_w, total_h), color=(10, 10, 15))
    label_colors = {"AXIAL": (56, 189, 248), "CORONAL": (52, 211, 153), "SAGITTAL": (244, 114, 182)}

    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(out)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
    except Exception:
        draw = None
        font = None

    for i, (img, label) in enumerate(panels):
        x_off = i * panel_w
        out.paste(img.convert("RGB"), (x_off, header_h))
        if draw:
            color = label_colors.get(label, (255, 255, 255))
            draw.text((x_off + 6, 4), label, fill=color, font=font)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    buf.seek(0)

    fname = f"cbct_{cbct_id}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    return send_file(buf, mimetype="image/png", as_attachment=True, download_name=fname)


# ══════════════════════════════════════════════════════════════════════════════
#  DB Migrations  (safe to run on every startup)
# ══════════════════════════════════════════════════════════════════════════════
def run_cbct_migrations(app):
    """
    Safe CBCT migrations for both SQLite and PostgreSQL.
    """

    with app.app_context():

        from sqlalchemy import inspect, text

        conn = db.engine.connect()
        inspector = inspect(db.engine)

        # ----------------------------------------------------
        # Create cbct_volumes table if missing
        # ----------------------------------------------------

        CBCTVolume.__table__.create(bind=db.engine, checkfirst=True)

        # ----------------------------------------------------
        # Add missing columns
        # ----------------------------------------------------

        existing = {
            c["name"]
            for c in inspector.get_columns("cbct_volumes")
        }

        columns = {
            "patient_id": "VARCHAR(64)",
            "study_date": "VARCHAR(20)",
            "modality": "VARCHAR(10)",
            "institution": "VARCHAR(120)",
            "coronal_slices": "INTEGER DEFAULT 0",
            "sagittal_slices": "INTEGER DEFAULT 0",
            "rows": "INTEGER DEFAULT 512",
            "cols": "INTEGER DEFAULT 512",
            "slice_thickness": "FLOAT DEFAULT 0.3",
            "pixel_spacing_x": "FLOAT DEFAULT 0.3",
            "pixel_spacing_y": "FLOAT DEFAULT 0.3",
            "notes": "TEXT",
            "slice_data": "TEXT",
        }

        for col, dtype in columns.items():

            if col not in existing:

                try:
                    conn.execute(
                        text(
                            f"ALTER TABLE cbct_volumes ADD COLUMN {col} {dtype}"
                        )
                    )

                    conn.commit()

                    print(f"[CBCT] Added {col}")

                except Exception as e:

                    print(f"[CBCT] {col}: {e}")

        # ----------------------------------------------------
        # Create cbct_annotations table (PostgreSQL)
        # ----------------------------------------------------

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cbct_annotations (
                    id         SERIAL PRIMARY KEY,
                    cbct_id    INTEGER NOT NULL REFERENCES cbct_volumes(id) ON DELETE CASCADE,
                    ann_type   VARCHAR(30),
                    ann_view   VARCHAR(20),
                    data       TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("[CBCT] cbct_annotations table ready")

        except Exception as e:
            print(f"[CBCT] {e}")

        finally:
            conn.close()