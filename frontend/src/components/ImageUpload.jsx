import { useEffect, useRef, useState } from "react";
import api from "../api/api";

/* ─── constants ─────────────────────────────────────────────── */
const IMAGE_TYPES = [
  { value: "IOPA",      label: "IOPA",            icon: "🦷", desc: "Intra-Oral Periapical" },
  { value: "OPG",       label: "OPG",             icon: "🦴", desc: "Orthopantomogram" },
  { value: "CBCT",      label: "CBCT",            icon: "🔬", desc: "Cone Beam CT" },
  { value: "INTRAORAL", label: "Intra Oral Image", icon: "📸", desc: "Intraoral Photo" },
];

const API_BASE = "https://dental-backend-xo1o.onrender.com";

function imgSrc(url) {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return `${API_BASE}${url}`;
}

function todayStr() { return new Date().toISOString().split("T")[0]; }
function fmtDate(d) {
  if (!d) return "—";
  const p = String(d).split("T")[0].split("-");
  return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : d;
}

/* ─── inject styles ─────────────────────────────────────────── */
const injectStyles = () => {
  if (document.getElementById("imgup-styles")) return;
  const s = document.createElement("style");
  s.id = "imgup-styles";
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');
    .imgup-root { font-family: 'Plus Jakarta Sans', sans-serif; }

    /* type selector cards */
    .imgup-type-card {
      flex: 1; min-width: 90px; padding: 10px 8px;
      border: 2px solid #e2e8f4; border-radius: 10px;
      background: #f8fafc; cursor: pointer;
      display: flex; flex-direction: column; align-items: center; gap: 4px;
      transition: all 0.18s; text-align: center;
    }
    .imgup-type-card:hover { border-color: #93c5fd; background: #eff6ff; }
    .imgup-type-card.selected { border-color: #1d6fa4; background: #eff6ff; box-shadow: 0 0 0 3px rgba(29,111,164,0.12); }

    /* drop zone */
    .imgup-dropzone {
      border: 2px dashed #c7d9f5; border-radius: 12px;
      background: #f8fafc; padding: 16px 20px;
      display: flex; flex-direction: column; align-items: center; gap: 8px;
      cursor: pointer; transition: all 0.18s;
    }
    .imgup-dropzone:hover, .imgup-dropzone.drag { border-color: #1d6fa4; background: #eff6ff; }
    .imgup-dropzone.has-file { border-color: #10b981; background: #f0fdf4; border-style: solid; }

    /* image cards in gallery */
    .imgup-img-card {
      background: #fff; border: 1.5px solid #e8eef8; border-radius: 12px;
      overflow: hidden; transition: box-shadow 0.18s, border-color 0.18s;
    }
    .imgup-img-card:hover { border-color: #c7d9fc; box-shadow: 0 4px 18px rgba(29,77,122,0.1); }

    /* lightbox */
    .imgup-lightbox {
      position: fixed; inset: 0; z-index: 9999;
      background: rgba(5,10,24,0.92); backdrop-filter: blur(8px);
      display: flex; align-items: center; justify-content: center;
      animation: imgup-fade 0.2s ease both;
    }
    @keyframes imgup-fade { from { opacity:0; } to { opacity:1; } }
    .imgup-lightbox-img {
      max-width: 90vw; max-height: 82vh;
      border-radius: 10px; box-shadow: 0 24px 80px rgba(0,0,0,0.7);
      transition: transform 0.2s ease;
      cursor: grab;
    }
    .imgup-lightbox-img:active { cursor: grabbing; }
    .imgup-lbox-btn {
      width: 40px; height: 40px; border-radius: 10px;
      border: 1.5px solid rgba(255,255,255,0.2);
      background: rgba(255,255,255,0.1);
      color: #fff; font-size: 18px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }
    .imgup-lbox-btn:hover { background: rgba(255,255,255,0.22); }

    /* upload modal overlay */
    .imgup-modal-overlay {
      position: fixed; inset: 0; z-index: 1000;
      background: rgba(10,25,55,0.5); backdrop-filter: blur(4px);
      display: flex; align-items: center; justify-content: center;
      animation: imgup-fade 0.2s ease both;
    }
    .imgup-modal {
      background: #fff; border-radius: 18px; padding: 28px 30px;
      width: 92%; max-width: 520px;
      max-height: 90vh; overflow-y: auto;
      box-shadow: 0 24px 80px rgba(10,25,55,0.25);
      animation: imgup-slide 0.25s cubic-bezier(.22,.68,0,1.2) both;
    }
    @keyframes imgup-slide { from { opacity:0; transform:translateY(18px) scale(0.97); } to { opacity:1; transform:none; } }

    /* edit modal */
    .imgup-edit-modal {
      background: #fff; border-radius: 18px; padding: 26px 28px;
      width: 92%; max-width: 460px;
      box-shadow: 0 24px 80px rgba(10,25,55,0.25);
      animation: imgup-slide 0.25s cubic-bezier(.22,.68,0,1.2) both;
    }

    /* section group heading */
    .imgup-section-hd {
      display: flex; align-items: center; gap: 8px;
      padding: 8px 14px; border-radius: 8px;
      margin: 18px 0 10px;
      background: linear-gradient(90deg, #eff6ff, transparent);
      border-left: 3px solid #1d6fa4;
      font-size: 12px; font-weight: 800; color: #0b2d4e;
      letter-spacing: 0.5px; text-transform: uppercase;
    }

    /* action buttons */
    .imgup-icon-btn {
      width: 30px; height: 30px; border-radius: 7px;
      border: 1.5px solid #e2e8f4; background: #f7f9fe;
      cursor: pointer; font-size: 13px;
      display: inline-flex; align-items: center; justify-content: center;
      transition: all 0.15s;
    }
    .imgup-icon-btn:hover { background: #eff4ff; border-color: #c7d9fc; }
    .imgup-icon-btn.danger:hover { background: #fff1f2; border-color: #fca5a5; }

    @keyframes imgup-spin { to { transform: rotate(360deg); } }
    .imgup-spinner {
      width: 16px; height: 16px; border-radius: 50%;
      border: 2px solid #dde8f8; border-top-color: #1d6fa4;
      animation: imgup-spin 0.7s linear infinite; display: inline-block;
    }
  `;
  document.head.appendChild(s);
};

/* ═══════════════════════════════════════════
   LIGHTBOX  — full-screen pan + zoom
═══════════════════════════════════════════ */
function Lightbox({ img, onClose }) {
  const MIN = 0.5, MAX = 8, STEP = 0.35;
  const [zoom,   setZoom]   = useState(1);
  const [pan,    setPan]    = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const dragRef  = useRef(null);   // { startX, startY, panX, panY }
  const stageRef = useRef(null);

  // reset pan when zoom goes back to 1
  const applyZoom = (next) => {
    const z = Math.min(Math.max(next, MIN), MAX);
    setZoom(z);
    if (z === 1) setPan({ x: 0, y: 0 });
  };

  // keyboard shortcuts
  useEffect(() => {
    const h = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "+" || e.key === "=") applyZoom(zoom + STEP);
      if (e.key === "-") applyZoom(zoom - STEP);
      if (e.key === "0") { setZoom(1); setPan({ x:0, y:0 }); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [zoom, onClose]);

  // wheel zoom centred on cursor
  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? STEP : -STEP;
    applyZoom(zoom + delta);
  };

  // attach wheel as non-passive so preventDefault works
  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  });

  // drag-to-pan
  const onMouseDown = (e) => {
    if (zoom <= 1) return;
    e.preventDefault();
    dragRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
    setDragging(true);
  };
  const onMouseMove = (e) => {
    if (!dragging || !dragRef.current) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    setPan({ x: dragRef.current.panX + dx, y: dragRef.current.panY + dy });
  };
  const onMouseUp = () => setDragging(false);

  const typeObj = IMAGE_TYPES.find(t => t.value === img.type) || { label: img.type };

  return (
    <div
      style={{
        position:"fixed", inset:0, zIndex:9999,
        background:"rgba(4,8,20,0.96)",
        display:"flex", flexDirection:"column",
        animation:"imgup-fade 0.18s ease both",
      }}
      onClick={onClose}
    >
      {/* ── Top bar ── */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          display:"flex", alignItems:"center", gap:8,
          padding:"12px 18px",
          background:"rgba(255,255,255,0.04)",
          borderBottom:"1px solid rgba(255,255,255,0.07)",
          flexShrink:0,
        }}
      >
        {/* Caption left */}
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ fontSize:13.5, fontWeight:700, color:"#fff", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
            {typeObj.label}
            {img.description && <span style={{ fontWeight:400, color:"rgba(255,255,255,0.6)", marginLeft:8 }}>{img.description}</span>}
          </div>
          {img.image_date && (
            <div style={{ fontSize:11.5, color:"rgba(255,255,255,0.4)", marginTop:2 }}>📅 {fmtDate(img.image_date)}</div>
          )}
        </div>

        {/* Controls right */}
        <div style={{ display:"flex", alignItems:"center", gap:6, flexShrink:0 }}>
          <button className="imgup-lbox-btn" onClick={() => applyZoom(zoom - STEP)} title="Zoom out (−)">−</button>
          <span style={{
            color:"#fff", fontSize:12, fontWeight:700,
            fontFamily:"'DM Mono',monospace",
            minWidth:48, textAlign:"center",
            background:"rgba(255,255,255,0.08)",
            borderRadius:7, padding:"4px 8px",
          }}>
            {Math.round(zoom * 100)}%
          </span>
          <button className="imgup-lbox-btn" onClick={() => applyZoom(zoom + STEP)} title="Zoom in (+)">+</button>
          <button className="imgup-lbox-btn" onClick={() => { setZoom(1); setPan({x:0,y:0}); }} title="Reset (0)"
            style={{ fontSize:11, fontWeight:800, letterSpacing:"-0.5px" }}>1:1</button>
          <div style={{ width:1, height:22, background:"rgba(255,255,255,0.15)", margin:"0 2px" }} />
          <button className="imgup-lbox-btn" onClick={onClose} title="Close (Esc)" style={{ fontSize:16 }}>✕</button>
        </div>
      </div>

      {/* ── Image stage — takes all remaining space ── */}
      <div
        ref={stageRef}
        onClick={e => e.stopPropagation()}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        style={{
          flex:1, overflow:"hidden",
          display:"flex", alignItems:"center", justifyContent:"center",
          cursor: zoom > 1 ? (dragging ? "grabbing" : "grab") : "default",
          userSelect:"none",
        }}
      >
        <img
          src={imgSrc(img.url)}
          alt={img.description || img.type}
          draggable={false}
          style={{
            maxWidth:"100%", maxHeight:"100%",
            objectFit:"contain",
            borderRadius: zoom === 1 ? 10 : 0,
            transform:`scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transformOrigin:"center center",
            transition: dragging ? "none" : "transform 0.15s ease",
            boxShadow: zoom === 1 ? "0 8px 40px rgba(0,0,0,0.6)" : "none",
            pointerEvents:"none",
          }}
        />
      </div>

      {/* ── Bottom hint ── */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          textAlign:"center", padding:"8px 0 10px",
          fontSize:11, color:"rgba(255,255,255,0.25)",
          flexShrink:0,
        }}
      >
        Scroll to zoom · Drag to pan · +/− keys · 0 to reset · Esc to close
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   UPLOAD MODAL — step 1: type select → step 2: file + details
═══════════════════════════════════════════ */
function UploadModal({ onClose, onUploaded, visitId }) {
  const [step,        setStep]        = useState(1);  // 1=type, 2=details
  const [selType,     setSelType]     = useState(null);
  const [file,        setFile]        = useState(null);
  const [preview,     setPreview]     = useState(null);
  const [description, setDescription] = useState("");
  const [imageDate,   setImageDate]   = useState(todayStr());
  const [drag,        setDrag]        = useState(false);
  const [uploading,   setUploading]   = useState(false);
  const fileRef = useRef();

  const pickFile = (f) => {
    if (!f) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = e => setPreview(e.target.result);
    reader.readAsDataURL(f);
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) pickFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("image",       file);
      fd.append("type",        selType);
      fd.append("description", description);
      fd.append("image_date",  imageDate);
      await api.post(`/visits/${visitId}/images`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onUploaded();
      onClose();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const selTypeObj = IMAGE_TYPES.find(t => t.value === selType);

  return (
    <div className="imgup-modal-overlay" onClick={onClose}>
      <div className="imgup-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
          <div>
            <div style={{ fontSize:16, fontWeight:800, color:"#0b2d4e" }}>
              {step === 1 ? "📂 Select Image Type" : `📸 Upload ${selTypeObj?.label}`}
            </div>
            <div style={{ fontSize:12, color:"#94a3b8", marginTop:2 }}>
              {step === 1 ? "Choose the category for this clinical image" : selTypeObj?.desc}
            </div>
          </div>
          <button onClick={onClose} style={{
            width:30, height:30, borderRadius:8, border:"1.5px solid #e2e8f4",
            background:"#f7f9fe", fontSize:15, cursor:"pointer",
            display:"flex", alignItems:"center", justifyContent:"center",
          }}>✕</button>
        </div>

        {/* ── STEP 1: type picker ── */}
        {step === 1 && (
          <>
            <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
              {IMAGE_TYPES.map(t => (
                <div
                  key={t.value}
                  className={`imgup-type-card ${selType===t.value ? "selected" : ""}`}
                  onClick={() => setSelType(t.value)}
                >
                  <span style={{ fontSize:22 }}>{t.icon}</span>
                  <span style={{ fontSize:12, fontWeight:700, color:"#0b2d4e" }}>{t.label}</span>
                  <span style={{ fontSize:10, color:"#94a3b8", lineHeight:1.3 }}>{t.desc}</span>
                </div>
              ))}
            </div>
            <button
              disabled={!selType}
              onClick={() => setStep(2)}
              style={{
                marginTop:20, width:"100%", padding:"12px 0", borderRadius:10,
                background: selType ? "linear-gradient(135deg,#1d4d7a,#1d6fa4)" : "#e2e8f0",
                color: selType ? "#fff" : "#94a3b8", border:"none",
                fontFamily:"'Plus Jakarta Sans',sans-serif",
                fontSize:14, fontWeight:700, cursor: selType ? "pointer" : "not-allowed",
              }}
            >
              Continue →
            </button>
          </>
        )}

        {/* ── STEP 2: file + details ── */}
        {step === 2 && (
          <>
            {/* Drop zone */}
            <div
              className={`imgup-dropzone ${drag ? "drag" : ""} ${file ? "has-file" : ""}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={handleDrop}
            >
              {preview ? (
                <img src={preview} alt="preview"
                  style={{ maxHeight:120, maxWidth:"100%", borderRadius:8, objectFit:"contain" }} />
              ) : (
                <>
                  <span style={{ fontSize:32 }}>🖼️</span>
                  <span style={{ fontSize:13.5, fontWeight:600, color:"#475569" }}>
                    Click or drag & drop an image
                  </span>
                  <span style={{ fontSize:11.5, color:"#94a3b8" }}>JPG, PNG, WEBP supported</span>
                </>
              )}
              <input ref={fileRef} type="file" accept="image/*" style={{ display:"none" }}
                onChange={e => pickFile(e.target.files?.[0])} />
            </div>
            {file && (
              <div style={{ fontSize:11.5, color:"#16a34a", fontWeight:600, marginTop:6, textAlign:"center" }}>
                ✓ {file.name}
              </div>
            )}

            {/* Date */}
            <div style={{ marginTop:14 }}>
              <label style={{ fontSize:10.5, fontWeight:700, color:"#8899bb", letterSpacing:"0.7px", textTransform:"uppercase", display:"block", marginBottom:5 }}>
                Image Date
              </label>
              <input type="date" value={imageDate} onChange={e => setImageDate(e.target.value)}
                style={{ width:"100%", padding:"9px 12px", border:"1.5px solid #e2e8f0", borderRadius:9,
                  fontFamily:"'DM Mono',monospace", fontSize:13, color:"#1e293b", background:"#f8fafc",
                  outline:"none", boxSizing:"border-box" }} />
            </div>

            {/* Description */}
            <div style={{ marginTop:12 }}>
              <label style={{ fontSize:10.5, fontWeight:700, color:"#8899bb", letterSpacing:"0.7px", textTransform:"uppercase", display:"block", marginBottom:5 }}>
                Description <span style={{ fontWeight:400, textTransform:"none", color:"#c0ccd8" }}>(optional)</span>
              </label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="e.g. Upper left molar region, post-RCT…"
                rows={3}
                style={{ width:"100%", padding:"9px 12px", border:"1.5px solid #e2e8f0", borderRadius:9,
                  fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:13, color:"#1e293b",
                  background:"#f8fafc", outline:"none", resize:"vertical", boxSizing:"border-box" }}
              />
            </div>

            {/* Actions */}
            <div style={{ display:"flex", gap:10, marginTop:18 }}>
              <button onClick={() => setStep(1)} style={{
                flex:1, padding:11, borderRadius:10, background:"transparent",
                color:"#64748b", border:"1.5px solid #e2e8f4",
                fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:13.5, fontWeight:600, cursor:"pointer",
              }}>← Back</button>
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                style={{
                  flex:2, padding:11, borderRadius:10,
                  background: (file && !uploading) ? "linear-gradient(135deg,#0d6e4a,#10b981)" : "#e2e8f0",
                  color: (file && !uploading) ? "#fff" : "#94a3b8", border:"none",
                  fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:14, fontWeight:700,
                  cursor: (file && !uploading) ? "pointer" : "not-allowed",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:8,
                }}
              >
                {uploading ? <><span className="imgup-spinner" /> Uploading…</> : "✓ Upload Image"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   EDIT MODAL
═══════════════════════════════════════════ */
function EditModal({ img, onClose, onSaved }) {
  const [description, setDescription] = useState(img.description || "");
  const [imageDate,   setImageDate]   = useState(img.image_date || todayStr());
  const [type,        setType]        = useState(img.type || "IOPA");
  const [saving,      setSaving]      = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/images/${img.id}`, { description, image_date: imageDate, type });
      onSaved();
      onClose();
    } catch (err) {
      console.error("Edit failed", err);
      alert("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="imgup-modal-overlay" onClick={onClose}>
      <div className="imgup-edit-modal" onClick={e => e.stopPropagation()}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:18 }}>
          <div style={{ fontSize:15, fontWeight:800, color:"#0b2d4e" }}>✏️ Edit Image Details</div>
          <button onClick={onClose} style={{
            width:28, height:28, borderRadius:7, border:"1.5px solid #e2e8f4",
            background:"#f7f9fe", fontSize:14, cursor:"pointer",
            display:"flex", alignItems:"center", justifyContent:"center",
          }}>✕</button>
        </div>

        {/* Type */}
        <div style={{ marginBottom:12 }}>
          <label style={{ fontSize:10.5, fontWeight:700, color:"#8899bb", letterSpacing:"0.7px", textTransform:"uppercase", display:"block", marginBottom:5 }}>Image Type</label>
          <select value={type} onChange={e => setType(e.target.value)}
            style={{ width:"100%", padding:"9px 12px", border:"1.5px solid #e2e8f0", borderRadius:9,
              fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:13, color:"#1e293b",
              background:"#f8fafc", outline:"none" }}>
            {IMAGE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label} — {t.desc}</option>)}
          </select>
        </div>

        {/* Date */}
        <div style={{ marginBottom:12 }}>
          <label style={{ fontSize:10.5, fontWeight:700, color:"#8899bb", letterSpacing:"0.7px", textTransform:"uppercase", display:"block", marginBottom:5 }}>Image Date</label>
          <input type="date" value={imageDate} onChange={e => setImageDate(e.target.value)}
            style={{ width:"100%", padding:"9px 12px", border:"1.5px solid #e2e8f0", borderRadius:9,
              fontFamily:"'DM Mono',monospace", fontSize:13, color:"#1e293b",
              background:"#f8fafc", outline:"none", boxSizing:"border-box" }} />
        </div>

        {/* Description */}
        <div style={{ marginBottom:18 }}>
          <label style={{ fontSize:10.5, fontWeight:700, color:"#8899bb", letterSpacing:"0.7px", textTransform:"uppercase", display:"block", marginBottom:5 }}>Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)}
            rows={3} placeholder="Image description…"
            style={{ width:"100%", padding:"9px 12px", border:"1.5px solid #e2e8f0", borderRadius:9,
              fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:13, color:"#1e293b",
              background:"#f8fafc", outline:"none", resize:"vertical", boxSizing:"border-box" }} />
        </div>

        <div style={{ display:"flex", gap:10 }}>
          <button onClick={onClose} style={{
            flex:1, padding:10, borderRadius:9, background:"transparent",
            color:"#64748b", border:"1.5px solid #e2e8f4",
            fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:13.5, fontWeight:600, cursor:"pointer",
          }}>Cancel</button>
          <button onClick={handleSave} disabled={saving} style={{
            flex:2, padding:10, borderRadius:9,
            background: saving ? "#e2e8f0" : "linear-gradient(135deg,#1d4d7a,#1d6fa4)",
            color: saving ? "#94a3b8" : "#fff", border:"none",
            fontFamily:"'Plus Jakarta Sans',sans-serif", fontSize:14, fontWeight:700,
            cursor: saving ? "not-allowed" : "pointer",
            display:"flex", alignItems:"center", justifyContent:"center", gap:8,
          }}>
            {saving ? <><span className="imgup-spinner" /> Saving…</> : "💾 Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   IMAGE CARD
═══════════════════════════════════════════ */
function ImageCard({ img, disabled, onEdit, onDelete, onView }) {
  const typeObj = IMAGE_TYPES.find(t => t.value === img.type) || { icon:"📄", label: img.type };
  return (
    <div className="imgup-img-card">
      {/* Thumbnail — click to open lightbox */}
      <div
        style={{ position:"relative", cursor:"zoom-in", background:"#0b1120", overflow:"hidden" }}
        onClick={() => onView(img)}
      >
        <img
          src={imgSrc(img.url)}
          alt={img.description || img.type}
          style={{ width:"100%", height:160, objectFit:"cover", display:"block",
            transition:"transform 0.22s", filter:"brightness(0.92)" }}
          onMouseOver={e => e.currentTarget.style.transform = "scale(1.04)"}
          onMouseOut={e  => e.currentTarget.style.transform = "scale(1)"}
        />
        <div style={{
          position:"absolute", top:8, left:8,
          background:"rgba(11,45,78,0.78)", backdropFilter:"blur(4px)",
          borderRadius:6, padding:"3px 9px",
          fontSize:11, fontWeight:700, color:"#fff", letterSpacing:"0.3px",
        }}>
          {typeObj.icon} {typeObj.label}
        </div>
        <div style={{
          position:"absolute", bottom:8, right:8,
          background:"rgba(0,0,0,0.55)", borderRadius:20,
          padding:"2px 8px", fontSize:10.5, color:"rgba(255,255,255,0.85)",
        }}>
          🔍 Click to zoom
        </div>
      </div>

      {/* Details */}
      <div style={{ padding:"10px 12px" }}>
        <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:8 }}>
          <div style={{ flex:1, minWidth:0 }}>
            {img.image_date && (
              <div style={{ fontSize:11, fontWeight:700, color:"#1d6fa4",
                fontFamily:"'DM Mono',monospace", marginBottom:3 }}>
                📅 {fmtDate(img.image_date)}
              </div>
            )}
            {img.description ? (
              <div style={{ fontSize:12.5, color:"#374151", lineHeight:1.5 }}>
                {img.description}
              </div>
            ) : (
              <div style={{ fontSize:12, color:"#cbd5e1", fontStyle:"italic" }}>No description</div>
            )}
            {img.uploaded_at && (
              <div style={{ fontSize:10.5, color:"#94a3b8", marginTop:4 }}>
                Uploaded: {img.uploaded_at}
              </div>
            )}
          </div>
          {!disabled && (
            <div style={{ display:"flex", gap:5, flexShrink:0 }}>
              <button className="imgup-icon-btn" onClick={() => onEdit(img)} title="Edit">✏️</button>
              <button className="imgup-icon-btn danger" onClick={() => onDelete(img)} title="Delete">🗑️</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════ */
export default function ImageUpload({ visitId, disabled = false }) {
  useEffect(() => { injectStyles(); }, []);

  const [images,      setImages]      = useState([]);
  const [loadingImgs, setLoadingImgs] = useState(false);
  const [showUpload,  setShowUpload]  = useState(false);
  const [lightbox,    setLightbox]    = useState(null);   // img object
  const [editImg,     setEditImg]     = useState(null);   // img object

  useEffect(() => {
    if (visitId) loadImages();
  }, [visitId]);

  const loadImages = async () => {
    setLoadingImgs(true);
    try {
      const res = await api.get(`/visits/${visitId}/images`);
      setImages(res.data || []);
    } catch (err) {
      console.error("Failed to load images", err);
    } finally {
      setLoadingImgs(false);
    }
  };

  const handleDelete = async (img) => {
    if (!window.confirm(`Delete this ${img.type} image? This cannot be undone.`)) return;
    try {
      await api.delete(`/images/${img.id}`);
      loadImages();
    } catch (err) {
      console.error("Delete failed", err);
      alert("Delete failed.");
    }
  };

  // Group images by type
  const grouped = IMAGE_TYPES.reduce((acc, t) => {
    const group = images.filter(img => img.type === t.value);
    if (group.length > 0) acc.push({ ...t, images: group });
    return acc;
  }, []);

  const inp = {
    fontFamily:"'Plus Jakarta Sans',sans-serif",
  };

  return (
    <div className="imgup-root">

      {/* ── Header ── */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:16 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:36, height:36, borderRadius:9, background:"linear-gradient(135deg,#dbeafe,#bfdbfe)",
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>🖼️</div>
          <div>
            <div style={{ fontSize:14, fontWeight:700, color:"#0b2d4e" }}>Clinical Images</div>
            <div style={{ fontSize:11.5, color:"#94a3b8" }}>
              {images.length} image{images.length !== 1 ? "s" : ""} · IOPA · OPG · CBCT · Intraoral
            </div>
          </div>
        </div>
        {!disabled && (
          <button
            onClick={() => setShowUpload(true)}
            style={{
              display:"inline-flex", alignItems:"center", gap:8,
              padding:"10px 20px", borderRadius:10,
              background:"linear-gradient(135deg,#1d4d7a,#1d6fa4)",
              color:"#fff", border:"none",
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              fontSize:13, fontWeight:700, cursor:"pointer",
              boxShadow:"0 4px 12px rgba(29,77,122,0.28)",
            }}
          >
            <span style={{ fontSize:16 }}>+</span> Upload Image
          </button>
        )}
      </div>

      {/* ── Loading ── */}
      {loadingImgs && (
        <div style={{ textAlign:"center", padding:"28px 0", color:"#94a3b8", fontSize:13 }}>
          <span className="imgup-spinner" style={{ marginRight:8 }} />
          Loading images…
        </div>
      )}

      {/* ── Empty state ── */}
      {!loadingImgs && images.length === 0 && (
        <div style={{
          textAlign:"center", padding:"40px 20px",
          background:"#fafbff", borderRadius:12,
          border:"1.5px dashed #dde8f8",
        }}>
          <div style={{ fontSize:40, marginBottom:10 }}>🦷</div>
          <div style={{ fontSize:14, fontWeight:600, color:"#475569", marginBottom:6 }}>
            No clinical images yet
          </div>
          <div style={{ fontSize:12.5, color:"#94a3b8", marginBottom:16 }}>
            Upload X-rays, OPGs, CBCTs or intraoral photos
          </div>
          {!disabled && (
            <button onClick={() => setShowUpload(true)} style={{
              padding:"10px 22px", borderRadius:10,
              background:"linear-gradient(135deg,#1d4d7a,#1d6fa4)",
              color:"#fff", border:"none",
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              fontSize:13, fontWeight:700, cursor:"pointer",
            }}>
              + Upload First Image
            </button>
          )}
        </div>
      )}

      {/* ── Grouped gallery ── */}
      {!loadingImgs && grouped.map(group => (
        <div key={group.value}>
          {/* Section heading */}
          <div className="imgup-section-hd">
            <span style={{ fontSize:16 }}>{group.icon}</span>
            {group.label}
            <span style={{
              marginLeft:"auto", fontSize:10, fontWeight:700,
              background:"#dbeafe", color:"#1d4ed8",
              borderRadius:20, padding:"1px 9px",
            }}>
              {group.images.length}
            </span>
          </div>

          {/* Grid */}
          <div style={{
            display:"grid",
            gridTemplateColumns:"repeat(auto-fill, minmax(200px, 1fr))",
            gap:12, marginBottom:8,
          }}>
            {group.images.map(img => (
              <ImageCard
                key={img.id}
                img={img}
                disabled={disabled}
                onView={setLightbox}
                onEdit={setEditImg}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </div>
      ))}

      {/* ── Modals ── */}
      {showUpload && (
        <UploadModal
          visitId={visitId}
          onClose={() => setShowUpload(false)}
          onUploaded={loadImages}
        />
      )}
      {editImg && (
        <EditModal
          img={editImg}
          onClose={() => setEditImg(null)}
          onSaved={loadImages}
        />
      )}
      {lightbox && (
        <Lightbox img={lightbox} onClose={() => setLightbox(null)} />
      )}
    </div>
  );
}