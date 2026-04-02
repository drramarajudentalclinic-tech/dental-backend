import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/api";

import DoctorMedicalSummary from "../components/doctor/DoctorMedicalSummary";
import DoctorAllergySummary from "../components/doctor/DoctorAllergySummary";
import DoctorHabitsSummary from "../components/doctor/DoctorHabitsSummary";
import DoctorWomenSummary from "../components/doctor/DoctorWomenSummary";

const injectStyles = () => {
  if (document.getElementById("dpv-styles")) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href =
    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap";
  document.head.appendChild(link);

  const s = document.createElement("style");
  s.id = "dpv-styles";
  s.textContent = `
    .dpv-card {
      background: #fff;
      border-radius: 16px;
      border: 1px solid rgba(220,230,245,0.9);
      box-shadow: 0 2px 8px rgba(15,50,100,0.05), 0 8px 28px rgba(15,50,100,0.06);
      padding: 26px 30px;
      margin-bottom: 20px;
    }
    .dpv-badge {
      display: inline-flex; align-items: center; gap: 7px;
      font-size: 10px; font-weight: 800; letter-spacing: 1.4px;
      text-transform: uppercase; padding: 4px 12px;
      border-radius: 20px; margin-bottom: 18px;
    }
    .dpv-info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }
    .dpv-info-cell {
      background: #f7f9fe;
      border: 1px solid #edf1fa;
      border-radius: 10px;
      padding: 12px 14px;
    }
    .dpv-info-label {
      font-size: 10.5px; font-weight: 700; color: #8899bb;
      letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 4px;
    }
    .dpv-info-value {
      font-size: 14px; font-weight: 600; color: #1a2540;
      line-height: 1.3;
    }
    .dpv-section-title {
      display: flex; align-items: center; gap: 9px;
      font-size: 13px; font-weight: 700; color: #1a2540;
      margin-bottom: 14px;
    }
    .dpv-section-title::before {
      content: ''; width: 3px; height: 16px; border-radius: 2px; flex-shrink: 0;
      background: linear-gradient(180deg, #2563eb, #60a5fa);
    }
    .dpv-alert-pill {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 7px 14px; border-radius: 9px;
      font-size: 12.5px; font-weight: 700;
    }
    .dpv-table { width: 100%; border-collapse: collapse; }
    .dpv-table thead tr { background: linear-gradient(90deg, #1e3a6e 0%, #2563eb 100%); }
    .dpv-table thead th {
      padding: 10px 14px; text-align: left;
      font-size: 10.5px; font-weight: 700; letter-spacing: 0.7px;
      text-transform: uppercase; color: rgba(255,255,255,0.92);
    }
    .dpv-table thead th:first-child { border-radius: 9px 0 0 0; }
    .dpv-table thead th:last-child  { border-radius: 0 9px 0 0; }
    .dpv-table tbody tr { border-bottom: 1px solid #f0f3fb; transition: background 0.15s; }
    .dpv-table tbody tr:last-child { border-bottom: none; }
    .dpv-table tbody tr:hover { background: #f7f9ff; }
    .dpv-table tbody td {
      padding: 10px 14px; font-size: 13px; color: #2d3a55; vertical-align: middle;
    }
    .dpv-table-wrap {
      border-radius: 10px; overflow: hidden;
      border: 1.5px solid #e4ecfb;
      box-shadow: 0 2px 8px rgba(37,99,235,0.06);
    }
    .dpv-sev { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
    .dpv-sev-mild   { background:#dcfce7; color:#166534; }
    .dpv-sev-mod    { background:#fef9c3; color:#854d0e; }
    .dpv-sev-sev    { background:#fee2e2; color:#991b1b; }
    .dpv-sev-life   { background:#ede9fe; color:#5b21b6; }
    .dpv-chip {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 4px 12px; border-radius: 20px;
      font-size: 11.5px; font-weight: 600;
    }
    .dpv-back-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 11px 22px; border-radius: 10px;
      background: transparent; color: #4a5578;
      border: 1.5px solid #dde5f4;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 13.5px; font-weight: 600; cursor: pointer;
      transition: all 0.18s;
    }
    .dpv-back-btn:hover { background: #f0f4fc; color: #1a2540; border-color: #b8c8e8; }
    .dpv-close-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 12px 28px; border-radius: 10px;
      background: linear-gradient(135deg, #dc2626, #ef4444);
      color: #fff; border: none;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 14px; font-weight: 700; cursor: pointer;
      box-shadow: 0 4px 14px rgba(220,38,38,0.3);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .dpv-close-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(220,38,38,0.36); }
    .dpv-close-btn:disabled { opacity: 0.65; cursor: not-allowed; }

    .dpv-followup-block {
      background: linear-gradient(135deg, #fffbeb, #fff8e1);
      border: 1.5px solid #fde68a;
      border-radius: 10px;
      padding: 14px 18px;
      margin-top: 10px;
    }
    .dpv-followup-label {
      font-size: 10px; font-weight: 800; color: #92400e;
      letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 6px;
      display: flex; align-items: center; gap: 6px;
    }
    .dpv-followup-text {
      font-size: 14px; color: #78350f; line-height: 1.7;
      font-style: italic; white-space: pre-wrap;
    }

    .dpv-complaint-block {
      background: #f0fdfe;
      border-left: 3px solid #0e7490;
      border-radius: 0 10px 10px 0;
      padding: 12px 16px;
    }
    .dpv-complaint-text {
      font-size: 14.5px; color: #1a2540; line-height: 1.75; font-style: italic;
    }

    .dpv-empty-field {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 8px 14px; border-radius: 8px;
      background: #f8faff; border: 1.5px dashed #d0ddf8;
      font-size: 12.5px; color: #94a3b8; font-style: italic;
    }

    /* ── Billing Instructions Modal ── */
    .dpv-billing-overlay {
      position: fixed; inset: 0; z-index: 2000;
      background: rgba(10,25,55,0.6);
      backdrop-filter: blur(5px);
      display: flex; align-items: center; justify-content: center;
      animation: dpv-fade 0.2s both;
    }
    @keyframes dpv-fade { from{opacity:0} to{opacity:1} }
    .dpv-billing-modal {
      background: #fff; border-radius: 20px;
      width: 95%; max-width: 600px; max-height: 92vh; overflow-y: auto;
      box-shadow: 0 28px 80px rgba(10,25,55,0.3);
      animation: dpv-modal-in 0.25s cubic-bezier(.22,.68,0,1.2) both;
    }
    @keyframes dpv-modal-in {
      from { opacity:0; transform: translateY(22px) scale(0.97); }
      to   { opacity:1; transform: none; }
    }
    .dpv-billing-modal-hd {
      padding: 22px 28px 16px;
      background: linear-gradient(135deg, #0b2d4e, #1d6fa4);
      border-radius: 20px 20px 0 0;
      display: flex; align-items: center; justify-content: space-between;
    }
    .dpv-billing-modal-body { padding: 22px 28px 28px; }
    .dpv-billing-note-box {
      background: #fffbeb;
      border: 1.5px solid #fde68a;
      border-radius: 12px;
      padding: 16px 18px;
    }
    .dpv-billing-note-textarea {
      width: 100%; padding: 12px 14px;
      border: 1.5px solid #fde68a; border-radius: 10px;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 13.5px; color: #78350f;
      background: #fffdf5; outline: none;
      resize: vertical; min-height: 100px;
      transition: border-color 0.18s, box-shadow 0.18s;
      box-sizing: border-box;
    }
    .dpv-billing-note-textarea:focus {
      border-color: #f59e0b;
      box-shadow: 0 0 0 3px rgba(245,158,11,0.15);
      background: #fffef7;
    }
    .dpv-billing-note-textarea::placeholder { color: #c4a35a; font-style: italic; }
    .dpv-clinical-summary-block {
      background: #f0f7ff;
      border: 1px solid #bfdbfe;
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 18px;
    }
    .dpv-confirm-btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      padding: 13px 28px; border-radius: 11px;
      background: linear-gradient(135deg, #dc2626, #ef4444);
      color: #fff; border: none;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 14px; font-weight: 700; cursor: pointer;
      box-shadow: 0 4px 14px rgba(220,38,38,0.3);
      transition: transform 0.15s, box-shadow 0.15s;
      flex: 2;
    }
    .dpv-confirm-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(220,38,38,0.38); }
    .dpv-confirm-btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .dpv-spinner {
      width: 16px; height: 16px; border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.35);
      border-top-color: #fff;
      animation: dpv-spin 0.7s linear infinite; display: inline-block;
    }
    @keyframes dpv-spin { to { transform: rotate(360deg); } }

    @keyframes dpv-in { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    .dpv-animate { animation: dpv-in 0.45s cubic-bezier(.22,.68,0,1.1) both; }
    .dpv-d1 { animation-delay: 0.04s; }
    .dpv-d2 { animation-delay: 0.08s; }
    .dpv-d3 { animation-delay: 0.12s; }
    .dpv-d4 { animation-delay: 0.16s; }
    .dpv-d5 { animation-delay: 0.20s; }
    .dpv-d6 { animation-delay: 0.24s; }

    @keyframes dpv-pulse-alert { 0%,100%{box-shadow:0 0 0 0 rgba(220,38,38,0.3);} 50%{box-shadow:0 0 0 6px rgba(220,38,38,0);} }
    .dpv-alert-pulse { animation: dpv-pulse-alert 2.2s ease-in-out infinite; }
  `;
  document.head.appendChild(s);
};

const medFlag = (data, ...keys) => {
  for (const k of keys) {
    const v = data?.[k];
    if (v === true || v === 1 || v === "YES" || v === "yes") return true;
  }
  return false;
};

const InfoCell = ({ label, value, wide, accent }) => (
  <div className="dpv-info-cell" style={wide ? { gridColumn: "span 2" } : {}}>
    <div className="dpv-info-label">{label}</div>
    <div className="dpv-info-value" style={accent ? { color: accent } : {}}>
      {value || <span style={{ color: "#c0cce0", fontWeight: 400, fontSize: 13 }}>Not provided</span>}
    </div>
  </div>
);

const Section = ({ badge, badgeColor, badgeBg, icon, children, delay = "" }) => (
  <div className={`dpv-card dpv-animate ${delay}`}>
    {badge && (
      <div className="dpv-badge" style={{ background: badgeBg || "#eff4ff", color: badgeColor || "#1d4ed8", border: `1px solid ${badgeColor || "#1d4ed8"}22` }}>
        {icon && <span style={{ fontSize: 12 }}>{icon}</span>}
        {badge}
      </div>
    )}
    {children}
  </div>
);

const SevPill = ({ s }) => {
  const map = {
    "Mild": "dpv-sev-mild", "Moderate": "dpv-sev-mod",
    "Severe": "dpv-sev-sev", "Life-threatening": "dpv-sev-life",
  };
  return s ? <span className={`dpv-sev ${map[s] || "dpv-sev-mod"}`}>{s}</span> : <span style={{ color: "#b0bad0" }}>—</span>;
};

/* ══════════════════════════════════════════════════════════════
   BILLING INSTRUCTIONS MODAL
   Shown when doctor clicks "Close Visit".
   Doctor reviews clinical summary and optionally types billing
   instructions before confirming the close.
══════════════════════════════════════════════════════════════ */
function BillingInstructionsModal({ visit, patient, onConfirm, onCancel }) {
  const [billingNote, setBillingNote] = useState("");
  const [saving, setSaving] = useState(false);

  const handleConfirm = async () => {
    setSaving(true);
    await onConfirm(billingNote.trim());
    setSaving(false);
  };

  return (
    <div className="dpv-billing-overlay" onClick={onCancel}>
      <div className="dpv-billing-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="dpv-billing-modal-hd">
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              width: 46, height: 46, borderRadius: 12, flexShrink: 0,
              background: "rgba(255,255,255,0.15)", border: "1.5px solid rgba(255,255,255,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22,
            }}>💰</div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#fff" }}>Close Visit & Send to Billing</div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", marginTop: 2 }}>
                {patient?.name} · {patient?.case_number ? `Case ${patient.case_number}` : ""}
              </div>
            </div>
          </div>
          <button onClick={onCancel} style={{
            width: 34, height: 34, borderRadius: 9,
            border: "1.5px solid rgba(255,255,255,0.25)", background: "rgba(255,255,255,0.12)",
            color: "#fff", fontSize: 16, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>✕</button>
        </div>

        <div className="dpv-billing-modal-body">

          {/* Info note */}
          <div style={{
            background: "#f0f8ff", border: "1px solid #bfdbfe",
            borderRadius: 10, padding: "10px 14px", marginBottom: 18,
            fontSize: 12.5, color: "#1d4d7a", lineHeight: 1.6,
          }}>
            📋 The clinical summary below will be sent to the <strong>reception billing queue</strong> automatically. You can add optional billing instructions for reception, then you'll be returned to your <strong>doctor dashboard</strong> for the next patient.
          </div>

          {/* Clinical Summary (auto-sent) */}
          {(visit?.diagnosis || visit?.treatment_done || visit?.treatment_plan || visit?.advice) && (
            <div className="dpv-clinical-summary-block">
              <div style={{ fontSize: 11, fontWeight: 800, color: "#1d4d7a", letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 10 }}>
                📋 Clinical Summary (auto-sent to billing)
              </div>
              {visit?.diagnosis      && (
                <div style={{ display: "flex", gap: 8, marginBottom: 6, fontSize: 13 }}>
                  <span style={{ fontWeight: 700, color: "#0b2d4e", minWidth: 130, flexShrink: 0 }}>Diagnosis:</span>
                  <span style={{ color: "#334155" }}>{visit.diagnosis}</span>
                </div>
              )}
              {visit?.treatment_done && (
                <div style={{ display: "flex", gap: 8, marginBottom: 6, fontSize: 13 }}>
                  <span style={{ fontWeight: 700, color: "#0b2d4e", minWidth: 130, flexShrink: 0 }}>Treatment Done:</span>
                  <span style={{ color: "#334155" }}>{visit.treatment_done}</span>
                </div>
              )}
              {visit?.treatment_plan && (
                <div style={{ display: "flex", gap: 8, marginBottom: 6, fontSize: 13 }}>
                  <span style={{ fontWeight: 700, color: "#0b2d4e", minWidth: 130, flexShrink: 0 }}>Treatment Plan:</span>
                  <span style={{ color: "#334155" }}>{visit.treatment_plan}</span>
                </div>
              )}
              {visit?.advice && (
                <div style={{ display: "flex", gap: 8, fontSize: 13 }}>
                  <span style={{ fontWeight: 700, color: "#0b2d4e", minWidth: 130, flexShrink: 0 }}>Advice:</span>
                  <span style={{ color: "#334155" }}>{visit.advice}</span>
                </div>
              )}
            </div>
          )}

          {/* Billing Instructions textarea */}
          <div className="dpv-billing-note-box" style={{ marginBottom: 22 }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#92400e", letterSpacing: "0.8px", textTransform: "uppercase", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
              <span>📝</span> Billing Instructions for Reception
              <span style={{ fontSize: 10, fontWeight: 600, color: "#b45309", background: "#fef3c7", border: "1px solid #fde68a", borderRadius: 20, padding: "1px 8px", letterSpacing: 0, textTransform: "none", marginLeft: 4 }}>Optional</span>
            </div>
            <textarea
              className="dpv-billing-note-textarea"
              placeholder="e.g. Charge RCT separately (₹3000), apply staff discount on scaling, patient has insurance — collect co-pay only, charge only consultation today…"
              value={billingNote}
              onChange={e => setBillingNote(e.target.value)}
              rows={4}
              autoFocus
            />
            <div style={{ fontSize: 11, color: "#92400e", marginTop: 6, opacity: 0.75 }}>
              💡 These notes will be prominently shown to the receptionist when generating the bill.
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={onCancel} style={{
              flex: 1, padding: 13, borderRadius: 11,
              background: "transparent", color: "#64748b",
              border: "1.5px solid #e2e8f4",
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: 14, fontWeight: 600, cursor: "pointer",
            }}>
              Cancel
            </button>
            <button
              className="dpv-confirm-btn"
              onClick={handleConfirm}
              disabled={saving}
            >
              {saving
                ? <><span className="dpv-spinner" /> Closing Visit…</>
                : "🔒 Close Visit & Return to Dashboard"
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════════ */
export default function DoctorPatientView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [patient,          setPatient]          = useState(null);
  const [visit,            setVisit]            = useState(null);
  const [medical,          setMedical]          = useState({});
  const [allergy,          setAllergy]          = useState({ rows: [] });
  const [habits,           setHabits]           = useState([]);
  const [women,            setWomen]            = useState({});
  const [familyDoc,        setFamilyDoc]        = useState({});
  const [consent,          setConsent]          = useState({});
  const [loading,          setLoading]          = useState(true);
  const [rawData,          setRawData]          = useState(null);

  // ── Billing instructions modal state ──
  const [showBillingDlg,   setShowBillingDlg]   = useState(false);
  const [closing,          setClosing]          = useState(false);

  useEffect(() => { injectStyles(); loadVisit(); }, [id]);

  const loadVisit = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/visits/${id}`);
      setRawData(res.data);
      setVisit(res.data.visit     || null);
      setPatient(res.data.patient || null);
      setMedical(res.data.medical || {});
      const raw = res.data.allergy;
      setAllergy(raw && Array.isArray(raw.rows) ? raw : { rows: [] });
      setHabits(Array.isArray(res.data.habits) ? res.data.habits : []);
      setWomen(res.data.women         || {});
      setFamilyDoc(res.data.family_doctor || {});
      setConsent(res.data.consent     || {});
    } catch (err) {
      console.error(err);
      alert("Failed to load visit data");
    } finally {
      setLoading(false);
    }
  };

  /* Called when doctor confirms close in the billing modal */
  const handleCloseVisit = async (billingNote) => {
    setClosing(true);
    try {
      await api.put(`/visits/${id}/close`, { billing_note: billingNote });
      setShowBillingDlg(false);
      // Return doctor to their dashboard for the next patient.
      // The closed visit automatically appears in the reception billing queue.
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
      const m = t.getMonth() - b.getMonth();
      if (m < 0 || (m === 0 && t.getDate() < b.getDate())) a--;
      return a + " yrs";
    }
    return manual ? manual + " yrs" : "—";
  };

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", fontFamily: "'Plus Jakarta Sans',sans-serif", color: "#64748b", fontSize: 14 }}>
      <span style={{ marginRight: 10, fontSize: 20 }}>🦷</span> Loading patient record…
    </div>
  );
  if (!patient) return (
    <div style={{ padding: 40, fontFamily: "'Plus Jakarta Sans',sans-serif", color: "#64748b" }}>Patient not found.</div>
  );

  const isClosed    = (visit?.status || "").toLowerCase() === "closed";
  const allergyRows = allergy?.rows || [];

  const chiefComplaint = (
    visit?.chief_complaint?.trim()    ||
    visit?.chiefComplaint?.trim()     ||
    visit?.complaint?.trim()          ||
    rawData?.chief_complaint?.trim()  ||
    patient?.chief_complaint?.trim()  ||
    patient?.chiefComplaint?.trim()   ||
    ""
  );

  const followupTreatment = (
    visit?.followup_treatment?.trim()   ||
    visit?.followupTreatment?.trim()    ||
    visit?.followup?.trim()             ||
    visit?.treatment_notes?.trim()      ||
    visit?.notes?.trim()                ||
    rawData?.followup_treatment?.trim() ||
    ""
  );

  const alerts = [];
  if (medFlag(medical, "bp_high",        "Blood_Pressure_High")) alerts.push({ icon: "🔴", text: "Known Hypertension",                 color: "#991b1b", bg: "#fee2e2" });
  if (medFlag(medical, "bp_low",         "Blood_Pressure_Low"))  alerts.push({ icon: "🟠", text: "Low Blood Pressure",                 color: "#92400e", bg: "#fff7ed" });
  if (medFlag(medical, "diabetes",       "Diabetes"))             alerts.push({ icon: "🔴", text: "Known Diabetes",                    color: "#991b1b", bg: "#fee2e2" });
  if (medFlag(medical, "heart_problems", "Heart_Problems"))       alerts.push({ icon: "🔴", text: "Cardiac Risk",                      color: "#991b1b", bg: "#fee2e2" });
  if (women?.pregnant)                                             alerts.push({ icon: "🔴", text: "Pregnant Patient",                  color: "#86198f", bg: "#fdf4ff" });
  if (allergyRows.some(r => r.severity === "Life-threatening"))   alerts.push({ icon: "🟣", text: "Life-threatening Allergy on Record", color: "#5b21b6", bg: "#ede9fe" });

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(150deg, #eef2fb 0%, #e6ecf8 55%, #dde8f5 100%)",
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      padding: "0 0 60px",
    }}>

      {/* ══════════ CLINIC HEADER STRIP ══════════ */}
      <div style={{
        background: "linear-gradient(135deg, #0b2d4e 0%, #0f4270 50%, #1059a0 100%)",
        padding: "20px 36px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        boxShadow: "0 4px 20px rgba(11,45,78,0.25)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10, flexShrink: 0,
            background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20,
          }}>🦷</div>
          <div>
            <p style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 18, fontWeight: 700, color: "#fff", lineHeight: 1.2 }}>
              Sri Satya Sai Oral Health Center & Dental Clinic
            </p>
            <p style={{ fontSize: 11.5, color: "rgba(255,255,255,0.65)", marginTop: 2 }}>
              Dr. Rama Raju · MDS &nbsp;|&nbsp; Doctor's Patient View
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button className="dpv-back-btn"
            style={{ background: "rgba(255,255,255,0.08)", borderColor: "rgba(255,255,255,0.2)", color: "#e2eaf8" }}
            onClick={() => navigate(-1)}>
            ← Back
          </button>
          {!isClosed && (
            <button
              className="dpv-close-btn"
              disabled={closing}
              onClick={() => setShowBillingDlg(true)}
            >
              {closing
                ? <><span className="dpv-spinner" style={{ width: 14, height: 14, borderColor: "rgba(255,255,255,0.3)", borderTopColor: "#fff" }} /> Closing…</>
                : "🔒 Close Visit"
              }
            </button>
          )}
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "32px auto 0", padding: "0 24px" }}>

        {/* ══════════ MEDICAL ALERTS ══════════ */}
        {alerts.length > 0 && (
          <div className="dpv-card dpv-animate dpv-alert-pulse" style={{
            background: "linear-gradient(135deg, #fff5f5, #fff)",
            border: "2px solid #fca5a5",
            marginBottom: 22,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div style={{ width: 34, height: 34, borderRadius: 9, background: "#fee2e2", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17 }}>🚨</div>
              <div>
                <p style={{ fontSize: 11, fontWeight: 800, letterSpacing: "1.2px", textTransform: "uppercase", color: "#dc2626" }}>Medical Alerts</p>
                <p style={{ fontSize: 12, color: "#7f1d1d", marginTop: 1 }}>Review before proceeding with any procedure</p>
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {alerts.map((a, i) => (
                <div key={i} className="dpv-alert-pill" style={{ background: a.bg, color: a.color, border: `1px solid ${a.color}33` }}>
                  <span>{a.icon}</span> {a.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════ PATIENT IDENTITY CARD ══════════ */}
        <Section badge="Patient Information" badgeColor="#0f4270" badgeBg="#eff4ff" icon="👤" delay="dpv-d1">
          <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 22 }}>
            <div style={{
              width: 60, height: 60, borderRadius: 14, flexShrink: 0,
              background: `linear-gradient(135deg, ${patient.gender === "Female" ? "#be185d, #db2777" : "#0f4270, #1d6fa4"})`,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#fff", fontSize: 24, fontWeight: 700,
              boxShadow: "0 4px 14px rgba(15,66,112,0.25)",
            }}>
              {(patient.name || "?")[0].toUpperCase()}
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: 28, fontWeight: 700, color: "#0b2540", lineHeight: 1.2 }}>
                {patient.name || "—"}
              </h2>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 7 }}>
                {patient.case_number && (
                  <span className="dpv-chip" style={{ background: "#eff4ff", color: "#1d4ed8", border: "1px solid #c7d9fc" }}>
                    📁 Case: {patient.case_number}
                  </span>
                )}
                {patient.gender && (
                  <span className="dpv-chip" style={{ background: patient.gender === "Female" ? "#fdf2f8" : "#eff4ff", color: patient.gender === "Female" ? "#be185d" : "#1d4d7a", border: "1px solid currentColor" }}>
                    {patient.gender === "Female" ? "♀" : "♂"} {patient.gender}
                  </span>
                )}
                {isClosed
                  ? <span className="dpv-chip" style={{ background: "#f1f5f9", color: "#64748b", border: "1px solid #cbd5e1" }}>🔒 Visit Closed</span>
                  : <span className="dpv-chip" style={{ background: "#f0fdf4", color: "#166534", border: "1px solid #86efac" }}>🟢 Active Visit</span>
                }
              </div>
            </div>
            {(visit?.date || visit?.visit_date) && (
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <p style={{ fontSize: 10.5, fontWeight: 700, color: "#8899bb", letterSpacing: "0.8px", textTransform: "uppercase" }}>Visit Date</p>
                <p style={{ fontSize: 15, fontWeight: 700, color: "#1a2540", marginTop: 3 }}>
                  {new Date(visit.visit_date || visit.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </p>
              </div>
            )}
          </div>

          <div className="dpv-info-grid">
            <InfoCell label="Date of Birth"     value={patient.date_of_birth} />
            <InfoCell label="Age"               value={calculateAge(patient.date_of_birth, patient.age)} />
            <InfoCell label="Mobile"            value={patient.mobile} accent="#0f4270" />
            <InfoCell label="Email"             value={patient.email} />
            <InfoCell label="Blood Group"       value={patient.blood_group} accent="#dc2626" />
            <InfoCell label="Marital Status"    value={patient.marital_status} />
            <InfoCell label="Profession"        value={patient.profession} />
            <InfoCell label="Referred By"       value={patient.referred_by} />
            <InfoCell label="Registration Date" value={patient.date} />
            <InfoCell label="Address"           value={patient.address} wide />
          </div>
        </Section>

        {/* ══════════════════════════════════════════════
            CHIEF COMPLAINT + FOLLOWUP TREATMENT
        ══════════════════════════════════════════════ */}
        <Section badge="Visit Reason & Followup Notes" badgeColor="#0e7490" badgeBg="#ecfeff" icon="🩺" delay="dpv-d2">
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* ── Chief Complaint ── */}
            <div>
              <div style={{
                fontSize: 10.5, fontWeight: 700, color: "#0e7490",
                letterSpacing: "0.9px", textTransform: "uppercase",
                marginBottom: 10, display: "flex", alignItems: "center", gap: 6,
              }}>
                <span>🩺</span> Chief Complaint
              </div>

              {chiefComplaint ? (
                <div className="dpv-complaint-block">
                  <p className="dpv-complaint-text">"{chiefComplaint}"</p>
                </div>
              ) : (
                <div style={{
                  padding: "14px 18px",
                  background: "#f8faff",
                  border: "1.5px dashed #cdd9f0",
                  borderRadius: 10,
                  display: "flex", alignItems: "center", gap: 10,
                }}>
                  <span style={{ fontSize: 18, opacity: 0.4 }}>🩺</span>
                  <div>
                    <p style={{ fontSize: 13, color: "#64748b", fontWeight: 600 }}>No chief complaint recorded</p>
                    <p style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>This may be a followup visit or the field was left empty at reception.</p>
                  </div>
                </div>
              )}
            </div>

            {/* ── Followup / Treatment Notes ── */}
            <div>
              <div style={{
                fontSize: 10.5, fontWeight: 700, color: "#92400e",
                letterSpacing: "0.9px", textTransform: "uppercase",
                marginBottom: 10, display: "flex", alignItems: "center", gap: 6,
              }}>
                <span>🔄</span> Followup / Treatment Notes
                <span style={{
                  fontSize: 9.5, fontWeight: 700, color: "#b45309",
                  background: "#fef9ee", border: "1px solid #fde68a",
                  padding: "1px 8px", borderRadius: 20, letterSpacing: "0.6px",
                }}>FROM RECEPTION</span>
              </div>

              {followupTreatment ? (
                <div className="dpv-followup-block">
                  <p className="dpv-followup-text">{followupTreatment}</p>
                </div>
              ) : (
                <div style={{
                  padding: "14px 18px",
                  background: "#fffdf5",
                  border: "1.5px dashed #fde68a",
                  borderRadius: 10,
                  display: "flex", alignItems: "center", gap: 10,
                }}>
                  <span style={{ fontSize: 18, opacity: 0.4 }}>🔄</span>
                  <div>
                    <p style={{ fontSize: 13, color: "#92400e", fontWeight: 600 }}>No followup notes recorded</p>
                    <p style={{ fontSize: 12, color: "#b45309", marginTop: 2 }}>Reception did not add any continuing treatment notes for this visit.</p>
                  </div>
                </div>
              )}
            </div>

          </div>
        </Section>

        {/* ══════════ FAMILY DOCTOR ══════════ */}
        {(familyDoc?.doctor_name || familyDoc?.doctor_phone) && (
          <Section badge="Family Doctor" badgeColor="#7c3aed" badgeBg="#f5f3ff" icon="👨‍⚕️" delay="dpv-d2">
            <div className="dpv-info-grid">
              <InfoCell label="Doctor Name"    value={familyDoc.doctor_name} />
              <InfoCell label="Doctor Phone"   value={familyDoc.doctor_phone} accent="#7c3aed" />
              <InfoCell label="Doctor Address" value={familyDoc.doctor_address} wide />
            </div>
          </Section>
        )}

        {/* ══════════ MEDICAL HISTORY ══════════ */}
        <Section badge="Medical History" badgeColor="#dc2626" badgeBg="#fff5f5" icon="📋" delay="dpv-d3">
          <DoctorMedicalSummary data={medical} />
        </Section>

        {/* ══════════ ALLERGY RECORDS TABLE ══════════ */}
        <Section badge="Allergy Records" badgeColor="#d97706" badgeBg="#fffbeb" icon="⚠️" delay="dpv-d3">
          {allergyRows.length === 0 ? (
            <div style={{ textAlign: "center", padding: "24px 0", background: "#fafbff", borderRadius: 10, border: "1.5px dashed #dde8f8", color: "#94a3b8", fontSize: 13.5 }}>
              No known allergies recorded.
            </div>
          ) : (
            <div className="dpv-table-wrap">
              <table className="dpv-table">
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
                  {allergyRows.map((row, i) => (
                    <tr key={row.id || i}>
                      <td style={{ fontWeight: 600, color: "#0b2d4e" }}>{row.type || "—"}</td>
                      <td style={{ fontWeight: 600 }}>{row.allergen || "—"}</td>
                      <td>{row.reaction || "—"}</td>
                      <td><SevPill s={row.severity} /></td>
                      <td style={{ color: "#64748b", fontSize: 12.5 }}>{row.notes || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* ══════════ HABITS ══════════ */}
        <Section badge="Personal Habits" badgeColor="#0d6e4a" badgeBg="#f0fdf4" icon="🧬" delay="dpv-d4">
          <DoctorHabitsSummary data={habits} />
        </Section>

        {/* ══════════ WOMEN'S HEALTH (if Female) ══════════ */}
        {patient.gender === "Female" && (
          <Section badge="Women's Health" badgeColor="#be185d" badgeBg="#fdf2f8" icon="🌸" delay="dpv-d4">
            <DoctorWomenSummary data={women} />
          </Section>
        )}

        {/* ══════════ CONSENT RECORD ══════════ */}
        {consent?.agreed && (
          <Section badge="Consent Record" badgeColor="#0e7490" badgeBg="#ecfeff" icon="✍️" delay="dpv-d5">
            <div className="dpv-info-grid">
              <div className="dpv-info-cell" style={{ gridColumn: "span 2", background: "#f0fdfa", border: "1px solid #99f6e4" }}>
                <div className="dpv-info-label">Consent Status</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                  <span style={{ width: 20, height: 20, borderRadius: 5, background: "#0d9488", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
                    <svg width="11" height="9" viewBox="0 0 12 10" fill="none"><path d="M1.5 5L4.5 8L10.5 2" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: "#0d6e4a" }}>Consent Acknowledged</span>
                </div>
              </div>
              <InfoCell label="Signed By"               value={consent.signature} />
              <InfoCell label="Relationship to Patient" value={consent.relationship} />
              <InfoCell label="Date of Consent"         value={consent.consent_date} />
            </div>
          </Section>
        )}

        {/* ══════════ BOTTOM ACTIONS ══════════ */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8 }}>
          <button className="dpv-back-btn" onClick={() => navigate(-1)}>
            ← Back to List
          </button>
          {!isClosed && (
            <button
              className="dpv-close-btn"
              disabled={closing}
              onClick={() => setShowBillingDlg(true)}
            >
              {closing
                ? <><span className="dpv-spinner" style={{ width: 14, height: 14, borderColor: "rgba(255,255,255,0.3)", borderTopColor: "#fff" }} /> Closing…</>
                : "🔒 Close Visit"
              }
            </button>
          )}
          {isClosed && (
            <span className="dpv-chip" style={{ background: "#f1f5f9", color: "#64748b", border: "1px solid #cbd5e1", padding: "10px 18px", fontSize: 13, fontWeight: 600 }}>
              🔒 This visit has been closed
            </span>
          )}
        </div>

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
  );
}