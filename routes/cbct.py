"""
routes/cbct.py
──────────────
CBCT Blueprint — handles ZIP upload, slice serving, annotations.

pip install pydicom numpy pillow
"""

from flask import Blueprint, request, jsonify, Response
import os, io, base64, zipfile, json, uuid, traceback
from datetime import datetime
from database import db
from sqlalchemy import text

cbct_bp = Blueprint("cbct", __name__)

# ── How many slices to skip between stored slices.
#    STEP=3 means store every 3rd slice → 66% fewer DB inserts.
#    Lower = more detail but slower upload. Raise to 4 or 5 for very large scans.
SLICE_STEP = 3

# ── Max ZIP size accepted (bytes). Reject early before reading into memory.
MAX_ZIP_MB  = 300
MAX_ZIP_BYTES = MAX_ZIP_MB * 1024 * 1024


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
    """Window-level a 2D float32 plane and return a base64-encoded PNG string."""
    from PIL import Image as PILImage
    clipped = plane_2d.clip(lo, hi)
    scaled  = ((clipped - lo) / max(hi - lo, 1.0) * 255).astype("uint8")
    buf     = io.BytesIO()
    PILImage.fromarray(scaled, mode="L").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ─── Upload ZIP ───────────────────────────────────────────────────────────────

@cbct_bp.route("/visits/<int:visit_id>/cbct", methods=["POST"])
def upload_cbct(visit_id):
    # ── Basic validation ──────────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "ZIP file required (field name: file)"}), 400

    zfile       = request.files["file"]
    uploaded_by = request.form.get("uploaded_by", "USER")
    notes       = request.form.get("notes", "")

    if not zfile.filename.lower().endswith(".zip"):
        return jsonify({"error": "Only .zip files are accepted"}), 400

    # ── Check deps ────────────────────────────────────────────────────────────
    try:
        import pydicom
        import numpy as np
    except ImportError:
        return jsonify({"error": "Server missing deps — run: pip install pydicom numpy pillow"}), 500

    try:
        # ── Read & size-guard the ZIP ─────────────────────────────────────────
        zip_bytes = zfile.read()
        if len(zip_bytes) > MAX_ZIP_BYTES:
            return jsonify({
                "error": f"ZIP too large. Max allowed: {MAX_ZIP_MB} MB "
                         f"(received {len(zip_bytes) // (1024*1024)} MB)"
            }), 413

        # ── Parse DICOM files from ZIP ────────────────────────────────────────
        try:
            zf_obj = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid or corrupted ZIP file"}), 400

        with zf_obj as zf:
            names = [
                n for n in zf.namelist()
                if not n.startswith("__MACOSX") and not n.endswith("/")
            ]
            dicom_files = []
            for name in names:
                raw = zf.read(name)
                try:
                    ds = pydicom.dcmread(io.BytesIO(raw))
                    if hasattr(ds, "pixel_array"):
                        dicom_files.append(ds)
                except Exception:
                    pass  # skip non-DICOM files silently

        if not dicom_files:
            return jsonify({"error": "No valid DICOM files found inside the ZIP"}), 400

        print(f"[cbct] visit={visit_id} — found {len(dicom_files)} DICOM files")

        # ── Sort slices by Z position ─────────────────────────────────────────
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

        # ── Extract metadata from first slice ─────────────────────────────────
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

        # ── Build 3-D volume ──────────────────────────────────────────────────
        print(f"[cbct] Building 3D volume from {len(dicom_files)} DICOM file(s)…")
        slices_arr = []
        for ds in dicom_files:
            arr = ds.pixel_array.astype(np.float32)
            slope     = float(getattr(ds, "RescaleSlope",     1))
            intercept = float(getattr(ds, "RescaleIntercept", 0))

            if arr.ndim == 2:
                # Standard single slice
                slices_arr.append(arr * slope + intercept)

            elif arr.ndim == 3:
                if arr.shape[2] in (3, 4):
                    # RGB/RGBA single frame → grayscale luminance
                    gray = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
                    slices_arr.append(gray * slope + intercept)
                else:
                    # Multi-frame DICOM — each frame is a separate slice
                    for frame in arr:
                        slices_arr.append(frame * slope + intercept)

            elif arr.ndim == 4:
                # Multi-frame RGB — (frames, Y, X, channels)
                for frame in arr:
                    if frame.shape[-1] in (3, 4):
                        gray = frame[..., 0] * 0.299 + frame[..., 1] * 0.587 + frame[..., 2] * 0.114
                    else:
                        gray = frame[..., 0]
                    slices_arr.append(gray * slope + intercept)

            else:
                # Fallback: flatten unknown dims → treat each sub-array as a slice
                flat = arr.reshape(-1, arr.shape[-2], arr.shape[-1])
                for frame in flat:
                    slices_arr.append(frame * slope + intercept)

        if not slices_arr:
            raise ValueError("No valid 2D slices could be extracted from DICOM files")

        print(f"[cbct] Extracted {len(slices_arr)} slices total")
        volume = np.stack(slices_arr, axis=0)   # shape: (Z, Y, X)
        Z, Y, X = volume.shape
        print(f"[cbct] Volume shape: Z={Z}, Y={Y}, X={X}")

        # Global windowing (computed once, reused for every slice)
        wc       = float(np.percentile(volume, 50))
        p2, p98  = float(np.percentile(volume, 2)), float(np.percentile(volume, 98))
        ww       = max(p98 - p2, 1.0)
        lo, hi   = wc - ww / 2, wc + ww / 2

        # ── Persist volume metadata ───────────────────────────────────────────
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
            print(f"[cbct] Created volume id={volume_id}")

            # ── Build slice rows with STEP sampling ───────────────────────────
            # STEP=3 → store indices 0, 3, 6, 9… per axis.
            # This reduces DB inserts by ~66% vs storing every slice.
            print(f"[cbct] Generating PNGs with SLICE_STEP={SLICE_STEP}…")

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

            print(f"[cbct] Inserting {len(slice_rows)} slice rows (batch)…")

            # ── Single batch INSERT — much faster than one INSERT per slice ───
            conn.execute(
                text("INSERT INTO cbct_slices (volume_id, axis, index, png_data) "
                     "VALUES (:vid, :ax, :i, :d)"),
                slice_rows          # SQLAlchemy executemany
            )

            # Update num_slices to reflect how many axial slices were actually stored
            stored_axial = len([r for r in slice_rows if r["ax"] == "axial"])
            conn.execute(
                text("UPDATE cbct_volumes SET num_slices = :n WHERE id = :vid"),
                dict(n=stored_axial, vid=volume_id)
            )
            conn.commit()
            print(f"[cbct] Done ✅ — {len(slice_rows)} slices stored")

        finally:
            conn.close()

        return jsonify({
            "id":            volume_id,
            "visit_id":      visit_id,
            "patient_name":  patient_name,
            "study_date":    study_date.strftime("%Y-%m-%d") if study_date else None,
            "num_slices":    stored_axial,
            "slice_step":    SLICE_STEP,
            "dimensions":    {"z": Z, "y": Y, "x": X},
            "voxel_spacing": {"x": vx, "y": vy, "z": vz},
            "message":       (
                f"Processed {stored_axial} axial + "
                f"{len([r for r in slice_rows if r['ax'] == 'coronal'])} coronal + "
                f"{len([r for r in slice_rows if r['ax'] == 'sagittal'])} sagittal slices "
                f"(every {SLICE_STEP}rd slice stored)"
            ),
        }), 201

    # ── Catch-all: log full traceback to Render logs, return readable error ───
    except MemoryError:
        print("[cbct] MemoryError — file too large for server RAM")
        return jsonify({"error": "File too large to process — server ran out of memory. Try a smaller scan."}), 507

    except Exception as e:
        print(f"[cbct] UNEXPECTED ERROR:\n{traceback.format_exc()}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


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
        "study_date":   r[2].strftime("%Y-%m-%d") if r[2] else None,
        "num_slices":   r[3],
        "voxel_spacing":{"x": r[4], "y": r[5], "z": r[6]},
        "dimensions":   {"rows": r[7], "cols": r[8]},
        "uploaded_at":  r[9].strftime("%d-%b-%Y %H:%M") if r[9] else None,
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
        "study_date":   r[1].strftime("%Y-%m-%d") if r[1] else None,
        "dimensions": {
            "axial":    dim_map.get("axial",    r[2]),
            "coronal":  dim_map.get("coronal",  r[7]),
            "sagittal": dim_map.get("sagittal", r[7]),
            "rows": r[6], "cols": r[7],
        },
        "voxel_spacing": {"x": r[3], "y": r[4], "z": r[5]},
        "uploaded_at":   r[8].strftime("%d-%b-%Y %H:%M") if r[8] else None,
        "notes":         r[9],
    })


# ─── Serve a single slice PNG ─────────────────────────────────────────────────

@cbct_bp.route("/cbct/<int:volume_id>/slice/<axis>/<int:index>", methods=["GET"])
def get_slice(volume_id, axis, index):
    if axis not in ("axial", "coronal", "sagittal"):
        return jsonify({"error": "axis must be axial | coronal | sagittal"}), 400

    conn = db.engine.connect()
    try:
        # ── Exact match first ─────────────────────────────────────────────────
        row = conn.execute(text("""
            SELECT png_data FROM cbct_slices
            WHERE volume_id = :vid AND axis = :ax AND index = :idx
        """), dict(vid=volume_id, ax=axis, idx=index)).fetchone()

        # ── If exact index wasn't stored (due to STEP sampling),
        #    return the nearest stored slice instead of a 404 ─────────────────
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