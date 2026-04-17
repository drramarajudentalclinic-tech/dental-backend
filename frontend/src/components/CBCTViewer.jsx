/**
 * CBCTViewer.jsx
 *
 * Full-featured CBCT viewer — drop-in React component.
 *
 * Props:
 *   volumeId   {number}   CBCT volume ID from the DB
 *   volumeMeta {object}   Meta object from GET /api/cbct/:id/meta  (optional, fetched if omitted)
 *   apiBase    {string}   e.g. "/api"  (default "/api")
 *   onClose    {function} Called when user clicks ✕
 *
 * Usage:
 *   <CBCTViewer volumeId={42} onClose={() => setOpen(false)} />
 */

import React, {
  useState, useEffect, useRef, useCallback, useMemo
} from "react";

// ─── Constants ────────────────────────────────────────────────────────────────

const AXES = ["axial", "coronal", "sagittal"];
const AXIS_LABELS = { axial: "Axial (Z)", coronal: "Coronal (Y)", sagittal: "Sagittal (X)" };
const AXIS_COLORS = { axial: "#22d3ee", coronal: "#f97316", sagittal: "#a78bfa" };

const TOOLS = [
  { id: "pan",      icon: "✋", label: "Pan" },
  { id: "window",   icon: "☀️", label: "Window / Level" },
  { id: "measure",  icon: "📏", label: "Measure Distance" },
  { id: "angle",    icon: "📐", label: "Measure Angle" },
  { id: "implant",  icon: "🦷", label: "Place Implant" },
  { id: "nerve",    icon: "🧠", label: "Trace Nerve (IAN)" },
  { id: "annotate", icon: "✏️", label: "Annotate" },
  { id: "roi",      icon: "⬜", label: "ROI / Crop" },
  { id: "probe",    icon: "🔬", label: "HU Probe" },
  { id: "erase",    icon: "🗑️", label: "Erase" },
];

const DEFAULT_WW = 3000;
const DEFAULT_WC = 400;

const WINDOW_PRESETS = [
  { label: "Bone",        wc:  400, ww: 1500 },
  { label: "Soft Tissue", wc:   40, ww:  400 },
  { label: "Enamel",      wc: 2500, ww: 4000 },
  { label: "Airway",      wc: -800, ww: 1000 },
  { label: "Full Range",  wc:  400, ww: 4000 },
];

const IMPLANT_SYSTEMS = [
  { brand: "Nobel Active",  lengths: [8,10,11.5,13,15,18], diameters: [3.0,3.5,4.3,5.0] },
  { brand: "Straumann BL",  lengths: [8,10,12,14,16],      diameters: [3.3,4.1,4.8,6.5] },
  { brand: "Zimmer TSV",    lengths: [8,10,11.5,13,16],    diameters: [3.7,4.7,5.7]     },
  { brand: "Generic",       lengths: [8,10,11,13,15,18],   diameters: [3.0,3.5,4.0,4.5,5.0] },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function dist2D(a, b) { return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2); }
function angleDeg(a, b, c) {
  const ab = { x: a.x - b.x, y: a.y - b.y };
  const cb = { x: c.x - b.x, y: c.y - b.y };
  const dot = ab.x * cb.x + ab.y * cb.y;
  const cross = Math.abs(ab.x * cb.y - ab.y * cb.x);
  return (Math.atan2(cross, dot) * 180) / Math.PI;
}

function getToken() {
  return localStorage.getItem("token") || sessionStorage.getItem("token") || "";
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token
    ? { Authorization: `Bearer ${token}`, ...extra }
    : { ...extra };
}

// ─── Slice Panel ──────────────────────────────────────────────────────────────

function SlicePanel({
  axis, volumeId, sliceIndex, totalSlices,
  wc, ww, apiBase,
  tool, zoom, pan,
  crosshair,
  onCrosshairChange,
  annotations, onAnnotationAdd,
  onSliceChange,
  onWindowChange,
  onPanChange,
  onZoomChange,
  active, onActivate,
}) {
  const canvasRef  = useRef(null);
  const imgRef     = useRef(new window.Image());
  const dragRef    = useRef(null);
  const annPtsRef  = useRef([]);

  const sliceUrl = useMemo(() =>
    `${apiBase}/cbct/${volumeId}/slice/${axis}/${sliceIndex}`,
    [apiBase, volumeId, axis, sliceIndex]
  );

  useEffect(() => {
    const img = imgRef.current;
    img.crossOrigin = "anonymous";
    // Attach token as query param since img.src doesn't support headers
    const token = getToken();
    img.src = token ? `${sliceUrl}?token=${token}` : sliceUrl;
    img.onload = () => render();
  }, [sliceUrl]);

  useEffect(() => { render(); }, [wc, ww, zoom, pan, crosshair, annotations, sliceIndex]);

  function render() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);

    const img = imgRef.current;
    if (img.complete && img.naturalWidth) {
      const sw = W * zoom, sh = H * zoom;
      const sx = (W - sw) / 2 + pan.x;
      const sy = (H - sh) / 2 + pan.y;
      ctx.drawImage(img, sx, sy, sw, sh);
    }

    if (crosshair) {
      const cx = crosshair.x * W, cy = crosshair.y * H;
      ctx.strokeStyle = AXIS_COLORS[axis] + "99";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, H); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(W, cy); ctx.stroke();
      ctx.setLineDash([]);
    }

    drawAnnotations(ctx, W, H, annotations, axis);

    if (annPtsRef.current.length > 0) {
      drawInProgress(ctx, annPtsRef.current, tool);
    }

    ctx.fillStyle = AXIS_COLORS[axis];
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.fillText(AXIS_LABELS[axis].toUpperCase(), 8, 20);
    ctx.fillStyle = "#fff8";
    ctx.font = "10px monospace";
    ctx.fillText(`${sliceIndex + 1} / ${totalSlices}`, 8, 36);
    ctx.fillText(`WC:${wc} WW:${ww}`, 8, 52);
  }

  function drawAnnotations(ctx, W, H, annotations, axis) {
    const axisAnns = annotations.filter(a => a.axis === axis);
    for (const ann of axisAnns) {
      if (ann.type === "measure") {
        const p1 = { x: ann.p1.x * W, y: ann.p1.y * H };
        const p2 = { x: ann.p2.x * W, y: ann.p2.y * H };
        ctx.strokeStyle = "#fde68a"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
        ctx.fillStyle = "#fde68a";
        ctx.beginPath(); ctx.arc(p1.x, p1.y, 3, 0, 2 * Math.PI); ctx.fill();
        ctx.beginPath(); ctx.arc(p2.x, p2.y, 3, 0, 2 * Math.PI); ctx.fill();
        const mid = { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
        ctx.font = "11px monospace"; ctx.fillStyle = "#fde68a";
        ctx.fillText(`${ann.mm.toFixed(1)} mm`, mid.x + 4, mid.y - 4);
      }
      if (ann.type === "angle") {
        const pts = ann.points.map(p => ({ x: p.x * W, y: p.y * H }));
        ctx.strokeStyle = "#86efac"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[1].x, pts[1].y); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(pts[1].x, pts[1].y); ctx.lineTo(pts[2].x, pts[2].y); ctx.stroke();
        pts.forEach(p => { ctx.fillStyle="#86efac"; ctx.beginPath(); ctx.arc(p.x,p.y,3,0,2*Math.PI); ctx.fill(); });
        ctx.font = "11px monospace"; ctx.fillStyle = "#86efac";
        ctx.fillText(`${ann.deg.toFixed(1)}°`, pts[1].x + 6, pts[1].y - 6);
      }
      if (ann.type === "implant" && ann.axis === axis) {
        const cx = ann.cx * W, cy = ann.cy * H;
        const r  = (ann.diameter / 2) * zoom * 10;
        const h  = ann.length * zoom * 10;
        ctx.strokeStyle = "#60a5fa"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(cx, cy, r, h / 2, ann.angleDeg * Math.PI / 180, 0, 2 * Math.PI); ctx.stroke();
        ctx.fillStyle = "#60a5fa44"; ctx.fill();
        ctx.fillStyle = "#60a5fa"; ctx.font = "10px monospace";
        ctx.fillText(`${ann.brand} Ø${ann.diameter}×${ann.length}mm`, cx + r + 4, cy);
      }
      if (ann.type === "nerve") {
        const pts = ann.points.map(p => ({ x: p.x * W, y: p.y * H }));
        ctx.strokeStyle = "#f9a8d4"; ctx.lineWidth = 2;
        ctx.setLineDash([3, 2]);
        ctx.beginPath();
        pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
        ctx.stroke(); ctx.setLineDash([]);
        pts.forEach(p => { ctx.fillStyle="#f9a8d4"; ctx.beginPath(); ctx.arc(p.x,p.y,2.5,0,2*Math.PI); ctx.fill(); });
      }
      if (ann.type === "text") {
        ctx.fillStyle = "#fbbf24"; ctx.font = "12px sans-serif";
        ctx.fillText(ann.text, ann.x * W, ann.y * H);
      }
    }
  }

  function drawInProgress(ctx, pts, tool) {
    if (pts.length === 0) return;
    const canvas = canvasRef.current;
    const W = canvas.width, H = canvas.height;
    if (tool === "measure" && pts.length === 1) {
      ctx.strokeStyle = "#fde68a88"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(pts[0].x * W, pts[0].y * H, 4, 0, 2 * Math.PI); ctx.stroke();
    }
    if (tool === "nerve" && pts.length > 1) {
      ctx.strokeStyle = "#f9a8d488"; ctx.lineWidth = 1.5; ctx.setLineDash([3,2]);
      ctx.beginPath();
      pts.forEach((p, i) => i===0 ? ctx.moveTo(p.x*W, p.y*H) : ctx.lineTo(p.x*W, p.y*H));
      ctx.stroke(); ctx.setLineDash([]);
    }
  }

  function canvasPos(e) {
    const r = canvasRef.current.getBoundingClientRect();
    return {
      x: clamp((e.clientX - r.left) / r.width,  0, 1),
      y: clamp((e.clientY - r.top)  / r.height, 0, 1),
    };
  }

  function onMouseDown(e) {
    onActivate();
    e.preventDefault();
    const pos = canvasPos(e);
    dragRef.current = { startPos: pos, startPan: { ...pan }, button: e.button, lastPos: pos };

    if (tool === "measure") {
      if (annPtsRef.current.length === 0) {
        annPtsRef.current = [pos];
      } else {
        const p1 = annPtsRef.current[0];
        const mm = dist2D(p1, pos) * 200;
        onAnnotationAdd({ type: "measure", axis, p1, p2: pos, mm });
        annPtsRef.current = [];
      }
      render(); return;
    }
    if (tool === "angle") {
      annPtsRef.current.push(pos);
      if (annPtsRef.current.length === 3) {
        const [a, b, c] = annPtsRef.current;
        onAnnotationAdd({ type: "angle", axis, points: [a, b, c], deg: angleDeg(a, b, c) });
        annPtsRef.current = [];
      }
      render(); return;
    }
    if (tool === "nerve") {
      annPtsRef.current.push(pos);
      render(); return;
    }
  }

  function onMouseMove(e) {
    const d = dragRef.current;
    if (!d || !e.buttons) return;
    const pos = canvasPos(e);
    const dx = pos.x - d.lastPos.x;
    const dy = pos.y - d.lastPos.y;
    d.lastPos = pos;

    if (tool === "pan" || e.buttons === 4) {
      const canvas = canvasRef.current;
      onPanChange({ x: pan.x + dx * canvas.width, y: pan.y + dy * canvas.height });
      return;
    }
    if (tool === "window") {
      onWindowChange(clamp(wc + dy * 800, -2000, 4000), clamp(ww + dx * 800, 1, 8000));
      return;
    }
    onCrosshairChange(pos);
    render();
  }

  function onMouseUp(e) {
    const d = dragRef.current;
    if (!d) return;
    const pos = canvasPos(e);
    if (tool === "implant") onAnnotationAdd({ type: "implant_request", axis, cx: pos.x, cy: pos.y });
    if (tool === "probe")   onAnnotationAdd({ type: "probe", axis, x: pos.x, y: pos.y, hu: "~"+Math.round(wc) });
    dragRef.current = null;
  }

  function onWheel(e) {
    e.preventDefault();
    if (e.ctrlKey) {
      onZoomChange(clamp(zoom * (e.deltaY > 0 ? 0.9 : 1.1), 0.3, 8));
    } else {
      onSliceChange(clamp(sliceIndex + (e.deltaY > 0 ? 1 : -1), 0, totalSlices - 1));
    }
  }

  function onDoubleClick() {
    if (tool === "nerve" && annPtsRef.current.length > 1) {
      onAnnotationAdd({ type: "nerve", axis, points: [...annPtsRef.current] });
      annPtsRef.current = [];
      render();
    }
  }

  const PANEL_SIZE = 380;

  return (
    <div style={{
      position: "relative",
      border: active ? `2px solid ${AXIS_COLORS[axis]}` : "2px solid #1e293b",
      borderRadius: 6, overflow: "hidden",
      cursor: tool === "pan" ? "grab" : tool === "window" ? "ew-resize" : "crosshair",
      background: "#000", flex: "1 1 0", minWidth: 280,
    }}>
      <canvas
        ref={canvasRef}
        width={PANEL_SIZE} height={PANEL_SIZE}
        style={{ display: "block", width: "100%", height: "100%" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onWheel={onWheel}
        onDoubleClick={onDoubleClick}
        onContextMenu={e => e.preventDefault()}
      />
      <input
        type="range" min={0} max={totalSlices - 1} value={sliceIndex}
        onChange={e => onSliceChange(Number(e.target.value))}
        style={{
          position: "absolute", bottom: 6, left: 8, right: 8,
          width: "calc(100% - 16px)",
          accentColor: AXIS_COLORS[axis], opacity: 0.7,
        }}
      />
    </div>
  );
}

// ─── Implant Dialog ───────────────────────────────────────────────────────────

function ImplantDialog({ request, onConfirm, onCancel }) {
  const [system,   setSystem]   = useState(0);
  const [length,   setLength]   = useState(10);
  const [diameter, setDiameter] = useState(4.0);
  const [angle,    setAngle]    = useState(0);
  const sys = IMPLANT_SYSTEMS[system];

  return (
    <div style={styles.modal}>
      <div style={styles.modalBox}>
        <h3 style={{ color: "#60a5fa", margin: "0 0 16px", fontFamily: "monospace" }}>
          🦷 Place Implant
        </h3>
        <label style={styles.label}>System</label>
        <select style={styles.select} value={system} onChange={e => setSystem(+e.target.value)}>
          {IMPLANT_SYSTEMS.map((s, i) => <option key={i} value={i}>{s.brand}</option>)}
        </select>
        <label style={styles.label}>Length (mm)</label>
        <select style={styles.select} value={length} onChange={e => setLength(+e.target.value)}>
          {sys.lengths.map(l => <option key={l} value={l}>{l} mm</option>)}
        </select>
        <label style={styles.label}>Diameter (mm)</label>
        <select style={styles.select} value={diameter} onChange={e => setDiameter(+e.target.value)}>
          {sys.diameters.map(d => <option key={d} value={d}>{d} mm</option>)}
        </select>
        <label style={styles.label}>Angle (°): {angle}°</label>
        <input type="range" min={-45} max={45} value={angle}
          onChange={e => setAngle(+e.target.value)}
          style={{ width: "100%", accentColor: "#60a5fa" }}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          <button style={styles.btnPrimary} onClick={() =>
            onConfirm({ brand: sys.brand, length, diameter, angleDeg: angle, ...request })
          }>Place</button>
          <button style={styles.btnSecondary} onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ─── Main CBCTViewer ──────────────────────────────────────────────────────────

export default function CBCTViewer({ volumeId, volumeMeta: initialMeta, apiBase = "/api", onClose }) {

  const [meta,        setMeta]        = useState(initialMeta || null);
  const [loading,     setLoading]     = useState(!initialMeta);
  const [error,       setError]       = useState(null);

  const [tool,        setTool]        = useState("pan");
  const [wc,          setWc]          = useState(DEFAULT_WC);
  const [ww,          setWw]          = useState(DEFAULT_WW);
  const [zoom,        setZoom]        = useState(1);
  const [pans,        setPans]        = useState({ axial:{x:0,y:0}, coronal:{x:0,y:0}, sagittal:{x:0,y:0} });
  const [activeAxis,  setActiveAxis]  = useState("axial");
  const [layout,      setLayout]      = useState("3up");
  const [showInfo,    setShowInfo]    = useState(false);
  const [showAnnot,   setShowAnnot]   = useState(true);
  const [annotations, setAnnotations] = useState([]);
  const [implantReq,  setImplantReq]  = useState(null);
  const [saved,       setSaved]       = useState(false);

  const [crosshair, setCrosshair] = useState({
    axial:    {x:0.5,y:0.5},
    coronal:  {x:0.5,y:0.5},
    sagittal: {x:0.5,y:0.5},
  });
  const [slices, setSlices] = useState({ axial: 0, coronal: 0, sagittal: 0 });

  const dims = meta ? {
    axial:    meta.dimensions?.axial    || meta.dimensions?.rows || 100,
    coronal:  meta.dimensions?.coronal  || meta.dimensions?.cols || 100,
    sagittal: meta.dimensions?.sagittal || meta.dimensions?.cols || 100,
  } : { axial: 100, coronal: 100, sagittal: 100 };

  // ── Load meta ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (meta) return;
    fetch(`${apiBase}/cbct/${volumeId}/meta`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { setMeta(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [volumeId]);

  // ── Load annotations ─────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${apiBase}/cbct/${volumeId}/annotations`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        const all = [
          ...(d.measurements || []),
          ...(d.implants     || []),
          ...(d.nerves       || []),
          ...(d.texts        || []),
        ];
        setAnnotations(all);
      })
      .catch(() => {});
  }, [volumeId]);

  // ── Save annotations ──────────────────────────────────────────────────────
  const saveAnnotations = useCallback(async () => {
    const body = {
      measurements: annotations.filter(a => a.type === "measure" || a.type === "angle"),
      implants:     annotations.filter(a => a.type === "implant"),
      nerves:       annotations.filter(a => a.type === "nerve"),
      texts:        annotations.filter(a => a.type === "text"),
    };
    await fetch(`${apiBase}/cbct/${volumeId}/annotations`, {
      method: "PUT",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }, [annotations, volumeId, apiBase]);

  // ── Annotation handler ────────────────────────────────────────────────────
  const handleAnnotationAdd = useCallback((ann) => {
    if (ann.type === "implant_request") { setImplantReq(ann); return; }
    setAnnotations(prev => [...prev, { ...ann, id: Date.now() }]);
  }, []);

  const handleImplantConfirm = useCallback((imp) => {
    setAnnotations(prev => [...prev, { ...imp, type: "implant", id: Date.now() }]);
    setImplantReq(null);
  }, []);

  const handleWindowChange = useCallback((newWc, newWw) => {
    setWc(Math.round(newWc));
    setWw(Math.round(newWw));
  }, []);

  // ── Crosshair sync ────────────────────────────────────────────────────────
  const handleCrosshair = useCallback((axis, pos) => {
    setCrosshair(prev => ({ ...prev, [axis]: pos }));
    if (axis === "axial") {
      setSlices(prev => ({
        ...prev,
        coronal:  Math.round(pos.y * dims.coronal),
        sagittal: Math.round(pos.x * dims.sagittal),
      }));
    }
    if (axis === "coronal") {
      setSlices(prev => ({
        ...prev,
        axial:    Math.round(pos.y * dims.axial),
        sagittal: Math.round(pos.x * dims.sagittal),
      }));
    }
    if (axis === "sagittal") {
      setSlices(prev => ({
        ...prev,
        axial:   Math.round(pos.y * dims.axial),
        coronal: Math.round(pos.x * dims.coronal),
      }));
    }
  }, [dims]);

  // ── Reset ─────────────────────────────────────────────────────────────────
  const resetView = () => {
    setWc(DEFAULT_WC); setWw(DEFAULT_WW); setZoom(1);
    setPans({ axial:{x:0,y:0}, coronal:{x:0,y:0}, sagittal:{x:0,y:0} });
    setSlices({ axial: 0, coronal: 0, sagittal: 0 });
    setCrosshair({ axial:{x:0.5,y:0.5}, coronal:{x:0.5,y:0.5}, sagittal:{x:0.5,y:0.5} });
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(annotations, null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `cbct_${volumeId}_annotations.json`; a.click();
  };

  const exportScreenshot = () => {
    const canvases = document.querySelectorAll(".cbct-canvas");
    if (!canvases.length) return;
    const combined = document.createElement("canvas");
    combined.width = canvases[0].width * canvases.length;
    combined.height = canvases[0].height;
    const ctx = combined.getContext("2d");
    canvases.forEach((c, i) => ctx.drawImage(c, i * c.width, 0));
    const a = document.createElement("a"); a.href = combined.toDataURL("image/png");
    a.download = `cbct_${volumeId}_screenshot.png`; a.click();
  };

  const visibleAxes = layout === "3up" ? AXES : [layout];

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────

  if (loading) return (
    <div style={styles.fullScreen}>
      <div style={{ color: "#60a5fa", fontFamily: "monospace", fontSize: 18 }}>
        ⏳ Loading CBCT volume…
      </div>
    </div>
  );

  if (error) return (
    <div style={styles.fullScreen}>
      <div style={{ color: "#f87171", fontFamily: "monospace" }}>❌ {error}</div>
      <button style={styles.btnSecondary} onClick={onClose}>Close</button>
    </div>
  );

  return (
    <>
      <style>{CSS}</style>
      <div style={styles.root}>

        {/* ── Top bar ─────────────────────────────── */}
        <div style={styles.topBar}>
          <div style={styles.topLeft}>
            <span style={styles.logo}>🦷 CBCT Viewer</span>
            {meta && (
              <span style={styles.patientChip}>
                {meta.patient_name}
                {meta.study_date && ` · ${meta.study_date}`}
                {` · ${meta.dimensions?.axial || "?"} slices`}
              </span>
            )}
          </div>

          <div style={styles.topCenter}>
            {["3up", "axial", "coronal", "sagittal"].map(l => (
              <button key={l}
                style={{ ...styles.layoutBtn, ...(layout === l ? styles.layoutBtnActive : {}) }}
                onClick={() => setLayout(l)}
              >
                {l === "3up" ? "⊞" : l === "axial" ? "⬛" : l === "coronal" ? "◼" : "▪"}
                {" " + l.charAt(0).toUpperCase() + l.slice(1, l === "3up" ? 3 : 4)}
              </button>
            ))}
          </div>

          <div style={styles.topRight}>
            <button style={styles.iconBtn} onClick={resetView}       title="Reset View">↺</button>
            <button style={styles.iconBtn} onClick={exportScreenshot} title="Screenshot">📷</button>
            <button style={styles.iconBtn} onClick={exportJSON}       title="Export Annotations">💾</button>
            <button style={styles.iconBtn} onClick={saveAnnotations}  title="Save to Server">
              {saved ? "✅" : "🔒"}
            </button>
            <button style={styles.iconBtn} onClick={() => setShowInfo(i => !i)} title="Info">ℹ️</button>
            <button style={{ ...styles.iconBtn, color: "#f87171" }} onClick={onClose} title="Close">✕</button>
          </div>
        </div>

        {/* ── Main area ────────────────────────────── */}
        <div style={styles.main}>

          {/* ── Toolbar ── */}
          <div style={styles.toolbar}>
            <div style={styles.toolSection}>
              {TOOLS.map(t => (
                <button key={t.id}
                  style={{ ...styles.toolBtn, ...(tool === t.id ? styles.toolBtnActive : {}) }}
                  onClick={() => setTool(t.id)}
                  title={t.label}
                >
                  <span style={{ fontSize: 18 }}>{t.icon}</span>
                  <span style={{ fontSize: 9, marginTop: 2, opacity: 0.7 }}>{t.label.split(" ")[0]}</span>
                </button>
              ))}
            </div>

            <div style={styles.toolDivider} />

            <div style={{ padding: "0 4px" }}>
              <div style={styles.sectionLabel}>PRESETS</div>
              {WINDOW_PRESETS.map(p => (
                <button key={p.label} style={styles.presetBtn}
                  onClick={() => { setWc(p.wc); setWw(p.ww); }}
                >{p.label}</button>
              ))}
            </div>

            <div style={styles.toolDivider} />

            <div style={{ padding: "0 4px" }}>
              <div style={styles.sectionLabel}>WINDOW</div>
              <div style={styles.sliderRow}>
                <span style={styles.sliderLabel}>WC</span>
                <input type="range" min={-2000} max={4000} value={wc}
                  onChange={e => setWc(+e.target.value)}
                  style={{ flex: 1, accentColor: "#22d3ee" }}
                />
                <span style={styles.sliderVal}>{wc}</span>
              </div>
              <div style={styles.sliderRow}>
                <span style={styles.sliderLabel}>WW</span>
                <input type="range" min={1} max={8000} value={ww}
                  onChange={e => setWw(+e.target.value)}
                  style={{ flex: 1, accentColor: "#22d3ee" }}
                />
                <span style={styles.sliderVal}>{ww}</span>
              </div>
              <div style={styles.sliderRow}>
                <span style={styles.sliderLabel}>Zoom</span>
                <input type="range" min={30} max={800} value={Math.round(zoom * 100)}
                  onChange={e => setZoom(+e.target.value / 100)}
                  style={{ flex: 1, accentColor: "#a78bfa" }}
                />
                <span style={styles.sliderVal}>{Math.round(zoom * 100)}%</span>
              </div>
            </div>

            <div style={styles.toolDivider} />

            <div style={{ padding: "0 4px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={styles.sectionLabel}>ANNOTATIONS</div>
                <button style={styles.tinyBtn} onClick={() => setShowAnnot(p => !p)}>
                  {showAnnot ? "Hide" : "Show"}
                </button>
              </div>
              {showAnnot && annotations.slice(-8).map((a, i) => (
                <div key={a.id || i} style={styles.annotRow}>
                  <span style={{ opacity: 0.6, fontSize: 10 }}>
                    {a.type === "measure"  ? `📏 ${a.mm?.toFixed(1)} mm (${a.axis})` :
                     a.type === "angle"    ? `📐 ${a.deg?.toFixed(1)}° (${a.axis})` :
                     a.type === "implant"  ? `🦷 ${a.brand} Ø${a.diameter}×${a.length}mm` :
                     a.type === "nerve"    ? `🧠 IAN Trace (${a.axis})` :
                     a.type === "probe"    ? `🔬 HU: ${a.hu}` :
                     a.type}
                  </span>
                  <button style={styles.tinyBtn} onClick={() =>
                    setAnnotations(prev => prev.filter((_, j) => j !== annotations.length - 8 + i))
                  }>✕</button>
                </div>
              ))}
              {annotations.length > 8 && (
                <div style={{ fontSize: 9, opacity: 0.4, padding: "2px 0" }}>+{annotations.length - 8} more</div>
              )}
              {annotations.length === 0 && (
                <div style={{ fontSize: 9, opacity: 0.3, padding: "4px 0" }}>No annotations yet</div>
              )}
            </div>

            <div style={styles.toolDivider} />

            <div style={{ padding: "0 4px" }}>
              <div style={styles.sectionLabel}>IMPLANTS</div>
              {annotations.filter(a => a.type === "implant").map((imp, i) => (
                <div key={i} style={{ fontSize: 9, color: "#93c5fd", margin: "2px 0" }}>
                  #{i+1} {imp.brand}<br />Ø{imp.diameter} × {imp.length}mm @ {imp.angleDeg}°
                </div>
              ))}
              {!annotations.find(a => a.type === "implant") && (
                <div style={{ fontSize: 9, opacity: 0.3 }}>Use Implant tool to plan</div>
              )}
            </div>
          </div>

          {/* ── Viewports ── */}
          <div style={{ ...styles.viewports, flexDirection: layout === "3up" ? "row" : "column" }}>
            {visibleAxes.map(axis => (
              <SlicePanel
                key={axis}
                axis={axis}
                volumeId={volumeId}
                sliceIndex={slices[axis]}
                totalSlices={dims[axis]}
                wc={wc} ww={ww}
                apiBase={apiBase}
                tool={tool}
                zoom={zoom}
                pan={pans[axis]}
                crosshair={crosshair[axis]}
                onCrosshairChange={pos => handleCrosshair(axis, pos)}
                annotations={showAnnot ? annotations : []}
                onAnnotationAdd={handleAnnotationAdd}
                onSliceChange={idx => setSlices(prev => ({ ...prev, [axis]: idx }))}
                onWindowChange={handleWindowChange}
                onPanChange={newPan => setPans(prev => ({ ...prev, [axis]: newPan }))}
                onZoomChange={setZoom}
                active={activeAxis === axis}
                onActivate={() => setActiveAxis(axis)}
              />
            ))}
          </div>
        </div>

        {/* ── Status bar ─────────────────────────── */}
        <div style={styles.statusBar}>
          <span>Tool: <b style={{ color: "#22d3ee" }}>{TOOLS.find(t=>t.id===tool)?.label}</b></span>
          <span>Slices: Ax {slices.axial+1}/{dims.axial} · Co {slices.coronal+1}/{dims.coronal} · Sa {slices.sagittal+1}/{dims.sagittal}</span>
          <span>WC:{wc} WW:{ww} · Zoom:{Math.round(zoom*100)}%</span>
          <span style={{ opacity: 0.4 }}>Scroll=slice · Ctrl+Scroll=zoom · Drag(window tool)=W/L</span>
        </div>

        {/* ── Info panel overlay ─────────────────── */}
        {showInfo && meta && (
          <div style={styles.infoPanel}>
            <button style={{ ...styles.iconBtn, position: "absolute", top: 8, right: 8 }}
              onClick={() => setShowInfo(false)}>✕</button>
            <h3 style={{ color: "#60a5fa", fontFamily: "monospace", margin: "0 0 12px" }}>Volume Info</h3>
            {[
              ["Patient",         meta.patient_name],
              ["Study Date",      meta.study_date],
              ["Axial Slices",    meta.dimensions?.axial],
              ["Coronal Slices",  meta.dimensions?.coronal],
              ["Sagittal Slices", meta.dimensions?.sagittal],
              ["Rows × Cols",     `${meta.dimensions?.rows} × ${meta.dimensions?.cols}`],
              ["Voxel X",         `${meta.voxel_spacing?.x?.toFixed(3)} mm`],
              ["Voxel Y",         `${meta.voxel_spacing?.y?.toFixed(3)} mm`],
              ["Voxel Z",         `${meta.voxel_spacing?.z?.toFixed(3)} mm`],
              ["Uploaded",        meta.uploaded_at],
              ["Notes",           meta.notes],
            ].map(([k, v]) => v ? (
              <div key={k} style={{ display: "flex", gap: 12, marginBottom: 6 }}>
                <span style={{ color: "#64748b", fontSize: 11, width: 110, flexShrink: 0 }}>{k}</span>
                <span style={{ color: "#e2e8f0", fontSize: 11 }}>{v}</span>
              </div>
            ) : null)}
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #1e293b" }}>
              <div style={styles.sectionLabel}>NERVE SAFETY REMINDER</div>
              <p style={{ fontSize: 10, color: "#fbbf24", margin: "4px 0 0" }}>
                Always verify IAN canal tracing with clinical judgment.
                Maintain ≥2 mm safety margin from identified nerve canal.
              </p>
            </div>
          </div>
        )}

        {/* ── Implant dialog ─────────────────────── */}
        {implantReq && (
          <ImplantDialog
            request={implantReq}
            onConfirm={handleImplantConfirm}
            onCancel={() => setImplantReq(null)}
          />
        )}
      </div>
    </>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = {
  root:         { position: "fixed", inset: 0, zIndex: 9999, background: "#020617", display: "flex", flexDirection: "column", fontFamily: "'JetBrains Mono', 'Fira Code', monospace", color: "#e2e8f0" },
  fullScreen:   { position: "fixed", inset: 0, zIndex: 9999, background: "#020617", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 },
  topBar:       { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 16px", background: "#0f172a", borderBottom: "1px solid #1e293b", flexShrink: 0, gap: 12 },
  topLeft:      { display: "flex", alignItems: "center", gap: 12, minWidth: 0 },
  logo:         { color: "#60a5fa", fontWeight: 700, fontSize: 14, whiteSpace: "nowrap" },
  patientChip:  { background: "#1e293b", color: "#94a3b8", fontSize: 11, padding: "3px 10px", borderRadius: 12, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  topCenter:    { display: "flex", gap: 4 },
  topRight:     { display: "flex", gap: 6, alignItems: "center" },
  layoutBtn:    { background: "#1e293b", color: "#64748b", border: "1px solid #334155", borderRadius: 4, padding: "4px 10px", fontSize: 11, cursor: "pointer", transition: "all 0.15s" },
  layoutBtnActive: { background: "#1d4ed8", color: "#fff", borderColor: "#3b82f6" },
  iconBtn:      { background: "transparent", color: "#94a3b8", border: "none", cursor: "pointer", fontSize: 15, padding: "4px 6px", borderRadius: 4, transition: "color 0.15s" },
  main:         { display: "flex", flex: 1, overflow: "hidden" },
  toolbar:      { width: 148, flexShrink: 0, background: "#0f172a", borderRight: "1px solid #1e293b", overflowY: "auto", display: "flex", flexDirection: "column", gap: 0, padding: "8px 0" },
  toolSection:  { display: "flex", flexDirection: "column", gap: 2, padding: "0 4px" },
  toolBtn:      { display: "flex", flexDirection: "column", alignItems: "center", background: "transparent", border: "1px solid transparent", borderRadius: 6, padding: "6px 4px", cursor: "pointer", color: "#94a3b8", transition: "all 0.15s" },
  toolBtnActive:{ background: "#1e3a5f", borderColor: "#3b82f6", color: "#60a5fa" },
  toolDivider:  { height: 1, background: "#1e293b", margin: "8px 8px" },
  sectionLabel: { fontSize: 9, color: "#475569", letterSpacing: 1, marginBottom: 4, paddingLeft: 2 },
  presetBtn:    { display: "block", width: "100%", textAlign: "left", background: "transparent", border: "none", color: "#94a3b8", padding: "3px 4px", fontSize: 11, cursor: "pointer", borderRadius: 4, transition: "background 0.1s" },
  sliderRow:    { display: "flex", alignItems: "center", gap: 4, marginBottom: 4 },
  sliderLabel:  { fontSize: 9, color: "#64748b", width: 22, flexShrink: 0 },
  sliderVal:    { fontSize: 9, color: "#94a3b8", width: 34, textAlign: "right", flexShrink: 0 },
  annotRow:     { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "2px 0", borderBottom: "1px solid #0f172a" },
  tinyBtn:      { background: "transparent", border: "none", color: "#475569", cursor: "pointer", fontSize: 10, padding: "0 2px" },
  viewports:    { flex: 1, display: "flex", gap: 4, padding: 4, overflow: "hidden" },
  statusBar:    { display: "flex", gap: 24, alignItems: "center", padding: "5px 16px", background: "#0f172a", borderTop: "1px solid #1e293b", fontSize: 10, color: "#475569", flexShrink: 0 },
  modal:        { position: "absolute", inset: 0, background: "#00000099", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 },
  modalBox:     { background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: 24, minWidth: 280, boxShadow: "0 20px 60px #0008" },
  label:        { display: "block", fontSize: 11, color: "#64748b", marginBottom: 4, marginTop: 12 },
  select:       { width: "100%", background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", padding: "6px 8px", borderRadius: 6, fontSize: 12 },
  btnPrimary:   { flex: 1, background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "8px 16px", cursor: "pointer", fontSize: 13 },
  btnSecondary: { flex: 1, background: "#1e293b", color: "#94a3b8", border: "1px solid #334155", borderRadius: 6, padding: "8px 16px", cursor: "pointer", fontSize: 13 },
  infoPanel:    { position: "absolute", top: 56, right: 16, width: 300, background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: 20, zIndex: 50, boxShadow: "0 20px 60px #0008" },
};

const CSS = `
  .cbct-canvas { display: block; width: 100%; height: 100%; }
  input[type=range] { height: 4px; }
  button:hover { opacity: 0.85; }
  ::-webkit-scrollbar { width: 4px; background: #0f172a; }
  ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }
`;