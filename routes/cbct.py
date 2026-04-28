"""
routes/cbct.py
──────────────
CBCT Blueprint — handles ZIP upload, slice serving, annotations.

pip install pydicom numpy pillow
"""

from flask import Blueprint, request, jsonify, Response
import os, io, base64, zipfile, json, uuid, traceback, threading
from datetime import datetime
from database import db
from sqlalchemy import text

cbct_bp = Blueprint("cbct", __name__)

# ── How many slices to skip between stored slices.
#    STEP=3 means store every 3rd slice → 66% fewer DB inserts.
SLICE_STEP = 3

# ── Max ZIP size accepted (bytes).
MAX_ZIP_MB    = 300
MAX_ZIP_BYTES = MAX_ZIP_MB * 1024 * 1024

# ── In-memory job tracker  { job_id: { status, volume_id, error } }
_jobs = {}


# ─── Date formatting helper ────────────────────────────────────────────────────

def fmt_date(val, fmt):
    """Safely format a date/datetime value; handles None and string types."""
    if not val:
        return None
    if isinstance(val, str):
        return val
    try:
        return val.strftime(fmt)
    except Exception:
        return str(val)


# ─── Migrations ───────────────────────────────────────────────────────────────

def run_cbct_migrations(app):
    with app.app_context():
        conn = db.engine.connect()
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cbct_volumes (
                    id            SERIAL PRIMARY KEY,
                    visit_id      INTEGER NOT NULL,
                    patient_name  VARCHAR(200),
                    study_date    DATE,
                    series_uid    VARCHAR(200),
                    num_slices    INTEGER DEFAULT 0,
                    voxel_x       FLOAT DEFAULT 1.0,
                    voxel_y       FLOAT DEFAULT 1.0,
                    voxel_z       FLOAT DEFAULT 1.0,
                    rows          INTEGER DEFAULT 512,
                    cols          INTEGER DEFAULT 512,
                    uploaded_at   TIMESTAMP DEFAULT NOW(),
                    uploaded_by   VARCHAR(100) DEFAULT 'SYSTEM',
                    notes         TEXT,
                    slice_step    INTEGER DEFAULT 1
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cbct_slices (
                    id          SERIAL PRIMARY KEY,
                    volume_id   INTEGER NOT NULL REFERENCES cbct_volumes(id) ON DELETE CASCADE,
                    axis        VARCHAR(10) NOT NULL,
                    index       INTEGER NOT NULL,
                    png_data    TEXT NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cbct_slices_vol_axis
                ON cbct_slices (volume_id, axis, index)
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cbct_annotations (
                    volume_id  INTEGER PRIMARY KEY,
                    data       TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("[cbct migration] Tables ready ✅")
        except Exception as e:
            print(f"[cbct migration] {e}")
        finally:
            conn.close()


# ─── Helper: 2D numpy plane → base64 PNG string ───────────────────────────────

def _plane_to_png_b64(plane_2d, lo, hi):
    from PIL import Image as PILImage
    clipped = plane_2d.clip(lo, hi)
    scaled  = ((clipped - lo) / max(hi - lo, 1.0) * 255).astype("uint8")
    buf     = io.BytesIO()
    PILImage.fromarray(scaled, mode="L").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ─── Background worker ────────────────────────────────────────────────────────

def _process_cbct(app, job_id, visit_id, zip_bytes, uploaded_by, notes):
    """Runs in a background thread. Updates _jobs[job_id] when done."""
    _jobs[job_id] = {"status": "processing", "volume_id": None, "error": None}

    try:
        import pydicom
        import numpy as np

        # ── Parse DICOM files from ZIP ────────────────────────────────────────
        try:
            zf_obj = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile:
            _jobs[job_id] = {"status": "error", "volume_id": None, "error": "Invalid or corrupted ZIP file"}
            return

        with zf_obj as zf:
            all_names = zf.namelist()
            names = []
            for n in all_names:
                if n.startswith("__MACOSX") or n.endswith("/"):
                    continue
                lower = n.lower()
                if lower.endswith(".dcm") or "." not in lower.split("/")[-1]:
                    names.append(n)
            if not names:
                names = [n for n in all_names
                         if not n.startswith("__MACOSX") and not n.endswith("/")]

            print(f"[cbct job={job_id}] {len(all_names)} entries, trying {len(names)} candidates")

            dicom_files = []
            skip_reasons = {}
            for name in names:
                raw = zf.read(name)
                try:
                    ds = pydicom.dcmread(io.BytesIO(raw), force=True)
                    if 0x7FE00010 not in ds:
                        skip_reasons["no_pixel_data"] = skip_reasons.get("no_pixel_data", 0) + 1
                        continue
                    try:
                        _ = ds.pixel_array
                        dicom_files.append(ds)
                    except Exception as px_err:
                        err_key = type(px_err).__name__ + ":" + str(px_err)[:80]
                        skip_reasons[err_key] = skip_reasons.get(err_key, 0) + 1
                        try:
                            rows_ = int(getattr(ds, "Rows", 0))
                            cols_ = int(getattr(ds, "Columns", 0))
                            bits  = int(getattr(ds, "BitsAllocated", 16))
                            dtype = np.uint16 if bits == 16 else np.uint8
                            px_bytes = bytes(ds.PixelData)
                            arr = np.frombuffer(px_bytes, dtype=dtype).astype(np.float32)
                            if rows_ > 0 and cols_ > 0 and arr.size >= rows_ * cols_:
                                arr = arr[:rows_ * cols_].reshape(rows_, cols_)
                                ds._raw_arr = arr
                                dicom_files.append(ds)
                        except Exception:
                            pass
                except Exception as read_err:
                    skip_reasons["read_err:" + str(read_err)[:60]] = skip_reasons.get("read_err:" + str(read_err)[:60], 0) + 1

            print(f"[cbct job={job_id}] Valid DICOM files: {len(dicom_files)}, skipped: {skip_reasons}")

        if not dicom_files:
            _jobs[job_id] = {"status": "error", "volume_id": None, "error": "No valid DICOM files found inside the ZIP"}
            return

        # ── Sort slices by Z ──────────────────────────────────────────────────
        def sort_key(ds):
            try:
                return float(ds.ImagePositionPatient[2])
            except Exception:
                pass
            try:
                return int(ds.InstanceNumber)
            except Exception:
                return 0

        dicom_files.sort(key=sort_key)

        # ── Metadata from first slice ─────────────────────────────────────────
        sample       = dicom_files[0]
        patient_name = str(getattr(sample, "PatientName", "Unknown"))
        raw_date     = str(getattr(sample, "StudyDate", ""))
        study_date   = None
        if len(raw_date) == 8:
            try:
                study_date = datetime.strptime(raw_date, "%Y%m%d").date()
            except Exception:
                pass
        series_uid = str(getattr(sample, "SeriesInstanceUID", str(uuid.uuid4())))
        rows = int(getattr(sample, "Rows",    512))
        cols = int(getattr(sample, "Columns", 512))
        ps   = getattr(sample, "PixelSpacing", [1.0, 1.0])
        vx, vy = float(ps[0]), float(ps[1])
        try:
            vz = float(sample.SliceThickness)
        except Exception:
            vz = 1.0

        # ── Build 3D volume ───────────────────────────────────────────────────
        print(f"[cbct job={job_id}] Building 3D volume…")
        slices_arr = []
        for ds in dicom_files:
            if hasattr(ds, "_raw_arr"):
                arr = ds._raw_arr.astype(np.float32)
            else:
                arr = ds.pixel_array.astype(np.float32)
            slope     = float(getattr(ds, "RescaleSlope",     1))
            intercept = float(getattr(ds, "RescaleIntercept", 0))

            if arr.ndim == 2:
                slices_arr.append(arr * slope + intercept)
            elif arr.ndim == 3:
                if arr.shape[2] in (3, 4):
                    gray = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
                    slices_arr.append(gray * slope + intercept)
                else:
                    for frame in arr:
                        slices_arr.append(frame * slope + intercept)
            elif arr.ndim == 4:
                for frame in arr:
                    if frame.shape[-1] in (3, 4):
                        gray = frame[..., 0] * 0.299 + frame[..., 1] * 0.587 + frame[..., 2] * 0.114
                    else:
                        gray = frame[..., 0]
                    slices_arr.append(gray * slope + intercept)
            else:
                flat = arr.reshape(-1, arr.shape[-2], arr.shape[-1])
                for frame in flat:
                    slices_arr.append(frame * slope + intercept)

        if not slices_arr:
            _jobs[job_id] = {"status": "error", "volume_id": None, "error": "No valid 2D slices could be extracted"}
            return

        volume = np.stack(slices_arr, axis=0)
        Z, Y, X = volume.shape
        print(f"[cbct job={job_id}] Volume shape Z={Z} Y={Y} X={X}")

        wc      = float(np.percentile(volume, 50))
        p2, p98 = float(np.percentile(volume, 2)), float(np.percentile(volume, 98))
        ww      = max(p98 - p2, 1.0)
        lo, hi  = wc - ww / 2, wc + ww / 2

        # ── DB insert inside app context ──────────────────────────────────────
        with app.app_context():
            conn = db.engine.connect()
            try:
                res = conn.execute(text("""
                    INSERT INTO cbct_volumes
                      (visit_id, patient_name, study_date, series_uid,
                       num_slices, voxel_x, voxel_y, voxel_z,
                       rows, cols, uploaded_by, notes, slice_step)
                    VALUES
                      (:vid, :pn, :sd, :uid,
                       :ns, :vx, :vy, :vz,
                       :rows, :cols, :ub, :notes, :step)
                    RETURNING id
                """), dict(
                    vid=visit_id, pn=patient_name, sd=study_date, uid=series_uid,
                    ns=Z, vx=vx, vy=vy, vz=vz, rows=rows, cols=cols,
                    ub=uploaded_by, notes=notes, step=SLICE_STEP
                ))
                volume_id = res.fetchone()[0]
                conn.commit()
                print(f"[cbct job={job_id}] Created volume id={volume_id}")

                print(f"[cbct job={job_id}] Generating PNGs with SLICE_STEP={SLICE_STEP}…")
                slice_rows = []

                for i in range(0, Z, SLICE_STEP):
                    slice_rows.append({
                        "vid": volume_id, "ax": "axial",
                        "i": i, "d": _plane_to_png_b64(volume[i, :, :], lo, hi)
                    })
                for i in range(0, Y, SLICE_STEP):
                    slice_rows.append({
                        "vid": volume_id, "ax": "coronal",
                        "i": i, "d": _plane_to_png_b64(volume[:, i, :], lo, hi)
                    })
                for i in range(0, X, SLICE_STEP):
                    slice_rows.append({
                        "vid": volume_id, "ax": "sagittal",
                        "i": i, "d": _plane_to_png_b64(volume[:, :, i], lo, hi)
                    })

                print(f"[cbct job={job_id}] Inserting {len(slice_rows)} slice rows…")
                conn.execute(
                    text("INSERT INTO cbct_slices (volume_id, axis, index, png_data) "
                         "VALUES (:vid, :ax, :i, :d)"),
                    slice_rows
                )

                stored_axial = len([r for r in slice_rows if r["ax"] == "axial"])
                conn.execute(
                    text("UPDATE cbct_volumes SET num_slices = :n WHERE id = :vid"),
                    dict(n=stored_axial, vid=volume_id)
                )
                conn.commit()
                print(f"[cbct job={job_id}] Done ✅ — {len(slice_rows)} slices stored")

            finally:
                conn.close()

        _jobs[job_id] = {"status": "done", "volume_id": volume_id, "error": None}

    except MemoryError:
        print(f"[cbct job={job_id}] MemoryError")
        _jobs[job_id] = {"status": "error", "volume_id": None, "error": "File too large — server ran out of memory"}
    except Exception as e:
        print(f"[cbct job={job_id}] UNEXPECTED ERROR:\n{traceback.format_exc()}")
        _jobs[job_id] = {"status": "error", "volume_id": None, "error": str(e)}


# ─── Upload ZIP → returns job_id immediately ──────────────────────────────────

@cbct_bp.route("/visits/<int:visit_id>/cbct", methods=["POST"])
def upload_cbct(visit_id):
    if "file" not in request.files:
        return jsonify({"error": "ZIP file required (field name: file)"}), 400

    zfile       = request.files["file"]
    uploaded_by = request.form.get("uploaded_by", "USER")
    notes       = request.form.get("notes", "")

    if not zfile.filename.lower().endswith(".zip"):
        return jsonify({"error": "Only .zip files are accepted"}), 400

    try:
        import pydicom  # noqa — check dep exists
        import numpy as np  # noqa
    except ImportError:
        return jsonify({"error": "Server missing deps — run: pip install pydicom numpy pillow"}), 500

    zip_bytes = zfile.read()
    if len(zip_bytes) > MAX_ZIP_BYTES:
        return jsonify({
            "error": f"ZIP too large. Max {MAX_ZIP_MB} MB "
                     f"(received {len(zip_bytes) // (1024*1024)} MB)"
        }), 413

    # Quick ZIP validity check before handing off to thread
    try:
        zipfile.ZipFile(io.BytesIO(zip_bytes)).close()
    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid or corrupted ZIP file"}), 400

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "queued", "volume_id": None, "error": None}

    from flask import current_app
    app = current_app._get_current_object()

    t = threading.Thread(
        target=_process_cbct,
        args=(app, job_id, visit_id, zip_bytes, uploaded_by, notes),
        daemon=True
    )
    t.start()

    # Return immediately — frontend polls /cbct/job/<job_id>
    return jsonify({
        "job_id":  job_id,
        "status":  "queued",
        "message": "Upload received. Processing in background — poll /api/cbct/job/<job_id> for status."
    }), 202


# ─── Job status poll endpoint ─────────────────────────────────────────────────

@cbct_bp.route("/cbct/job/<job_id>", methods=["GET"])
def job_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "job_id":    job_id,
        "status":    job["status"],      # queued | processing | done | error
        "volume_id": job["volume_id"],   # set when done
        "error":     job["error"],       # set when error
    })


# ─── List volumes for a visit ─────────────────────────────────────────────────

@cbct_bp.route("/visits/<int:visit_id>/cbct", methods=["GET"])
def list_cbct(visit_id):
    conn = db.engine.connect()
    try:
        rows = conn.execute(text("""
            SELECT id, patient_name, study_date, num_slices,
                   voxel_x, voxel_y, voxel_z, rows, cols,
                   uploaded_at, uploaded_by, notes
            FROM cbct_volumes WHERE visit_id = :vid
            ORDER BY uploaded_at DESC
        """), dict(vid=visit_id)).fetchall()
    finally:
        conn.close()

    return jsonify([{
        "id":           r[0],
        "patient_name": r[1],
        "study_date":   fmt_date(r[2], "%Y-%m-%d"),
        "num_slices":   r[3],
        "voxel_spacing":{"x": r[4], "y": r[5], "z": r[6]},
        "dimensions":   {"rows": r[7], "cols": r[8]},
        "uploaded_at":  fmt_date(r[9], "%d-%b-%Y %H:%M"),
        "uploaded_by":  r[10],
        "notes":        r[11],
    } for r in rows])


# ─── Volume metadata ──────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:volume_id>/meta", methods=["GET"])
def get_meta(volume_id):
    conn = db.engine.connect()
    try:
        r = conn.execute(text("""
            SELECT patient_name, study_date, num_slices,
                   voxel_x, voxel_y, voxel_z, rows, cols,
                   uploaded_at, notes, visit_id
            FROM cbct_volumes WHERE id = :vid
        """), dict(vid=volume_id)).fetchone()

        counts = conn.execute(text("""
            SELECT axis, COUNT(*) FROM cbct_slices
            WHERE volume_id = :vid GROUP BY axis
        """), dict(vid=volume_id)).fetchall()
    finally:
        conn.close()

    if not r:
        return jsonify({"error": "Volume not found"}), 404

    dim_map = {row[0]: row[1] for row in counts}
    return jsonify({
        "id":           volume_id,
        "visit_id":     r[10],
        "patient_name": r[0],
        "study_date":   fmt_date(r[1], "%Y-%m-%d"),
        "dimensions": {
            "axial":    dim_map.get("axial",    r[2]),
            "coronal":  dim_map.get("coronal",  r[7]),
            "sagittal": dim_map.get("sagittal", r[7]),
            "rows": r[6], "cols": r[7],
        },
        "voxel_spacing": {"x": r[3], "y": r[4], "z": r[5]},
        "uploaded_at":   fmt_date(r[8], "%d-%b-%Y %H:%M"),
        "notes":         r[9],
    })


# ─── Serve a single slice PNG ─────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:volume_id>/slice/<axis>/<int:index>", methods=["GET"])
def get_slice(volume_id, axis, index):
    if axis not in ("axial", "coronal", "sagittal"):
        return jsonify({"error": "axis must be axial | coronal | sagittal"}), 400

    conn = db.engine.connect()
    try:
        row = conn.execute(text("""
            SELECT png_data FROM cbct_slices
            WHERE volume_id = :vid AND axis = :ax AND index = :idx
        """), dict(vid=volume_id, ax=axis, idx=index)).fetchone()

        if not row:
            row = conn.execute(text("""
                SELECT png_data FROM cbct_slices
                WHERE volume_id = :vid AND axis = :ax
                ORDER BY ABS(index - :idx)
                LIMIT 1
            """), dict(vid=volume_id, ax=axis, idx=index)).fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "Slice not found"}), 404

    png_bytes = base64.b64decode(row[0])
    return Response(png_bytes, mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


# ─── Delete volume ────────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:volume_id>", methods=["DELETE"])
def delete_cbct(volume_id):
    conn = db.engine.connect()
    try:
        conn.execute(text("DELETE FROM cbct_slices  WHERE volume_id = :vid"), dict(vid=volume_id))
        conn.execute(text("DELETE FROM cbct_volumes WHERE id         = :vid"), dict(vid=volume_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "deleted"})


# ─── Annotations ─────────────────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:volume_id>/annotations", methods=["GET"])
def get_annotations(volume_id):
    conn = db.engine.connect()
    try:
        row = conn.execute(text(
            "SELECT data FROM cbct_annotations WHERE volume_id = :vid"
        ), dict(vid=volume_id)).fetchone()
    finally:
        conn.close()
    return jsonify(json.loads(row[0]) if row else {"measurements": [], "implants": [], "nerves": [], "texts": []})


@cbct_bp.route("/cbct/<int:volume_id>/annotations", methods=["PUT"])
def save_annotations(volume_id):
    data = request.get_json(force=True) or {}
    conn = db.engine.connect()
    try:
        conn.execute(text("""
            INSERT INTO cbct_annotations (volume_id, data, updated_at)
            VALUES (:vid, :d, NOW())
            ON CONFLICT (volume_id) DO UPDATE
              SET data = EXCLUDED.data, updated_at = NOW()
        """), dict(vid=volume_id, d=json.dumps(data)))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "saved"})


# ─── ZIP inspector (debug) ────────────────────────────────────────────────────

@cbct_bp.route("/cbct/inspect-zip", methods=["POST"])
def inspect_zip():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    zfile = request.files["file"]
    zb = zfile.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(zb))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    entries = zf.namelist()
    result = []
    for n in entries[:50]:
        info = zf.getinfo(n)
        result.append({"name": n, "size": info.file_size, "is_dir": n.endswith("/")})
    return jsonify({
        "total_entries": len(entries),
        "first_50": result,
        "all_names_sample": entries[:20],
    })