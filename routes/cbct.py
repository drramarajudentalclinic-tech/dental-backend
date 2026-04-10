"""
routes/cbct.py
──────────────
CBCT Blueprint — handles ZIP upload, slice serving, annotations.

pip install pydicom numpy pillow
"""

from flask import Blueprint, request, jsonify, Response
import os, io, base64, zipfile, json, uuid
from datetime import datetime
from database import db
from sqlalchemy import text

cbct_bp = Blueprint("cbct", __name__)


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
                    notes         TEXT
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


# ─── Upload ZIP ───────────────────────────────────────────────────────────────

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
        import pydicom
        import numpy as np
        from PIL import Image as PILImage
    except ImportError:
        return jsonify({"error": "Server missing deps — run: pip install pydicom numpy pillow"}), 500

    # ── Read ZIP ──────────────────────────────────────────────────────────────
    zip_bytes = zfile.read()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = [n for n in zf.namelist() if not n.startswith("__MACOSX") and not n.endswith("/")]
        dicom_files = []
        for name in names:
            raw = zf.read(name)
            try:
                ds = pydicom.dcmread(io.BytesIO(raw))
                if hasattr(ds, "pixel_array"):
                    dicom_files.append(ds)
            except Exception:
                pass

    if not dicom_files:
        return jsonify({"error": "No valid DICOM files found inside the ZIP"}), 400

    # ── Sort slices ───────────────────────────────────────────────────────────
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

    # ── Metadata ──────────────────────────────────────────────────────────────
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

    # ── Build 3-D volume ──────────────────────────────────────────────────────
    slices_arr = []
    for ds in dicom_files:
        arr       = ds.pixel_array.astype(np.float32)
        slope     = float(getattr(ds, "RescaleSlope",     1))
        intercept = float(getattr(ds, "RescaleIntercept", 0))
        slices_arr.append(arr * slope + intercept)

    volume = np.stack(slices_arr, axis=0)   # (Z, Y, X)
    Z, Y, X = volume.shape

    # Global window
    wc = float(np.percentile(volume, 50))
    p2, p98 = np.percentile(volume, 2), np.percentile(volume, 98)
    ww = max(float(p98 - p2), 1.0)

    def to_png_b64(plane_2d):
        lo, hi  = wc - ww / 2, wc + ww / 2
        clipped = np.clip(plane_2d, lo, hi)
        scaled  = ((clipped - lo) / (hi - lo) * 255).astype(np.uint8)
        img     = PILImage.fromarray(scaled, mode="L")
        buf     = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # ── Persist ───────────────────────────────────────────────────────────────
    conn = db.engine.connect()
    try:
        res = conn.execute(text("""
            INSERT INTO cbct_volumes
              (visit_id, patient_name, study_date, series_uid,
               num_slices, voxel_x, voxel_y, voxel_z,
               rows, cols, uploaded_by, notes)
            VALUES
              (:vid, :pn, :sd, :uid,
               :ns, :vx, :vy, :vz,
               :rows, :cols, :ub, :notes)
            RETURNING id
        """), dict(vid=visit_id, pn=patient_name, sd=study_date, uid=series_uid,
                   ns=Z, vx=vx, vy=vy, vz=vz, rows=rows, cols=cols,
                   ub=uploaded_by, notes=notes))
        volume_id = res.fetchone()[0]
        conn.commit()

        for i in range(Z):
            conn.execute(text(
                "INSERT INTO cbct_slices (volume_id, axis, index, png_data) VALUES (:vid,'axial',:i,:d)"
            ), dict(vid=volume_id, i=i, d=to_png_b64(volume[i, :, :])))

        for i in range(Y):
            conn.execute(text(
                "INSERT INTO cbct_slices (volume_id, axis, index, png_data) VALUES (:vid,'coronal',:i,:d)"
            ), dict(vid=volume_id, i=i, d=to_png_b64(volume[:, i, :])))

        for i in range(X):
            conn.execute(text(
                "INSERT INTO cbct_slices (volume_id, axis, index, png_data) VALUES (:vid,'sagittal',:i,:d)"
            ), dict(vid=volume_id, i=i, d=to_png_b64(volume[:, :, i])))

        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "id":           volume_id,
        "visit_id":     visit_id,
        "patient_name": patient_name,
        "study_date":   study_date.strftime("%Y-%m-%d") if study_date else None,
        "num_slices":   Z,
        "dimensions":   {"z": Z, "y": Y, "x": X},
        "voxel_spacing":{"x": vx, "y": vy, "z": vz},
        "message":      f"Processed {Z} axial + {Y} coronal + {X} sagittal slices",
    }), 201


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
        row = conn.execute(text("""
            SELECT png_data FROM cbct_slices
            WHERE volume_id = :vid AND axis = :ax AND index = :idx
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