/**
 * CBCTSection.jsx
 *
 * Fixes applied:
 *   1. API returns { cbct_files: [...], visit_id } — unwrapped correctly
 *   2. "View CBCT" opens CBCTViewer in a new fullscreen browser tab
 *   3. JWT token attached to all fetch calls
 */

import React, { useState, useEffect, useRef, useCallback } from "react";

const API = "/api";

function getToken() {
  return localStorage.getItem("token") || sessionStorage.getItem("token") || "";
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra };
}

export default function CBCTSection({ visitId, apiBase = API }) {
  const [volumes,   setVolumes]   = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadPct, setUploadPct] = useState(0);
  const [uploadMsg, setUploadMsg] = useState("");
  const [error,     setError]     = useState(null);
  const [dragOver,  setDragOver]  = useState(false);
  const fileRef = useRef(null);

  // ── Load volumes ─────────────────────────────────────────────────────────
  const loadVolumes = useCallback(() => {
    setLoading(true);
    fetch(`${apiBase}/visits/${visitId}/cbct`, { headers: authHeaders() })
      .then(r => r.json())
      .then(data => {
        // Backend returns { cbct_files: [...], visit_id } OR a plain array
        const list = Array.isArray(data)
          ? data
          : Array.isArray(data.cbct_files)
            ? data.cbct_files
            : [];
        setVolumes(list);
        setLoading(false);
      })
      .catch(() => { setError("Failed to load CBCT volumes"); setLoading(false); });
  }, [visitId, apiBase]);

  useEffect(() => { loadVolumes(); }, [loadVolumes]);

  // ── Open viewer in new tab ────────────────────────────────────────────────
  const openViewer = (volumeId) => {
    localStorage.setItem("cbct_viewer_params", JSON.stringify({ volumeId, apiBase }));
    window.open(
      `${window.location.origin}/cbct-viewer?volumeId=${volumeId}`,
      "_blank",
      "noopener"
    );
  };

  // ── Upload ────────────────────────────────────────────────────────────────
  const doUpload = useCallback(async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setError("Please select a .zip file containing DICOM files.");
      return;
    }
    setError(null);
    setUploading(true);
    setUploadPct(5);
    setUploadMsg("Uploading ZIP\u2026");

    const form = new FormData();
    form.append("file", file);
    form.append("uploaded_by", "USER");

    try {
      const interval = setInterval(() => {
        setUploadPct(p => {
          if (p >= 85) { clearInterval(interval); return p; }
          return p + Math.random() * 12;
        });
        setUploadMsg(prev =>
          prev.includes("DICOM")   ? "Generating coronal & sagittal slices\u2026" :
          prev.includes("coronal") ? "Storing volume in database\u2026" :
          "Processing DICOM stack\u2026"
        );
      }, 800);

      const res = await fetch(`${apiBase}/visits/${visitId}/cbct`, {
        method: "POST",
        headers: authHeaders(),
        body: form,
      });
      clearInterval(interval);

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Upload failed");
      }

      const data = await res.json();
      const numSlices = data.cbct?.num_slices ?? data.num_slices ?? "?";
      setUploadPct(100);
      setUploadMsg(`Done! ${numSlices} axial slices processed.`);
      setTimeout(() => {
        setUploading(false);
        setUploadPct(0);
        setUploadMsg("");
        loadVolumes();
      }, 1500);
    } catch (e) {
      setError(e.message);
      setUploading(false);
      setUploadPct(0);
    }
  }, [visitId, apiBase, loadVolumes]);

  // ── Delete ────────────────────────────────────────────────────────────────
  const deleteVolume = async (id) => {
    if (!window.confirm("Delete this CBCT volume? This cannot be undone.")) return;
    await fetch(`${apiBase}/cbct/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    loadVolumes();
  };

  // ── Drag & drop ───────────────────────────────────────────────────────────
  const onDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) doUpload(file);
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={s.root}>

      <div
        style={{ ...s.dropZone, ...(dragOver ? s.dropZoneActive : {}) }}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => !uploading && fileRef.current?.click()}
      >
        <input
          ref={fileRef} type="file" accept=".zip"
          style={{ display: "none" }}
          onChange={e => doUpload(e.target.files[0])}
        />

        {uploading ? (
          <div style={s.uploadProgress}>
            <div style={s.progressBar}>
              <div style={{ ...s.progressFill, width: `${uploadPct}%` }} />
            </div>
            <p style={s.uploadMsg}>{uploadMsg}</p>
            <p style={s.uploadSub}>{Math.round(uploadPct)}% complete</p>
          </div>
        ) : (
          <>
            <div style={s.dropIcon}>🗜️</div>
            <p style={s.dropTitle}>Upload CBCT ZIP</p>
            <p style={s.dropSub}>
              Drop your DICOM ZIP file here, or click to browse.
              <br />
              <span style={{ opacity: 0.5 }}>Axial · Coronal · Sagittal slices will be auto-generated.</span>
            </p>
          </>
        )}
      </div>

      {error && (
        <div style={s.errorBox}>
          <span>⚠️ {error}</span>
          <button style={s.clearBtn} onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div style={s.listHeader}>
        <h3 style={s.listTitle}>CBCT Volumes</h3>
        <button style={s.refreshBtn} onClick={loadVolumes}>↺ Refresh</button>
      </div>

      {loading ? (
        <div style={s.empty}>Loading…</div>
      ) : volumes.length === 0 ? (
        <div style={s.empty}>No CBCT volumes yet. Upload a ZIP file above to get started.</div>
      ) : (
        <div style={s.list}>
          {volumes.map(vol => (
            <div key={vol.id} style={s.volCard}>
              <div style={s.volIcon}>🦷</div>
              <div style={s.volInfo}>
                <div style={s.volName}>
                  {vol.patient_name || "CBCT Volume"}
                  <span style={s.volBadge}>{vol.num_slices} slices</span>
                </div>
                <div style={s.volMeta}>
                  {vol.study_date && <span>📅 {vol.study_date}</span>}
                  {vol.study_date && <span>·</span>}
                  <span>
                    {vol.dimensions?.rows} × {vol.dimensions?.cols} px
                    {vol.voxel_spacing?.x ? ` · ${vol.voxel_spacing.x.toFixed(2)} mm/vx` : ""}
                  </span>
                  <span>·</span>
                  <span>⬆ {vol.uploaded_at}</span>
                </div>
                {vol.notes && <div style={s.volNotes}>{vol.notes}</div>}
              </div>
              <div style={s.volActions}>
                <button style={s.openBtn} onClick={() => openViewer(vol.id)}>
                  🖥️ View CBCT
                </button>
                <button style={s.delBtn} onClick={() => deleteVolume(vol.id)} title="Delete volume">
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={s.legend}>
        {[
          ["🧠", "Axial / Coronal / Sagittal MPR"],
          ["🖱️", "Scroll to navigate slices"],
          ["☀️", "Window / Level adjustment"],
          ["📏", "Distance & angle measurement"],
          ["🦷", "Implant planning (Nobel, Straumann…)"],
          ["🧠", "IAN nerve tracing"],
          ["🔬", "HU density probe"],
          ["💾", "Save annotations to server"],
        ].map(([icon, label]) => (
          <div key={label} style={s.legendItem}>
            <span>{icon}</span>
            <span style={{ opacity: 0.6, fontSize: 11 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const BLUE   = "#3b82f6";
const DARK   = "#0f172a";
const BORDER = "#1e293b";

const s = {
  root:          { display: "flex", flexDirection: "column", gap: 16, fontFamily: "system-ui, sans-serif" },
  dropZone:      { border: `2px dashed ${BORDER}`, borderRadius: 12, padding: "32px 24px", textAlign: "center", cursor: "pointer", background: "#f8fafc08", transition: "all 0.2s", userSelect: "none" },
  dropZoneActive:{ borderColor: BLUE, background: "#1d4ed811" },
  dropIcon:      { fontSize: 40, marginBottom: 8 },
  dropTitle:     { fontSize: 16, fontWeight: 600, color: "#e2e8f0", margin: "0 0 8px" },
  dropSub:       { fontSize: 13, color: "#64748b", margin: 0, lineHeight: 1.7 },
  uploadProgress:{ width: "100%" },
  progressBar:   { height: 6, background: BORDER, borderRadius: 4, overflow: "hidden", marginBottom: 12 },
  progressFill:  { height: "100%", background: BLUE, transition: "width 0.4s ease", borderRadius: 4 },
  uploadMsg:     { color: "#60a5fa", fontSize: 14, margin: "0 0 4px", fontWeight: 500 },
  uploadSub:     { color: "#64748b", fontSize: 12, margin: 0 },
  errorBox:      { display: "flex", justifyContent: "space-between", alignItems: "center", background: "#450a0a", border: "1px solid #7f1d1d", borderRadius: 8, padding: "10px 14px", color: "#fca5a5", fontSize: 13 },
  clearBtn:      { background: "transparent", border: "none", color: "#fca5a5", cursor: "pointer", fontSize: 16, padding: 0 },
  listHeader:    { display: "flex", justifyContent: "space-between", alignItems: "center" },
  listTitle:     { margin: 0, fontSize: 15, fontWeight: 600, color: "#e2e8f0" },
  refreshBtn:    { background: "transparent", border: `1px solid ${BORDER}`, color: "#64748b", padding: "4px 10px", borderRadius: 6, fontSize: 12, cursor: "pointer" },
  empty:         { color: "#475569", fontSize: 13, textAlign: "center", padding: "24px 0" },
  list:          { display: "flex", flexDirection: "column", gap: 8 },
  volCard:       { display: "flex", alignItems: "center", gap: 14, background: DARK, border: `1px solid ${BORDER}`, borderRadius: 10, padding: "14px 16px", transition: "border-color 0.15s" },
  volIcon:       { fontSize: 28, flexShrink: 0 },
  volInfo:       { flex: 1, minWidth: 0 },
  volName:       { fontSize: 14, fontWeight: 600, color: "#e2e8f0", display: "flex", alignItems: "center", gap: 8, marginBottom: 4 },
  volBadge:      { background: "#1d4ed8", color: "#93c5fd", fontSize: 10, padding: "2px 8px", borderRadius: 10 },
  volMeta:       { display: "flex", gap: 6, flexWrap: "wrap", color: "#64748b", fontSize: 11 },
  volNotes:      { color: "#475569", fontSize: 11, marginTop: 4, fontStyle: "italic" },
  volActions:    { display: "flex", gap: 8, flexShrink: 0 },
  openBtn:       { background: BLUE, color: "#fff", border: "none", borderRadius: 8, padding: "8px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", transition: "opacity 0.15s" },
  delBtn:        { background: "transparent", border: `1px solid ${BORDER}`, color: "#64748b", borderRadius: 8, padding: "8px 10px", fontSize: 14, cursor: "pointer" },
  legend:        { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, padding: "12px 16px", background: "#f8fafc04", border: `1px solid ${BORDER}`, borderRadius: 10, marginTop: 4 },
  legendItem:    { display: "flex", gap: 8, alignItems: "center" },
};