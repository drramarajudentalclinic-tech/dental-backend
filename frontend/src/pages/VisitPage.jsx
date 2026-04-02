import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/api";

import DoctorMedicalSummary from "../components/doctor/DoctorMedicalSummary";
import DoctorHabitsSummary from "../components/doctor/DoctorHabitsSummary";
import DoctorWomenSummary from "../components/doctor/DoctorWomenSummary";

import DentalChart from "../components/DentalChart";
import Findings from "../components/Findings";
import Consultation from "../components/Consultation";
import Prescription from "../components/Prescription";
import ImageUpload from "../components/ImageUpload";

/* ═══════════════════════════════════════════
   GLOBAL STYLES
═══════════════════════════════════════════ */
const injectStyles = () => {
  if (document.getElementById("vp-styles")) return;

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href =
    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap";
  document.head.appendChild(link);

  const s = document.createElement("style");
  s.id = "vp-styles";
  s.textContent = `
    *, *::before, *::after { box-sizing: border-box; }

    .vp-card {
      background: #fff;
      border-radius: 16px;
      border: 1px solid rgba(220,230,245,0.9);
      box-shadow: 0 2px 8px rgba(15,50,100,0.05), 0 8px 28px rgba(15,50,100,0.06);
      padding: 26px 30px;
      margin-bottom: 20px;
    }
    .vp-card-teal  { border-color: rgba(20,184,166,0.25) !important; }
    .vp-card-blue  { border-color: rgba(37,99,235,0.2)  !important; }
    .vp-card-red   { border-color: rgba(220,38,38,0.2)  !important; }
    .vp-card-amber { border-color: rgba(217,119,6,0.2)  !important; }
    .vp-card-green { border-color: rgba(22,163,74,0.2)  !important; }

    .vp-badge {
      display: inline-flex; align-items: center; gap: 7px;
      font-size: 10px; font-weight: 800; letter-spacing: 1.4px;
      text-transform: uppercase; padding: 4px 12px;
      border-radius: 20px; margin-bottom: 18px;
    }

    .vp-info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 13px;
    }
    .vp-info-cell {
      background: #f7f9fe; border: 1px solid #edf1fa;
      border-radius: 10px; padding: 11px 14px;
    }
    .vp-info-label {
      font-size: 10px; font-weight: 800; color: #8899bb;
      letter-spacing: 0.9px; text-transform: uppercase; margin-bottom: 4px;
    }
    .vp-info-value {
      font-size: 13.5px; font-weight: 600; color: #1a2540; line-height: 1.35;
    }

    .vp-alert-pill {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 7px 14px; border-radius: 9px;
      font-size: 12.5px; font-weight: 700;
    }

    .vp-table { width: 100%; border-collapse: collapse; }
    .vp-table thead tr { background: linear-gradient(90deg, #1e3a6e 0%, #2563eb 100%); }
    .vp-table thead th {
      padding: 10px 14px; text-align: left;
      font-size: 10.5px; font-weight: 700; letter-spacing: 0.7px;
      text-transform: uppercase; color: rgba(255,255,255,0.92);
    }
    .vp-table thead th:first-child { border-radius: 9px 0 0 0; }
    .vp-table thead th:last-child  { border-radius: 0 9px 0 0; }
    .vp-table tbody tr { border-bottom: 1px solid #f0f3fb; transition: background 0.15s; }
    .vp-table tbody tr:last-child { border-bottom: none; }
    .vp-table tbody tr:hover { background: #f7f9ff; }
    .vp-table tbody td { padding: 10px 14px; font-size: 13px; color: #2d3a55; vertical-align: middle; }
    .vp-table-wrap {
      border-radius: 10px; overflow: hidden;
      border: 1.5px solid #e4ecfb;
      box-shadow: 0 2px 8px rgba(37,99,235,0.06);
    }
    .vp-sev { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
    .vp-sev-mild { background:#dcfce7; color:#166534; }
    .vp-sev-mod  { background:#fef9c3; color:#854d0e; }
    .vp-sev-sev  { background:#fee2e2; color:#991b1b; }
    .vp-sev-life { background:#ede9fe; color:#5b21b6; }

    .vp-chip {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 4px 12px; border-radius: 20px;
      font-size: 11.5px; font-weight: 600;
    }

    .vp-module {
      background: #fff;
      border-radius: 16px;
      border: 1px solid rgba(220,230,245,0.9);
      box-shadow: 0 2px 8px rgba(15,50,100,0.04), 0 6px 20px rgba(15,50,100,0.05);
      padding: 22px 28px;
      margin-bottom: 18px;
    }
    .vp-module-header {
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 18px; padding-bottom: 14px;
      border-bottom: 1px solid #edf1fa;
    }
    .vp-module-icon {
      width: 34px; height: 34px; border-radius: 9px; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center; font-size: 17px;
    }
    .vp-module-title { font-size: 13.5px; font-weight: 700; color: #0b2540; }
    .vp-module-sub   { font-size: 11.5px; color: #8899bb; margin-top: 1px; }

    .vp-back-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 11px 22px; border-radius: 10px;
      background: rgba(255,255,255,0.1); color: #e2eaf8;
      border: 1.5px solid rgba(255,255,255,0.2);
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 13.5px; font-weight: 600; cursor: pointer; transition: all 0.18s;
    }
    .vp-back-btn:hover { background: rgba(255,255,255,0.18); }

    .vp-close-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 12px 28px; border-radius: 10px;
      background: linear-gradient(135deg, #dc2626, #ef4444);
      color: #fff; border: none;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 14px; font-weight: 700; cursor: pointer;
      box-shadow: 0 4px 14px rgba(220,38,38,0.32);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .vp-close-btn:hover  { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(220,38,38,0.4); }
    .vp-close-btn:active { transform: translateY(0); }

    @keyframes vp-in { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    .vp-animate { animation: vp-in 0.45s cubic-bezier(.22,.68,0,1.1) both; }
    .vp-d1 { animation-delay: 0.04s; } .vp-d2 { animation-delay: 0.08s; }
    .vp-d3 { animation-delay: 0.12s; } .vp-d4 { animation-delay: 0.16s; }
    .vp-d5 { animation-delay: 0.20s; } .vp-d6 { animation-delay: 0.24s; }

    @keyframes vp-pulse-alert {
      0%,100% { box-shadow: 0 0 0 0 rgba(220,38,38,0.3); }
      50%      { box-shadow: 0 0 0 6px rgba(220,38,38,0); }
    }
    .vp-alert-pulse { animation: vp-pulse-alert 2.2s ease-in-out infinite; }
  `;
  document.head.appendChild(s);
};

/* ── Check a medical flag regardless of key format ── */
const medFlag = (data, ...keys) => {
  for (const k of keys) {
    const v = data?.[k];
    if (v === true || v === 1 || v === "YES" || v === "yes") return true;
  }
  return false;
};

/* ── Helpers ── */
const InfoCell = ({ label, value, wide, accent }) => (
  <div className="vp-info-cell" style={wide ? { gridColumn: "span 2" } : {}}>
    <div className="vp-info-label">{label}</div>
    <div className="vp-info-value" style={accent ? { color: accent } : {}}>
      {value || <span style={{ color: "#c0cce0", fontWeight: 400, fontSize: 12.5 }}>Not provided</span>}
    </div>
  </div>
);

const SevPill = ({ s }) => {
  const map = { Mild: "vp-sev-mild", Moderate: "vp-sev-mod", Severe: "vp-sev-sev", "Life-threatening": "vp-sev-life" };
  return s
    ? <span className={`vp-sev ${map[s] || "vp-sev-mod"}`}>{s}</span>
    : <span style={{ color: "#b0bad0" }}>—</span>;
};

const Module = ({ icon, title, sub, bg, children, delay = "" }) => (
  <div className={`vp-module vp-animate ${delay}`}>
    <div className="vp-module-header">
      <div className="vp-module-icon" style={{ background: bg || "#eff4ff" }}>{icon}</div>
      <div>
        <div className="vp-module-title">{title}</div>
        {sub && <div className="vp-module-sub">{sub}</div>}
      </div>
    </div>
    {children}
  </div>
);

const Card = ({ badge, badgeColor, badgeBg, icon, children, delay = "", extra = "" }) => (
  <div className={`vp-card vp-animate ${delay} ${extra}`}>
    {badge && (
      <div className="vp-badge" style={{
        background: badgeBg || "#eff4ff",
        color: badgeColor || "#1d4ed8",
        border: `1px solid ${badgeColor || "#1d4ed8"}22`,
      }}>
        {icon && <span style={{ fontSize: 12 }}>{icon}</span>}
        {badge}
      </div>
    )}
    {children}
  </div>
);

/* ═══════════════════════════════════════════
   BILLING INSTRUCTIONS MODAL
═══════════════════════════════════════════ */
function BillingInstructionsModal({ visit, patient, onConfirm, onCancel }) {
  const [billingNote, setBillingNote] = useState("");
  const [saving,      setSaving]      = useState(false);

  const handleConfirm = async () => {
    setSaving(true);
    await onConfirm(billingNote.trim());
    setSaving(false);
  };

  return (
    <div style={{
      position:"fixed", inset:0, zIndex:2000,
      background:"rgba(10,25,55,0.6)", backdropFilter:"blur(5px)",
      display:"flex", alignItems:"center", justifyContent:"center",
    }} onClick={onCancel}>
      <div style={{
        background:"#fff", borderRadius:20, width:"95%", maxWidth:560,
        maxHeight:"92vh", overflowY:"auto",
        boxShadow:"0 28px 80px rgba(10,25,55,0.3)",
      }} onClick={e => e.stopPropagation()}>

        <div style={{
          padding:"22px 28px 16px",
          background:"linear-gradient(135deg,#0b2d4e,#1d6fa4)",
          borderRadius:"20px 20px 0 0",
          display:"flex", alignItems:"center", justifyContent:"space-between",
        }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            <div style={{
              width:44, height:44, borderRadius:12, flexShrink:0,
              background:"rgba(255,255,255,0.15)", border:"1.5px solid rgba(255,255,255,0.3)",
              display:"flex", alignItems:"center", justifyContent:"center", fontSize:20,
            }}>💰</div>
            <div>
              <div style={{ fontSize:16, fontWeight:800, color:"#fff" }}>Close Visit & Send to Billing</div>
              <div style={{ fontSize:12, color:"rgba(255,255,255,0.65)", marginTop:2 }}>
                {patient?.name}{patient?.case_number ? ` · Case ${patient.case_number}` : ""}
              </div>
            </div>
          </div>
          <button onClick={onCancel} style={{
            width:32, height:32, borderRadius:9,
            border:"1.5px solid rgba(255,255,255,0.25)", background:"rgba(255,255,255,0.12)",
            color:"#fff", fontSize:16, cursor:"pointer",
            display:"flex", alignItems:"center", justifyContent:"center",
          }}>✕</button>
        </div>

        <div style={{ padding:"22px 28px 28px" }}>
          <div style={{
            background:"#f0f8ff", border:"1px solid #bfdbfe",
            borderRadius:10, padding:"10px 14px", marginBottom:18,
            fontSize:12.5, color:"#1d4d7a", lineHeight:1.6,
          }}>
            📋 The clinical summary will be sent to the <strong>reception billing queue</strong> automatically.
            Add optional billing instructions below, then you will return to your <strong>dashboard</strong> for the next patient.
          </div>

          {(visit?.diagnosis || visit?.treatment_done || visit?.treatment_plan || visit?.advice) && (
            <div style={{
              background:"#f0f7ff", border:"1px solid #bfdbfe",
              borderRadius:10, padding:"14px 18px", marginBottom:18,
            }}>
              <div style={{ fontSize:11, fontWeight:800, color:"#1d4d7a", letterSpacing:0.5,
                textTransform:"uppercase", marginBottom:10 }}>
                📋 Clinical Summary (auto-sent to billing)
              </div>
              {visit?.diagnosis      && <div style={{ display:"flex", gap:8, marginBottom:6, fontSize:13 }}><span style={{ fontWeight:700, color:"#0b2d4e", minWidth:130, flexShrink:0 }}>Diagnosis:</span><span style={{ color:"#334155" }}>{visit.diagnosis}</span></div>}
              {visit?.treatment_done && <div style={{ display:"flex", gap:8, marginBottom:6, fontSize:13 }}><span style={{ fontWeight:700, color:"#0b2d4e", minWidth:130, flexShrink:0 }}>Treatment Done:</span><span style={{ color:"#334155" }}>{visit.treatment_done}</span></div>}
              {visit?.treatment_plan && <div style={{ display:"flex", gap:8, marginBottom:6, fontSize:13 }}><span style={{ fontWeight:700, color:"#0b2d4e", minWidth:130, flexShrink:0 }}>Treatment Plan:</span><span style={{ color:"#334155" }}>{visit.treatment_plan}</span></div>}
              {visit?.advice         && <div style={{ display:"flex", gap:8, fontSize:13 }}><span style={{ fontWeight:700, color:"#0b2d4e", minWidth:130, flexShrink:0 }}>Advice:</span><span style={{ color:"#334155" }}>{visit.advice}</span></div>}
            </div>
          )}

          <div style={{
            background:"#fffbeb", border:"1.5px solid #fde68a",
            borderRadius:12, padding:"16px 18px", marginBottom:22,
          }}>
            <div style={{ fontSize:11, fontWeight:800, color:"#92400e", letterSpacing:"0.8px",
              textTransform:"uppercase", marginBottom:8, display:"flex", alignItems:"center", gap:6 }}>
              <span>📝</span> Billing Instructions for Reception
              <span style={{ fontSize:10, fontWeight:600, color:"#b45309", background:"#fef3c7",
                border:"1px solid #fde68a", borderRadius:20, padding:"1px 8px",
                textTransform:"none", letterSpacing:0, marginLeft:4 }}>Optional</span>
            </div>
            <textarea
              style={{
                width:"100%", padding:"12px 14px",
                border:"1.5px solid #fde68a", borderRadius:10,
                fontFamily:"'Plus Jakarta Sans',sans-serif",
                fontSize:13.5, color:"#78350f",
                background:"#fffdf5", outline:"none",
                resize:"vertical", minHeight:100, boxSizing:"border-box",
              }}
              placeholder="e.g. Charge RCT separately (₹3000), apply staff discount on scaling…"
              value={billingNote}
              onChange={e => setBillingNote(e.target.value)}
              rows={4}
              autoFocus
            />
            <div style={{ fontSize:11, color:"#92400e", marginTop:6, opacity:0.75 }}>
              💡 These notes will be shown prominently to the receptionist when generating the bill.
            </div>
          </div>

          <div style={{ display:"flex", gap:10 }}>
            <button onClick={onCancel} style={{
              flex:1, padding:13, borderRadius:11,
              background:"transparent", color:"#64748b",
              border:"1.5px solid #e2e8f4",
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              fontSize:14, fontWeight:600, cursor:"pointer",
            }}>Cancel</button>
            <button onClick={handleConfirm} disabled={saving} style={{
              flex:2, padding:13, borderRadius:11,
              background:"linear-gradient(135deg,#dc2626,#ef4444)",
              color:"#fff", border:"none",
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              fontSize:14, fontWeight:700, cursor:"pointer",
              boxShadow:"0 4px 14px rgba(220,38,38,0.3)",
              opacity: saving ? 0.65 : 1,
            }}>
              {saving ? "Closing Visit…" : "🔒 Close Visit & Return to Dashboard"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════ */
export default function VisitPage() {
  const { visitId } = useParams();
  const navigate    = useNavigate();

  const [showBillingDlg, setShowBillingDlg] = useState(false);
  const [closing,        setClosing]        = useState(false);

  const [loading,    setLoading]    = useState(true);
  const [visit,      setVisit]      = useState(null);
  const [patient,    setPatient]    = useState(null);
  const [medical,    setMedical]    = useState({});
  const [allergy,    setAllergy]    = useState({ rows: [] });
  const [habits,     setHabits]     = useState([]);
  const [women,      setWomen]      = useState({});
  const [familyDoc,  setFamilyDoc]  = useState({});
  const [consent,    setConsent]    = useState({});

  // ── NEW: lifted state for auto-filling Consultation diagnosis ──
  const [chartRecords,       setChartRecords]       = useState([]);
  const [findings,           setFindings]           = useState([]);
  const [latestConsultation, setLatestConsultation] = useState(null);

  useEffect(() => {
    injectStyles();
    if (visitId) loadAll();
  }, [visitId]);

  const loadAll = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/visits/${visitId}`);
      const d   = res.data;

      setVisit(d.visit     || null);
      setPatient(d.patient || null);
      setMedical(d.medical || {});
      setAllergy(d.allergy && Array.isArray(d.allergy.rows) ? d.allergy : { rows: [] });
      setHabits(Array.isArray(d.habits) ? d.habits : []);
      setWomen(d.women     || {});
      setFamilyDoc(d.family_doctor || {});
      setConsent(d.consent || {});
    } catch (err) {
      console.error(err);
      alert("Failed to load visit details");
    } finally {
      setLoading(false);
    }
  };

  // Fetch latest consultation so Prescription can auto-fill
  const loadLatestConsultation = async () => {
    if (!visitId) return;
    try {
      const res = await api.get(`/visits/${visitId}/consultations`);
      const rows = res.data || [];
      if (rows.length > 0) setLatestConsultation(rows[rows.length - 1]);
    } catch {}
  };

  useEffect(() => {
    loadLatestConsultation();
    // Poll every 5s so prescription auto-fills shortly after doctor saves consultation
    const interval = setInterval(loadLatestConsultation, 5000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visitId]);

  const handleCloseVisit = async (billingNote) => {
    setClosing(true);
    try {
      await api.put(`/visits/${visitId}/close`, { billing_note: billingNote });
      setShowBillingDlg(false);
      navigate(-1);
    } catch (err) {
      console.error(err);
      alert("Failed to close visit. Please try again.");
      setClosing(false);
    }
  };

  const calculateAge = (dob, manual) => {
    if (dob) {
      const b = new Date(dob), t = new Date();
      let a = t.getFullYear() - b.getFullYear();
      if (t.getMonth() - b.getMonth() < 0 ||
         (t.getMonth() === b.getMonth() && t.getDate() < b.getDate())) a--;
      return a + " yrs";
    }
    return manual ? manual + " yrs" : "—";
  };

  if (loading) return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center",
      minHeight:"100vh", fontFamily:"'Plus Jakarta Sans',sans-serif", color:"#64748b", fontSize:14, gap:10 }}>
      <span style={{ fontSize:22 }}>🦷</span> Loading visit…
    </div>
  );
  if (!visit || !patient) return (
    <div style={{ padding:40, fontFamily:"'Plus Jakarta Sans',sans-serif", color:"#64748b" }}>
      Visit not found.
    </div>
  );

  const isClosed    = (visit.status || "").toUpperCase() === "CLOSED";
  const allergyRows = allergy?.rows || [];

  const chiefComplaint =
    (visit.chief_complaint && visit.chief_complaint.trim())
      ? visit.chief_complaint
      : (patient.chief_complaint || "");

  const alerts = [];
  if (medFlag(medical, "bp_high",        "Blood_Pressure_High")) alerts.push({ icon:"🔴", text:"Known Hypertension",       color:"#991b1b", bg:"#fee2e2" });
  if (medFlag(medical, "bp_low",         "Blood_Pressure_Low"))  alerts.push({ icon:"🟠", text:"Low Blood Pressure",       color:"#92400e", bg:"#fff7ed" });
  if (medFlag(medical, "diabetes",       "Diabetes"))             alerts.push({ icon:"🔴", text:"Known Diabetes",           color:"#991b1b", bg:"#fee2e2" });
  if (medFlag(medical, "heart_problems", "Heart_Problems"))       alerts.push({ icon:"🔴", text:"Cardiac Risk",             color:"#991b1b", bg:"#fee2e2" });
  if (women?.pregnant)                                             alerts.push({ icon:"🔴", text:"Pregnant Patient",         color:"#86198f", bg:"#fdf4ff" });
  if (allergyRows.some(r => r.severity === "Life-threatening"))   alerts.push({ icon:"🟣", text:"Life-threatening Allergy", color:"#5b21b6", bg:"#ede9fe" });

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(150deg, #eef2fb 0%, #e6ecf8 55%, #dde8f5 100%)",
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      padding: "0 0 60px",
    }}>

      {/* ══════════ CLINIC HEADER ══════════ */}
      <div style={{
        background: "linear-gradient(135deg, #0b2d4e 0%, #0f4270 50%, #1059a0 100%)",
        padding: "20px 36px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        boxShadow: "0 4px 20px rgba(11,45,78,0.25)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{
            width:40, height:40, borderRadius:10, flexShrink:0,
            background:"rgba(255,255,255,0.12)", border:"1px solid rgba(255,255,255,0.2)",
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:20,
          }}>🦷</div>
          <div>
            <p style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:18, fontWeight:700, color:"#fff", lineHeight:1.2 }}>
              Sri Satya Sai Oral Health Center & Dental Clinic
            </p>
            <p style={{ fontSize:11.5, color:"rgba(255,255,255,0.6)", marginTop:2 }}>
              Dr. Rama Raju · MDS &nbsp;|&nbsp;
              <span style={{ color:isClosed?"#fca5a5":"#86efac", fontWeight:700 }}>
                {isClosed ? "🔒 Visit Closed" : "🟢 Active Visit"}
              </span>
              {(visit.visit_date || visit.date) && (
                <span style={{ marginLeft:8, color:"rgba(255,255,255,0.5)" }}>
                  · {new Date(visit.visit_date || visit.date).toLocaleDateString("en-IN",
                      { day:"numeric", month:"short", year:"numeric" })}
                </span>
              )}
            </p>
          </div>
        </div>

        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          <div style={{
            background:"rgba(255,255,255,0.1)", border:"1px solid rgba(255,255,255,0.18)",
            borderRadius:10, padding:"7px 14px", marginRight:6,
          }}>
            <p style={{ fontSize:11, color:"rgba(255,255,255,0.55)", fontWeight:600, letterSpacing:"0.5px" }}>PATIENT</p>
            <p style={{ fontSize:14, color:"#fff", fontWeight:700, marginTop:1 }}>{patient.name}</p>
          </div>
          <button className="vp-back-btn" onClick={() => navigate(-1)}>← Back</button>
          {!isClosed && (
            <button className="vp-close-btn" onClick={() => setShowBillingDlg(true)} disabled={closing}>
              {closing ? "Closing…" : "🔒 Close Visit"}
            </button>
          )}
        </div>
      </div>

      <div style={{ maxWidth:1100, margin:"30px auto 0", padding:"0 24px" }}>

        {/* ══════════ MEDICAL ALERTS ══════════ */}
        {alerts.length > 0 && (
          <div className="vp-card vp-animate vp-alert-pulse" style={{
            background:"linear-gradient(135deg,#fff5f5,#fff)",
            border:"2px solid #fca5a5", marginBottom:22,
          }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:14 }}>
              <div style={{ width:34, height:34, borderRadius:9, background:"#fee2e2",
                display:"flex", alignItems:"center", justifyContent:"center", fontSize:17 }}>🚨</div>
              <div>
                <p style={{ fontSize:11, fontWeight:800, letterSpacing:"1.2px",
                  textTransform:"uppercase", color:"#dc2626" }}>Medical Alerts</p>
                <p style={{ fontSize:12, color:"#7f1d1d", marginTop:1 }}>Review carefully before any procedure</p>
              </div>
            </div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:10 }}>
              {alerts.map((a,i) => (
                <div key={i} className="vp-alert-pill"
                  style={{ background:a.bg, color:a.color, border:`1px solid ${a.color}33` }}>
                  {a.icon} {a.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════ PATIENT IDENTITY ══════════ */}
        <Card badge="Patient Information" badgeColor="#0f4270" badgeBg="#eff4ff" icon="👤" delay="vp-d1">
          <div style={{ display:"flex", alignItems:"center", gap:18, marginBottom:20 }}>
            <div style={{
              width:56, height:56, borderRadius:14, flexShrink:0,
              background:`linear-gradient(135deg,${patient.gender==="Female"?"#be185d,#db2777":"#0f4270,#1d6fa4"})`,
              display:"flex", alignItems:"center", justifyContent:"center",
              color:"#fff", fontSize:22, fontWeight:700,
              boxShadow:"0 4px 14px rgba(15,66,112,0.25)",
            }}>
              {(patient.name||"?")[0].toUpperCase()}
            </div>
            <div style={{ flex:1 }}>
              <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:26,
                fontWeight:700, color:"#0b2540", lineHeight:1.2 }}>
                {patient.name}
              </h2>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginTop:7 }}>
                {patient.case_number && (
                  <span className="vp-chip" style={{ background:"#eff4ff", color:"#1d4ed8", border:"1px solid #c7d9fc" }}>
                    📁 Case: {patient.case_number}
                  </span>
                )}
                {patient.gender && (
                  <span className="vp-chip" style={{
                    background:patient.gender==="Female"?"#fdf2f8":"#eff4ff",
                    color:patient.gender==="Female"?"#be185d":"#1d4d7a",
                    border:"1px solid currentColor",
                  }}>
                    {patient.gender==="Female"?"♀":"♂"} {patient.gender}
                  </span>
                )}
                {patient.blood_group && (
                  <span className="vp-chip" style={{ background:"#fff5f5", color:"#dc2626", border:"1px solid #fca5a5" }}>
                    🩸 {patient.blood_group}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="vp-info-grid">
            <InfoCell label="Date of Birth"     value={patient.date_of_birth} />
            <InfoCell label="Age"               value={calculateAge(patient.date_of_birth, patient.age)} />
            <InfoCell label="Mobile"            value={patient.mobile} accent="#0f4270" />
            <InfoCell label="Email"             value={patient.email} />
            <InfoCell label="Marital Status"    value={patient.marital_status} />
            <InfoCell label="Profession"        value={patient.profession} />
            <InfoCell label="Referred By"       value={patient.referred_by} />
            <InfoCell label="Registration Date" value={patient.date} />
            <InfoCell label="Address"           value={patient.address} wide />
          </div>
        </Card>

        {/* ══════════ VISIT DETAILS / CHIEF COMPLAINT ══════════ */}
        <Card badge="Visit Details — Chief Complaint" badgeColor="#0e7490" badgeBg="#ecfeff" icon="🩺" delay="vp-d2" extra="vp-card-teal">
          {chiefComplaint ? (
            <p style={{ fontSize:14.5, color:"#1a2540", lineHeight:1.8,
              fontStyle:"italic", borderLeft:"3px solid #0e7490", paddingLeft:14 }}>
              "{chiefComplaint}"
            </p>
          ) : (
            <p style={{ color:"#94a3b8", fontSize:13.5 }}>No chief complaint recorded.</p>
          )}
        </Card>

        {/* ══════════ FAMILY DOCTOR ══════════ */}
        {(familyDoc?.doctor_name || familyDoc?.doctor_phone) && (
          <Card badge="Family Doctor" badgeColor="#7c3aed" badgeBg="#f5f3ff" icon="👨‍⚕️" delay="vp-d2">
            <div className="vp-info-grid">
              <InfoCell label="Doctor Name"    value={familyDoc.doctor_name} />
              <InfoCell label="Doctor Phone"   value={familyDoc.doctor_phone} accent="#7c3aed" />
              <InfoCell label="Doctor Address" value={familyDoc.doctor_address} wide />
            </div>
          </Card>
        )}

        {/* ══════════ MEDICAL HISTORY ══════════ */}
        <Card badge="Medical History" badgeColor="#dc2626" badgeBg="#fff5f5" icon="📋" delay="vp-d3" extra="vp-card-red">
          <DoctorMedicalSummary data={medical} />
        </Card>

        {/* ══════════ ALLERGY RECORDS ══════════ */}
        <Card badge="Allergy Records" badgeColor="#d97706" badgeBg="#fffbeb" icon="⚠️" delay="vp-d3" extra="vp-card-amber">
          {allergyRows.length === 0 ? (
            <div style={{ textAlign:"center", padding:"22px 0", background:"#fafbff",
              borderRadius:10, border:"1.5px dashed #dde8f8", color:"#94a3b8", fontSize:13.5 }}>
              No known allergies recorded.
            </div>
          ) : (
            <div className="vp-table-wrap">
              <table className="vp-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Allergen / Substance</th>
                    <th>Reaction</th>
                    <th>Severity</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {allergyRows.map((row,i) => (
                    <tr key={row.id||i}>
                      <td style={{ fontWeight:600, color:"#0b2d4e" }}>{row.type||"—"}</td>
                      <td style={{ fontWeight:600 }}>{row.allergen||"—"}</td>
                      <td>{row.reaction||"—"}</td>
                      <td><SevPill s={row.severity} /></td>
                      <td style={{ color:"#64748b", fontSize:12.5 }}>{row.notes||"—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* ══════════ HABITS ══════════ */}
        <Card badge="Personal Habits" badgeColor="#0d6e4a" badgeBg="#f0fdf4" icon="🧬" delay="vp-d4" extra="vp-card-green">
          <DoctorHabitsSummary data={habits} />
        </Card>

        {/* ══════════ WOMEN'S HEALTH ══════════ */}
        {patient.gender === "Female" && (
          <Card badge="Women's Health" badgeColor="#be185d" badgeBg="#fdf2f8" icon="🌸" delay="vp-d4">
            <DoctorWomenSummary data={women} />
          </Card>
        )}

        {/* ══════════ CONSENT RECORD ══════════ */}
        {consent?.agreed && (
          <Card badge="Consent Record" badgeColor="#0e7490" badgeBg="#ecfeff" icon="✍️" delay="vp-d4">
            <div className="vp-info-grid">
              <div className="vp-info-cell" style={{ gridColumn:"span 2", background:"#f0fdfa", border:"1px solid #99f6e4" }}>
                <div className="vp-info-label">Consent Status</div>
                <div style={{ display:"flex", alignItems:"center", gap:8, marginTop:4 }}>
                  <span style={{ width:20, height:20, borderRadius:5, background:"#0d9488",
                    display:"inline-flex", alignItems:"center", justifyContent:"center" }}>
                    <svg width="11" height="9" viewBox="0 0 12 10" fill="none">
                      <path d="M1.5 5L4.5 8L10.5 2" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                  <span style={{ fontSize:14, fontWeight:700, color:"#0d6e4a" }}>Consent Acknowledged</span>
                </div>
              </div>
              <InfoCell label="Signed By"               value={consent.signature} />
              <InfoCell label="Relationship to Patient" value={consent.relationship} />
              <InfoCell label="Date of Consent"         value={consent.consent_date} />
            </div>
          </Card>
        )}

        {/* ══════════ DENTAL SECTION HEADER ══════════ */}
        <div style={{
          display:"flex", alignItems:"center", gap:14,
          margin:"32px 0 20px", padding:"16px 22px",
          background:"linear-gradient(135deg,#0b2d4e,#0f4270)",
          borderRadius:14, boxShadow:"0 4px 16px rgba(11,45,78,0.2)",
        }}>
          <div style={{ width:36, height:36, borderRadius:9, background:"rgba(255,255,255,0.12)",
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>🦷</div>
          <div>
            <p style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:20,
              fontWeight:700, color:"#fff", lineHeight:1.2 }}>Clinical Dental Modules</p>
            <p style={{ fontSize:11.5, color:"rgba(255,255,255,0.55)", marginTop:2 }}>
              {isClosed ? "Read-only — visit is closed" : "Active session — all modules editable"}
            </p>
          </div>
          {isClosed && (
            <span style={{
              marginLeft:"auto", background:"rgba(252,165,165,0.2)",
              border:"1px solid rgba(252,165,165,0.4)",
              color:"#fca5a5", fontSize:12, fontWeight:700, padding:"5px 14px", borderRadius:20,
            }}>🔒 CLOSED</span>
          )}
        </div>

        {/* ══════════ DENTAL MODULES ══════════ */}
        {/* ── DentalChart: onRecordsChange lifts records up ── */}
        <Module icon="📊" title="Dental Chart" sub="Clinical charting data" bg="#f0fdf4" delay="vp-d5">
          <DentalChart
            visitId={visitId}
            disabled={isClosed}
            onRecordsChange={setChartRecords}
          />
        </Module>

        {/* ── Findings: onFindingsChange lifts findings up ── */}
        <Module icon="🔍" title="Findings" sub="Clinical examination findings" bg="#fffbeb" delay="vp-d5">
          <Findings
            visitId={visitId}
            disabled={isClosed}
            onFindingsChange={setFindings}
          />
        </Module>

        {/* ── Consultation: receives both for auto-filling Diagnosis ── */}
        <Module icon="💬" title="Consultation" sub="Doctor's notes & advice" bg="#f5f3ff" delay="vp-d5">
          <Consultation
            visitId={visitId}
            disabled={isClosed}
            dentalChartLog={chartRecords}
            otherFindings={findings}
          />
        </Module>

        <Module icon="💊" title="Prescription" sub="Medications & dosage" bg="#fff5f5" delay="vp-d6">
          <Prescription visitId={visitId} disabled={isClosed}
            patient={patient ? { name: patient.name, age: patient.age, case_number: patient.case_number, gender: patient.gender, mobile: patient.mobile || "" } : null}
            consultationData={latestConsultation}
          />
        </Module>

        <Module icon="🖼️" title="Image Upload" sub="X-rays & clinical photos" bg="#ecfeff" delay="vp-d6">
          <ImageUpload visitId={visitId} disabled={isClosed} />
        </Module>

        {/* ══════════ BOTTOM ACTIONS ══════════ */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", paddingTop:10 }}>
          <button
            style={{
              display:"inline-flex", alignItems:"center", gap:8,
              padding:"11px 22px", borderRadius:10,
              background:"transparent", color:"#4a5578",
              border:"1.5px solid #dde5f4",
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              fontSize:13.5, fontWeight:600, cursor:"pointer", transition:"all 0.18s",
            }}
            onClick={() => navigate(-1)}
          >
            ← Back
          </button>

          {!isClosed ? (
            <button className="vp-close-btn" onClick={() => setShowBillingDlg(true)} disabled={closing}>
              {closing ? "Closing…" : "🔒 Close Visit"}
            </button>
          ) : (
            <span className="vp-chip" style={{
              background:"#f1f5f9", color:"#64748b",
              border:"1px solid #cbd5e1", padding:"11px 20px",
              fontSize:13, fontWeight:600,
            }}>
              🔒 Visit Closed
            </span>
          )}
        </div>


      {/* ══════════ BILLING INSTRUCTIONS MODAL ══════════ */}
      {showBillingDlg && (
        <BillingInstructionsModal
          visit={visit}
          patient={patient}
          onConfirm={handleCloseVisit}
          onCancel={() => setShowBillingDlg(false)}
        />
      )}

      </div>
    </div>
  );
}