import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";

/* ═══════════════════════════════════════════
   APPOINTMENTS PAGE
   Route: /reception/appointments
   Standalone full-page component — no wrapper needed.
   Navbar: Dashboard · New Patient · Find Patient ·
           Appointments (active) · Prescriptions · Doctor View
═══════════════════════════════════════════ */

/* ── Fonts + Global styles ── */
const GlobalStyles = () => {
  const id = "appt-page-styles";
  if (typeof document !== "undefined" && !document.getElementById(id)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap";
    document.head.appendChild(link);

    const style = document.createElement("style");
    style.id = id;
    style.textContent = `
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      /* ════════════════════════════════════
         NAVBAR — sticky, responsive
      ════════════════════════════════════ */
      .ap-navbar {
        background: linear-gradient(90deg, #0a2540, #0f3d6e);
        border-bottom: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
        position: sticky; top: 0; z-index: 200;
      }
      .ap-navbar-inner {
        max-width: 1100px; margin: 0 auto;
        padding: 0 12px;
        display: flex; align-items: stretch;
        overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none;
      }
      .ap-navbar-inner::-webkit-scrollbar { display: none; }

      .ap-nav-btn {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 0 15px; height: 48px;
        color: rgba(255,255,255,0.55);
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 12.5px; font-weight: 600;
        border: none; background: transparent; cursor: pointer;
        border-bottom: 2.5px solid transparent;
        transition: color 0.18s, border-color 0.18s, background 0.18s;
        white-space: nowrap; flex-shrink: 0;
        text-decoration: none; letter-spacing: 0.15px;
      }
      .ap-nav-btn:hover  { color: #fff; background: rgba(255,255,255,0.06); }
      .ap-nav-btn.active { color: #fff; border-bottom-color: #38bdf8; background: rgba(56,189,248,0.09); }

      .ap-nav-badge {
        display: inline-flex; align-items: center; justify-content: center;
        min-width: 17px; height: 17px; padding: 0 4px;
        border-radius: 9px; font-size: 10px; font-weight: 800;
        background: #ef4444; color: #fff;
      }

      /* Hide emoji on phones but keep text */
      @media (max-width: 500px) {
        .ap-nav-btn   { padding: 0 11px; font-size: 12px; }
        .ap-nav-emoji { display: none; }
      }

      /* ════════════════════════════════════
         STAT PILLS in hero
      ════════════════════════════════════ */
      .ap-stat-pill {
        display: flex; align-items: center; gap: 8px;
        padding: 7px 16px;
        background: rgba(255,255,255,0.11);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
      }

      /* ════════════════════════════════════
         FILTER CONTROLS
      ════════════════════════════════════ */
      .ap-filter-wrap {
        display: flex; gap: 10px; align-items: center;
        flex-wrap: wrap; margin-bottom: 20px;
      }
      .ap-filter-label {
        font-size: 11px; font-weight: 700; color: #8899bb;
        letter-spacing: 0.8px; text-transform: uppercase;
      }
      .ap-filter-input, .ap-filter-select {
        padding: 8px 12px;
        border: 1.5px solid #e2e8f4; border-radius: 9px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 12.5px; color: #1a1f36; background: #f7f9fe;
        outline: none; cursor: pointer;
        transition: border-color 0.2s;
      }
      .ap-filter-input:focus,
      .ap-filter-select:focus { border-color: #1d6fa4; box-shadow: 0 0 0 3px rgba(29,111,164,0.09); }

      /* ════════════════════════════════════
         TAB BAR
      ════════════════════════════════════ */
      .ap-tab-bar {
        display: flex; border-bottom: 2px solid #f0f4fb; margin-bottom: 20px; gap: 2px;
      }
      .ap-tab {
        padding: 10px 18px; border: none; background: transparent;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px; font-weight: 600; color: #94a3b8;
        cursor: pointer; border-bottom: 2.5px solid transparent;
        margin-bottom: -2px; transition: all 0.18s; border-radius: 6px 6px 0 0;
        white-space: nowrap;
      }
      .ap-tab:hover  { color: #1d6fa4; background: #f0f8ff; }
      .ap-tab.active { color: #1d4d7a; border-bottom-color: #1d6fa4; background: #f0f8ff; }
      .ap-tab-count {
        margin-left: 6px; font-size: 10.5px; font-weight: 700;
        padding: 1px 7px; border-radius: 20px;
      }

      /* ════════════════════════════════════
         APPOINTMENT CARD
      ════════════════════════════════════ */
      .ap-card {
        border: 1.5px solid #e8eef8; border-radius: 12px;
        padding: 14px 18px; background: #fff;
        transition: box-shadow 0.18s, border-color 0.18s;
        position: relative; overflow: hidden;
      }
      .ap-card:hover { border-color: #c7d9fc; box-shadow: 0 4px 16px rgba(29,77,122,0.09); }
      .ap-card::before {
        content: ''; position: absolute; left: 0; top: 0; bottom: 0;
        width: 3.5px; border-radius: 3px 0 0 3px;
      }
      .ap-card.pending::before   { background: #f59e0b; }
      .ap-card.completed::before { background: #10b981; }
      .ap-card.completed { background: #f9fffe; border-color: #a7f3d0; opacity: 0.85; }

      .ap-status-badge {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 3px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 700;
      }
      .ap-status-badge.pending   { background: #fef9ee; color: #b45309; border: 1px solid #fde68a; }
      .ap-status-badge.completed { background: #f0fdf4; color: #166534; border: 1px solid #86efac; }

      .ap-icon-btn {
        width: 31px; height: 31px; border-radius: 8px;
        display: inline-flex; align-items: center; justify-content: center;
        border: 1.5px solid #e2e8f4; background: #f7f9fe;
        cursor: pointer; font-size: 13px; transition: all 0.15s;
      }
      .ap-icon-btn:hover        { background: #eff4ff; border-color: #c7d9fc; }
      .ap-icon-btn.danger:hover { background: #fff1f2; border-color: #fca5a5; }
      .ap-icon-btn.success:hover{ background: #f0fdf4; border-color: #86efac; }

      /* ════════════════════════════════════
         DATE GROUP HEADER
      ════════════════════════════════════ */
      .ap-date-header {
        font-size: 11px; font-weight: 700; color: #8899bb;
        letter-spacing: 1px; text-transform: uppercase;
        padding: 14px 4px 8px;
        display: flex; align-items: center; gap: 10px;
      }
      .ap-date-header::after {
        content: ''; flex: 1; height: 1px; background: #f0f4fb;
      }

      /* ════════════════════════════════════
         MODALS
      ════════════════════════════════════ */
      .ap-overlay {
        position: fixed; inset: 0;
        background: rgba(10,25,55,0.45); backdrop-filter: blur(4px);
        display: flex; align-items: center; justify-content: center;
        z-index: 1000; animation: ap-fade 0.2s both;
      }
      .ap-modal {
        background: #fff; border-radius: 18px;
        padding: 32px 36px; max-width: 500px; width: 92%;
        box-shadow: 0 20px 60px rgba(10,25,55,0.22);
        animation: ap-modal-in 0.25s cubic-bezier(.22,.68,0,1.2) both;
        max-height: 92vh; overflow-y: auto;
      }
      @keyframes ap-fade     { from { opacity:0; } to { opacity:1; } }
      @keyframes ap-modal-in { from { opacity:0; transform:translateY(20px) scale(0.97); } to { opacity:1; transform:none; } }

      .ap-form-label {
        font-size: 10.5px; font-weight: 700; color: #8899bb;
        letter-spacing: 0.8px; text-transform: uppercase;
        margin-bottom: 5px; display: block;
      }
      .ap-form-input {
        width: 100%; padding: 10px 14px;
        border: 1.5px solid #e2e8f4; border-radius: 9px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px; color: #1a1f36; background: #f7f9fe;
        outline: none; transition: border-color 0.2s, box-shadow 0.2s;
      }
      .ap-form-input:focus {
        border-color: #1d6fa4;
        box-shadow: 0 0 0 3px rgba(29,111,164,0.10); background: #fff;
      }

      /* ════════════════════════════════════
         ANIMATIONS + SPINNER
      ════════════════════════════════════ */
      @keyframes ap-slide-up {
        from { opacity:0; transform:translateY(14px); }
        to   { opacity:1; transform:translateY(0); }
      }
      .ap-fade-in { animation: ap-slide-up 0.45s cubic-bezier(.22,.68,0,1.1) both; }

      @keyframes ap-spin { to { transform: rotate(360deg); } }
      .ap-spinner {
        width: 18px; height: 18px; border-radius: 50%;
        border: 2px solid #dde8f8; border-top-color: #1d6fa4;
        animation: ap-spin 0.7s linear infinite; display: inline-block;
        vertical-align: middle;
      }

      /* ════════════════════════════════════
         TOOTH DECO PULSE
      ════════════════════════════════════ */
      @keyframes ap-pulse { 0%,100%{opacity:.14} 50%{opacity:.24} }
      .ap-tooth-deco { animation: ap-pulse 4s ease-in-out infinite; }

      /* ════════════════════════════════════
         RESPONSIVE CONTENT PADDING
      ════════════════════════════════════ */
      @media (max-width: 600px) {
        .ap-modal { padding: 24px 18px; }
        .ap-card  { padding: 12px 14px; }
      }
    `;
    document.head.appendChild(style);
  }
  return null;
};

/* ── Decorative tooth SVG ── */
const ToothSVG = ({ size = 60, color = "#fff" }) => (
  <svg width={size} height={size} viewBox="0 0 60 60" fill="none">
    <path d="M30 6C22 6 14 11 14 20C14 26 16 30 18 35C19.5 39 20 44 21 50C21.5 53 23 54 25 52C27 50 28 45 30 45C32 45 33 50 35 52C37 54 38.5 53 39 50C40 44 40.5 39 42 35C44 30 46 26 46 20C46 11 38 6 30 6Z"
      stroke={color} strokeWidth="2.5" strokeLinejoin="round" fill="none" opacity="0.7"/>
    <path d="M22 18C24 16 28 15 30 15C32 15 36 16 38 18"
      stroke={color} strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
  </svg>
);

/* ── Helpers ── */
const MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];

const fmtDateLabel = (ds) => {
  if (!ds) return "—";
  try {
    const d = new Date(ds), now = new Date();
    const tom = new Date(); tom.setDate(now.getDate()+1);
    const yes = new Date(); yes.setDate(now.getDate()-1);
    if (d.toDateString()===now.toDateString()) return "Today";
    if (d.toDateString()===tom.toDateString()) return "Tomorrow";
    if (d.toDateString()===yes.toDateString()) return "Yesterday";
    return d.toLocaleDateString("en-IN",{weekday:"short",day:"numeric",month:"short",year:"numeric"});
  } catch { return ds; }
};

const fmtTime = (t) => {
  if (!t) return "";
  try {
    const [h,m]=t.split(":");
    const hr=parseInt(h), ampm=hr>=12?"PM":"AM", h12=hr%12||12;
    return `${h12}:${m} ${ampm}`;
  } catch { return t; }
};

/* ════════════════════════════════════════════
   APPOINTMENT FORM MODAL
════════════════════════════════════════════ */
const EMPTY = { name:"", date:"", time:"", mobile:"", case_number:"", treatment:"", notes:"" };

const ApptModal = ({ initial, onSave, onClose, saving }) => {
  const [form, setForm] = useState(initial || EMPTY);
  const set = (k,v) => setForm(p=>({...p,[k]:v}));
  const isEdit = !!initial?.appt_id;
  const canSave = form.name.trim() && form.date && form.time && form.mobile.trim();

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-modal" onClick={e=>e.stopPropagation()}>

        {/* Header */}
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:22}}>
          <div>
            <div style={{fontSize:17,fontWeight:800,color:"#0b2d4e"}}>
              {isEdit ? "✏️ Edit Appointment" : "📅 New Appointment"}
            </div>
            <div style={{fontSize:12,color:"#94a3b8",marginTop:2}}>
              {isEdit ? "Update appointment details" : "Book a new patient appointment"}
            </div>
          </div>
          <button onClick={onClose} style={{width:32,height:32,borderRadius:8,border:"1.5px solid #e2e8f4",
            background:"#f7f9fe",fontSize:16,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}}>
            ✕
          </button>
        </div>

        {/* Grid */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px 16px"}}>
          <div style={{gridColumn:"1/-1"}}>
            <label className="ap-form-label">Patient Name *</label>
            <input className="ap-form-input" placeholder="Full name"
              value={form.name} onChange={e=>set("name",e.target.value)} autoFocus />
          </div>
          <div>
            <label className="ap-form-label">Date *</label>
            <input className="ap-form-input" type="date"
              value={form.date} onChange={e=>set("date",e.target.value)} />
          </div>
          <div>
            <label className="ap-form-label">Time *</label>
            <input className="ap-form-input" type="time"
              value={form.time} onChange={e=>set("time",e.target.value)} />
          </div>
          <div>
            <label className="ap-form-label">Mobile *</label>
            <input className="ap-form-input" placeholder="10-digit mobile"
              value={form.mobile} onChange={e=>set("mobile",e.target.value)} />
          </div>
          <div>
            <label className="ap-form-label">Case No. <span style={{color:"#c0cce0",fontWeight:400,textTransform:"none",letterSpacing:0}}>(optional)</span></label>
            <input className="ap-form-input" placeholder="e.g. C-1023"
              value={form.case_number} onChange={e=>set("case_number",e.target.value)} />
          </div>
          <div style={{gridColumn:"1/-1"}}>
            <label className="ap-form-label">Treatment <span style={{color:"#c0cce0",fontWeight:400,textTransform:"none",letterSpacing:0}}>(optional)</span></label>
            <input className="ap-form-input" placeholder="e.g. RCT, Scaling…"
              value={form.treatment} onChange={e=>set("treatment",e.target.value)} />
          </div>
          <div style={{gridColumn:"1/-1"}}>
            <label className="ap-form-label">Notes <span style={{color:"#c0cce0",fontWeight:400,textTransform:"none",letterSpacing:0}}>(optional)</span></label>
            <textarea className="ap-form-input" rows={2} placeholder="Additional notes…"
              value={form.notes} onChange={e=>set("notes",e.target.value)}
              style={{resize:"vertical",minHeight:60}} />
          </div>
        </div>

        {/* Buttons */}
        <div style={{display:"flex",gap:10,marginTop:22}}>
          <button onClick={onClose} style={{flex:1,padding:12,borderRadius:10,
            background:"transparent",color:"#64748b",border:"1.5px solid #e2e8f4",
            fontFamily:"'Plus Jakarta Sans',sans-serif",fontSize:14,fontWeight:600,cursor:"pointer"}}>
            Cancel
          </button>
          <button onClick={()=>onSave(form)} disabled={saving||!canSave} style={{
            flex:2,padding:12,borderRadius:10,
            background:"linear-gradient(135deg,#1d4d7a,#1d6fa4)",
            color:"#fff",border:"none",fontFamily:"'Plus Jakarta Sans',sans-serif",
            fontSize:14,fontWeight:700,cursor:"pointer",
            boxShadow:"0 4px 12px rgba(29,77,122,0.3)",
            opacity:(saving||!canSave)?0.45:1,
            display:"flex",alignItems:"center",justifyContent:"center",gap:6}}>
            {saving ? <><span className="ap-spinner" style={{marginRight:6}}/> Saving…</>
              : (isEdit ? "✔ Update" : "✔ Book Appointment")}
          </button>
        </div>
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   DELETE CONFIRM MODAL
════════════════════════════════════════════ */
const DeleteModal = ({ appt, onConfirm, onCancel, loading }) => (
  <div className="ap-overlay" onClick={onCancel}>
    <div className="ap-modal" style={{maxWidth:420}} onClick={e=>e.stopPropagation()}>
      <div style={{width:52,height:52,borderRadius:14,background:"linear-gradient(135deg,#fff1f2,#ffe4e6)",
        border:"1.5px solid #fca5a5",display:"flex",alignItems:"center",justifyContent:"center",
        fontSize:24,marginBottom:16}}>🗑️</div>
      <div style={{fontSize:17,fontWeight:800,color:"#0b2d4e",marginBottom:8}}>Delete Appointment?</div>
      <div style={{fontSize:13.5,color:"#64748b",lineHeight:1.65,marginBottom:24}}>
        Delete appointment for <strong style={{color:"#0b2d4e"}}>{appt?.name}</strong> on{" "}
        <strong style={{color:"#0b2d4e"}}>{fmtDateLabel(appt?.date)}</strong>? This cannot be undone.
      </div>
      <div style={{display:"flex",gap:10}}>
        <button onClick={onCancel} style={{flex:1,padding:12,borderRadius:10,
          background:"transparent",color:"#64748b",border:"1.5px solid #e2e8f4",
          fontFamily:"'Plus Jakarta Sans',sans-serif",fontSize:14,fontWeight:600,cursor:"pointer"}}>
          Cancel
        </button>
        <button onClick={onConfirm} disabled={loading} style={{
          flex:1,padding:12,borderRadius:10,
          background:"linear-gradient(135deg,#dc2626,#ef4444)",
          color:"#fff",border:"none",fontFamily:"'Plus Jakarta Sans',sans-serif",
          fontSize:14,fontWeight:700,cursor:"pointer",
          boxShadow:"0 4px 12px rgba(220,38,38,0.28)",
          opacity:loading?0.65:1}}>
          {loading ? "Deleting…" : "🗑️ Delete"}
        </button>
      </div>
    </div>
  </div>
);

/* ════════════════════════════════════════════
   APPOINTMENT CARD
════════════════════════════════════════════ */
const ApptCard = ({ appt, onEdit, onDelete, onToggle }) => {
  const done = appt.status === "completed";
  return (
    <div className={`ap-card ${done?"completed":"pending"}`}>
      <div style={{display:"flex",alignItems:"flex-start",justifyContent:"space-between",gap:12}}>
        <div style={{flex:1,minWidth:0}}>
          <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap",marginBottom:6}}>
            <span style={{fontSize:14.5,fontWeight:800,color:done?"#374151":"#0b2d4e",
              textDecoration:done?"line-through":"none"}}>
              {appt.name}
            </span>
            <span className={`ap-status-badge ${done?"completed":"pending"}`}>
              {done ? "✔ Completed" : "⏳ Pending"}
            </span>
          </div>
          <div style={{display:"flex",flexWrap:"wrap",gap:"5px 14px",fontSize:12.5,color:"#64748b"}}>
            <span>🕐 {fmtTime(appt.time)}</span>
            {appt.mobile      && <span>📱 {appt.mobile}</span>}
            {appt.case_number && <span>📁 {appt.case_number}</span>}
            {appt.treatment   && <span>🦷 {appt.treatment}</span>}
          </div>
          {appt.notes && (
            <div style={{marginTop:7,fontSize:12,color:"#94a3b8",fontStyle:"italic",
              background:"#f8faff",borderRadius:7,padding:"5px 10px",display:"inline-block"}}>
              📝 {appt.notes}
            </div>
          )}
        </div>
        <div style={{display:"flex",gap:6,flexShrink:0}}>
          <button className={`ap-icon-btn ${done?"":"success"}`} title={done?"Mark Pending":"Mark Completed"}
            onClick={()=>onToggle(appt)}>{done?"↩":"✔"}</button>
          {!done && <button className="ap-icon-btn" title="Edit" onClick={()=>onEdit(appt)}>✏️</button>}
          <button className="ap-icon-btn danger" title="Delete" onClick={()=>onDelete(appt)}>🗑</button>
        </div>
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   MAIN PAGE
════════════════════════════════════════════ */
export default function AppointmentsPage() {
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [activeTab,    setActiveTab]    = useState("upcoming");
  const [showModal,    setShowModal]    = useState(false);
  const [editAppt,     setEditAppt]     = useState(null);
  const [deleteAppt,   setDeleteAppt]   = useState(null);
  const [saving,       setSaving]       = useState(false);
  const [deleting,     setDeleting]     = useState(false);

  const now = new Date();
  const [filterMonth, setFilterMonth] = useState(now.getMonth()+1);
  const [filterYear,  setFilterYear]  = useState(now.getFullYear());
  const [filterDate,  setFilterDate]  = useState("");

  useEffect(()=>{ load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/appointments");
      setAppointments(res.data || []);
    } catch(e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  /* ── Counts ── */
  const todayStr     = new Date().toDateString();
  const pendingCount = appointments.filter(a=>a.status!=="completed").length;
  const completedCount = appointments.filter(a=>a.status==="completed").length;
  const todayCount   = appointments.filter(a=>a.date && new Date(a.date).toDateString()===todayStr && a.status!=="completed").length;
  const upcomingCount = appointments.filter(a=>{
    if(!a.date||a.status==="completed") return false;
    const d=new Date(a.date); d.setHours(0,0,0,0);
    const t=new Date(); t.setHours(0,0,0,0);
    return d>=t;
  }).length;

  /* ── Filtering ── */
  const filtered = appointments.filter(a => {
    if (!a.date) return false;
    const d = new Date(a.date);
    const today = new Date(); today.setHours(0,0,0,0);

    if (activeTab === "upcoming") {
      const ad = new Date(a.date); ad.setHours(0,0,0,0);
      if (a.status==="completed" || ad<today) return false;
    }
    if (activeTab === "completed" && a.status!=="completed") return false;

    if (filterDate) return a.date===filterDate;
    if (filterMonth && filterYear)
      return d.getMonth()+1===filterMonth && d.getFullYear()===filterYear;
    return true;
  }).sort((a,b) => {
    const da=new Date(`${a.date}T${a.time||"00:00"}`);
    const db=new Date(`${b.date}T${b.time||"00:00"}`);
    return activeTab==="completed" ? db-da : da-db;
  });

  const grouped = filtered.reduce((acc,a)=>{
    if (!acc[a.date]) acc[a.date]=[];
    acc[a.date].push(a);
    return acc;
  },{});
  const groupKeys = Object.keys(grouped).sort((a,b)=>
    activeTab==="completed" ? new Date(b)-new Date(a) : new Date(a)-new Date(b)
  );

  /* ── CRUD ── */
  const handleSave = async (form) => {
    setSaving(true);
    try {
      if (form.appt_id) {
        const res = await api.put(`/appointments/${form.appt_id}`, form);
        setAppointments(p=>p.map(a=>a.appt_id===form.appt_id?res.data:a));
      } else {
        const res = await api.post("/appointments", form);
        setAppointments(p=>[res.data,...p]);
      }
      setShowModal(false); setEditAppt(null);
    } catch(e) { console.error(e); alert("Failed to save. Please try again."); }
    finally    { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleteAppt) return;
    setDeleting(true);
    try {
      await api.delete(`/appointments/${deleteAppt.appt_id}`);
      setAppointments(p=>p.filter(a=>a.appt_id!==deleteAppt.appt_id));
      setDeleteAppt(null);
    } catch(e) { console.error(e); alert("Failed to delete."); }
    finally    { setDeleting(false); }
  };

  const handleToggle = async (appt) => {
    const ns = appt.status==="completed" ? "pending" : "completed";
    try {
      const res = await api.put(`/appointments/${appt.appt_id}`,{...appt,status:ns});
      setAppointments(p=>p.map(a=>a.appt_id===appt.appt_id?res.data:a));
    } catch(e) { console.error(e); alert("Failed to update status."); }
  };

  const openNew  = ()     => { setEditAppt(null);  setShowModal(true); };
  const openEdit = (appt) => { setEditAppt(appt);  setShowModal(true); };

  const yearOptions = [];
  for (let y=now.getFullYear()-2; y<=now.getFullYear()+2; y++) yearOptions.push(y);

  /* ════════════════════════════════════════════
     RENDER
  ════════════════════════════════════════════ */
  return (
    <>
      <GlobalStyles />

      <div style={{minHeight:"100vh",background:"linear-gradient(160deg,#f0f5fb 0%,#e8eff8 50%,#dde8f5 100%)",
        fontFamily:"'Plus Jakarta Sans',sans-serif"}}>

        {/* ════════════════════════
            HERO HEADER
        ════════════════════════ */}
        <div style={{background:"linear-gradient(135deg,#0b2d4e 0%,#0f4270 45%,#1059a0 100%)",
          padding:"32px 24px 36px",position:"relative",overflow:"hidden"}}>

          {/* Decorative teeth */}
          <div className="ap-tooth-deco" style={{position:"absolute",top:-10,right:50,opacity:0.13}}>
            <ToothSVG size={120} color="#fff"/>
          </div>
          <div className="ap-tooth-deco" style={{position:"absolute",bottom:-18,right:200,opacity:0.07,animationDelay:"2s"}}>
            <ToothSVG size={85} color="#fff"/>
          </div>

          <div style={{maxWidth:1100,margin:"0 auto",position:"relative",zIndex:1}}>

            {/* Clinic branding */}
            <div style={{display:"flex",alignItems:"center",gap:18,marginBottom:20}}>
              <div style={{width:54,height:54,borderRadius:14,flexShrink:0,
                background:"linear-gradient(135deg,rgba(255,255,255,0.2),rgba(255,255,255,0.07))",
                border:"1.5px solid rgba(255,255,255,0.25)",
                display:"flex",alignItems:"center",justifyContent:"center",
                backdropFilter:"blur(6px)",boxShadow:"0 4px 16px rgba(0,0,0,0.18)"}}>
                <ToothSVG size={34} color="#fff"/>
              </div>
              <div>
                <h1 style={{fontFamily:"'Cormorant Garamond',serif",fontSize:26,fontWeight:700,
                  color:"#fff",lineHeight:1.1,textShadow:"0 2px 8px rgba(0,0,0,0.3)"}}>
                  Sri Satya Sai Oral Health Center
                </h1>
                <p style={{fontFamily:"'Cormorant Garamond',serif",fontSize:16,
                  color:"rgba(255,255,255,0.78)",fontStyle:"italic",marginTop:3}}>
                  &amp; Dental Clinic
                </p>
              </div>
            </div>

            {/* Stat pills row + New Appointment button */}
            <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
              {[
                {label:"Upcoming",  value:upcomingCount,  color:"#93c5fd"},
                {label:"Today",     value:todayCount,     color:"#86efac"},
                {label:"Pending",   value:pendingCount,   color:"#fde68a"},
                {label:"Completed", value:completedCount, color:"#c4b5fd"},
              ].map(s=>(
                <div key={s.label} className="ap-stat-pill">
                  <span style={{fontSize:20,fontWeight:800,color:s.color,lineHeight:1}}>{s.value}</span>
                  <span style={{fontSize:11.5,color:"rgba(255,255,255,0.68)",fontWeight:600}}>{s.label}</span>
                </div>
              ))}

              <button onClick={openNew} style={{
                marginLeft:"auto",display:"inline-flex",alignItems:"center",gap:8,
                padding:"10px 22px",borderRadius:11,
                background:"rgba(255,255,255,0.18)",
                border:"1.5px solid rgba(255,255,255,0.32)",
                color:"#fff",fontFamily:"'Plus Jakarta Sans',sans-serif",
                fontSize:13.5,fontWeight:700,cursor:"pointer",
                transition:"background 0.18s",flexShrink:0,
                boxShadow:"0 4px 14px rgba(0,0,0,0.15)"}}
                onMouseEnter={e=>e.currentTarget.style.background="rgba(255,255,255,0.26)"}
                onMouseLeave={e=>e.currentTarget.style.background="rgba(255,255,255,0.18)"}>
                <span style={{fontSize:17,fontWeight:700}}>+</span> New Appointment
              </button>
            </div>
          </div>
        </div>

        {/* ════════════════════════
            NAVBAR — ALL LINKS
            scrollable on mobile
        ════════════════════════ */}
        <nav className="ap-navbar">
          <div className="ap-navbar-inner">

            <button className="ap-nav-btn"
              onClick={()=>navigate("/reception/dashboard")}>
              <span className="ap-nav-emoji">🏠</span> Dashboard
            </button>

            <button className="ap-nav-btn"
              onClick={()=>navigate("/reception/patient/new")}>
              <span className="ap-nav-emoji">👤</span> New Patient
            </button>

            <button className="ap-nav-btn"
              onClick={()=>navigate("/reception/dashboard")}>
              <span className="ap-nav-emoji">🔍</span> Find Patient
            </button>

            <button className="ap-nav-btn active">
              <span className="ap-nav-emoji">📅</span> Appointments
              {pendingCount > 0 && (
                <span className="ap-nav-badge">{pendingCount}</span>
              )}
            </button>

            <button className="ap-nav-btn"
              onClick={()=>navigate("/reception/dashboard?section=prescriptions")}>
              <span className="ap-nav-emoji">💊</span> Prescriptions
            </button>

            <button className="ap-nav-btn"
              onClick={()=>navigate("/doctor/dashboard")}>
              <span className="ap-nav-emoji">🩺</span> Doctor View
            </button>

          </div>
        </nav>

        {/* ════════════════════════
            APPOINTMENTS CONTENT
        ════════════════════════ */}
        <div style={{maxWidth:1100,margin:"28px auto 0",padding:"0 16px 60px"}}>
          <div className="ap-fade-in" style={{
            background:"#fff",borderRadius:16,overflow:"hidden",
            border:"1px solid rgba(226,232,244,0.9)",
            boxShadow:"0 2px 8px rgba(29,77,122,0.05),0 8px 24px rgba(29,77,122,0.07)"}}>

            {/* Card top header bar */}
            <div style={{
              background:"linear-gradient(135deg,#0f4270,#1059a0)",
              padding:"18px 24px",
              display:"flex",alignItems:"center",justifyContent:"space-between",gap:12}}>
              <div style={{display:"flex",alignItems:"center",gap:12}}>
                <div style={{width:38,height:38,borderRadius:10,
                  background:"rgba(255,255,255,0.15)",border:"1px solid rgba(255,255,255,0.22)",
                  display:"flex",alignItems:"center",justifyContent:"center",fontSize:18}}>
                  📅
                </div>
                <div>
                  <div style={{fontSize:15,fontWeight:800,color:"#fff"}}>Appointments Diary</div>
                  <div style={{fontSize:11.5,color:"rgba(255,255,255,0.62)",marginTop:1}}>
                    {pendingCount} pending · {todayCount} today · {completedCount} completed
                  </div>
                </div>
              </div>
              <button onClick={load} style={{
                display:"inline-flex",alignItems:"center",gap:6,
                padding:"7px 16px",borderRadius:9,
                background:"rgba(255,255,255,0.14)",border:"1.5px solid rgba(255,255,255,0.26)",
                color:"#fff",fontFamily:"'Plus Jakarta Sans',sans-serif",
                fontSize:12.5,fontWeight:600,cursor:"pointer",transition:"background 0.18s"}}
                onMouseEnter={e=>e.currentTarget.style.background="rgba(255,255,255,0.22)"}
                onMouseLeave={e=>e.currentTarget.style.background="rgba(255,255,255,0.14)"}>
                ↻ Refresh
              </button>
            </div>

            <div style={{padding:"20px 24px 28px"}}>

              {/* Tabs */}
              <div className="ap-tab-bar">
                {[
                  {key:"upcoming",  label:"Upcoming",  count:upcomingCount},
                  {key:"all",       label:"All",        count:appointments.length},
                  {key:"completed", label:"Completed",  count:completedCount},
                ].map(tab=>(
                  <button key={tab.key}
                    className={`ap-tab ${activeTab===tab.key?"active":""}`}
                    onClick={()=>setActiveTab(tab.key)}>
                    {tab.label}
                    <span className="ap-tab-count" style={{
                      background: activeTab===tab.key ? "#1d4d7a" : "#f0f4fb",
                      color:      activeTab===tab.key ? "#fff"    : "#94a3b8",
                    }}>{tab.count}</span>
                  </button>
                ))}
              </div>

              {/* Filter row */}
              <div className="ap-filter-wrap">
                <span className="ap-filter-label">Filter:</span>

                <input type="date" className="ap-filter-input"
                  value={filterDate}
                  onChange={e=>setFilterDate(e.target.value)} />

                <select className="ap-filter-select"
                  value={filterMonth}
                  onChange={e=>{setFilterMonth(Number(e.target.value));setFilterDate("");}}>
                  {MONTHS.map((m,i)=>(
                    <option key={m} value={i+1}>{m}</option>
                  ))}
                </select>

                <select className="ap-filter-select"
                  value={filterYear}
                  onChange={e=>{setFilterYear(Number(e.target.value));setFilterDate("");}}>
                  {yearOptions.map(y=><option key={y} value={y}>{y}</option>)}
                </select>

                {filterDate && (
                  <button onClick={()=>setFilterDate("")} style={{
                    padding:"7px 12px",borderRadius:8,border:"1.5px solid #e2e8f4",
                    background:"#f7f9fe",color:"#64748b",cursor:"pointer",
                    fontFamily:"'Plus Jakarta Sans',sans-serif",fontSize:12,fontWeight:600}}>
                    ✕ Clear
                  </button>
                )}

                <span style={{marginLeft:"auto",fontSize:12,color:"#94a3b8",fontWeight:600}}>
                  {filtered.length} appointment{filtered.length!==1?"s":""}
                </span>
              </div>

              {/* Content */}
              {loading ? (
                <div style={{textAlign:"center",padding:"44px 0",color:"#94a3b8"}}>
                  <span className="ap-spinner" style={{width:22,height:22}}/>{" "}
                  <span style={{marginLeft:10}}>Loading appointments…</span>
                </div>

              ) : groupKeys.length === 0 ? (
                <div style={{textAlign:"center",padding:"48px 20px",color:"#94a3b8"}}>
                  <div style={{fontSize:44,marginBottom:12,opacity:0.35}}>📅</div>
                  <div style={{fontWeight:700,color:"#475569",marginBottom:6,fontSize:15}}>
                    No appointments found
                  </div>
                  <div style={{fontSize:13}}>Try adjusting the filters or book a new appointment.</div>
                  <button onClick={openNew} style={{
                    marginTop:18,display:"inline-flex",alignItems:"center",gap:7,
                    padding:"10px 24px",borderRadius:10,
                    background:"linear-gradient(135deg,#1d4d7a,#1d6fa4)",
                    color:"#fff",border:"none",
                    fontFamily:"'Plus Jakarta Sans',sans-serif",
                    fontSize:13,fontWeight:700,cursor:"pointer",
                    boxShadow:"0 4px 12px rgba(29,77,122,0.25)"}}>
                    + Book Appointment
                  </button>
                </div>

              ) : (
                <div style={{display:"flex",flexDirection:"column",gap:0}}>
                  {groupKeys.map(dk=>(
                    <div key={dk}>
                      <div className="ap-date-header">
                        {fmtDateLabel(dk)}
                        <span style={{fontSize:10.5,fontWeight:700,
                          background:"#f0f4fb",color:"#8899bb",
                          padding:"1px 8px",borderRadius:20}}>
                          {grouped[dk].length}
                        </span>
                      </div>
                      <div style={{display:"flex",flexDirection:"column",gap:8,marginBottom:8}}>
                        {grouped[dk].map(appt=>(
                          <ApptCard key={appt.appt_id} appt={appt}
                            onEdit={openEdit}
                            onDelete={setDeleteAppt}
                            onToggle={handleToggle} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showModal && (
        <ApptModal
          initial={editAppt}
          onSave={handleSave}
          onClose={()=>{setShowModal(false);setEditAppt(null);}}
          saving={saving}
        />
      )}
      {deleteAppt && (
        <DeleteModal
          appt={deleteAppt}
          onConfirm={handleDelete}
          onCancel={()=>setDeleteAppt(null)}
          loading={deleting}
        />
      )}
    </>
  );
}