import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/api";

import PatientMedical from "../components/PatientMedical";
import PatientHabits from "../components/PatientHabits";
import PatientWomen from "../components/PatientWomen";

/* ═══════════════════════════════════════════
   GLOBAL STYLES
═══════════════════════════════════════════ */
const GlobalStyles = () => {
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap";
    document.head.appendChild(link);

    const style = document.createElement("style");
    style.textContent = `
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      .rpf-input, .rpf-select, .rpf-textarea {
        width: 100%;
        padding: 11px 14px;
        border: 1.5px solid #e2e8f4;
        border-radius: 9px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13.5px;
        color: #1a1f36;
        background: #fff;
        transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
        outline: none;
        appearance: none;
      }
      .rpf-input:hover, .rpf-select:hover { border-color: #b8c8e8; }
      .rpf-input:focus, .rpf-select:focus, .rpf-textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3.5px rgba(37,99,235,0.11);
        background: #fafcff;
      }
      .rpf-input::placeholder, .rpf-textarea::placeholder { color: #b0bad0; font-size: 13px; }
      .rpf-textarea { resize: vertical; min-height: 90px; line-height: 1.65; }
      .rpf-select {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236b7a99' stroke-width='1.8' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 13px center;
        cursor: pointer;
        padding-right: 36px;
      }

      /* ── Table styles ── */
      .rpf-table { width: 100%; border-collapse: collapse; }
      .rpf-table thead tr {
        background: linear-gradient(90deg, #1e40af 0%, #2563eb 100%);
      }
      .rpf-table thead th {
        padding: 11px 14px;
        text-align: left;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.9);
      }
      .rpf-table thead th:first-child { border-radius: 10px 0 0 0; }
      .rpf-table thead th:last-child  { border-radius: 0 10px 0 0; text-align: center; }
      .rpf-table tbody tr { border-bottom: 1px solid #f0f3fb; transition: background 0.15s; }
      .rpf-table tbody tr:last-child { border-bottom: none; }
      .rpf-table tbody tr:hover { background: #f7f9ff; }
      .rpf-table tbody td { padding: 9px 14px; font-size: 13.5px; color: #2d3a55; vertical-align: middle; }
      .rpf-table tbody td:last-child { text-align: center; }
      .rpf-table-wrapper {
        border-radius: 10px;
        overflow: hidden;
        border: 1.5px solid #e8edf8;
        box-shadow: 0 2px 8px rgba(37,99,235,0.06);
      }
      .tbl-input {
        width: 100%;
        padding: 7px 10px;
        border: 1.5px solid #e2e8f4;
        border-radius: 7px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px;
        color: #1a1f36;
        background: transparent;
        outline: none;
        transition: border-color 0.18s, box-shadow 0.18s;
      }
      .tbl-input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.10);
        background: #fff;
      }
      .tbl-select {
        width: 100%;
        padding: 7px 28px 7px 10px;
        border: 1.5px solid #e2e8f4;
        border-radius: 7px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px;
        color: #1a1f36;
        background: transparent url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7a99' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat right 9px center;
        appearance: none;
        outline: none;
        cursor: pointer;
        transition: border-color 0.18s;
      }
      .tbl-select:focus { border-color: #2563eb; }
      .tbl-add-btn {
        display: inline-flex; align-items: center; gap: 6px;
        margin-top: 12px;
        padding: 8px 16px;
        background: #eff4ff;
        color: #2563eb;
        border: 1.5px dashed #93b4f5;
        border-radius: 8px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px; font-weight: 600;
        cursor: pointer;
        transition: background 0.2s, border-color 0.2s;
      }
      .tbl-add-btn:hover { background: #ddeaff; border-color: #2563eb; }
      .tbl-del-btn {
        width: 28px; height: 28px;
        border: none; border-radius: 6px;
        background: #fff0f0; color: #e03e3e;
        font-size: 15px; line-height: 1;
        cursor: pointer; transition: background 0.2s;
        display: inline-flex; align-items: center; justify-content: center;
      }
      .tbl-del-btn:hover { background: #ffd5d5; }

      /* ── Buttons ── */
      .rpf-save-btn {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: #fff;
        padding: 13px 38px;
        border: none;
        border-radius: 11px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 15px; font-weight: 700;
        cursor: pointer;
        letter-spacing: 0.2px;
        box-shadow: 0 4px 18px rgba(37,99,235,0.38);
        transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
      }
      .rpf-save-btn:hover { transform: translateY(-1.5px); box-shadow: 0 8px 24px rgba(37,99,235,0.44); }
      .rpf-save-btn:active { transform: translateY(0); }
      .rpf-save-btn:disabled { opacity: 0.65; cursor: not-allowed; transform: none; }

      .rpf-cancel-btn {
        background: transparent; color: #64748b;
        padding: 13px 28px;
        border: 1.5px solid #e2e8f4;
        border-radius: 11px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 15px; font-weight: 500;
        cursor: pointer; transition: all 0.2s;
      }
      .rpf-cancel-btn:hover { background: #f5f7fc; color: #1a1f36; border-color: #c8d3ea; }

      /* ── Badge ── */
      .rpf-section-badge {
        display: inline-flex; align-items: center; gap: 7px;
        background: linear-gradient(135deg, #eff4ff, #e8f0fe);
        color: #1d4ed8;
        font-size: 10.5px; font-weight: 700;
        letter-spacing: 1.3px; text-transform: uppercase;
        padding: 5px 13px; border-radius: 20px; margin-bottom: 20px;
        border: 1px solid #c7d9fc;
      }

      /* ── Sub-heading accent ── */
      .rpf-sub-heading {
        display: flex; align-items: center; gap: 9px;
        font-size: 13px; font-weight: 700; color: #1a1f36;
        margin-bottom: 14px;
      }
      .rpf-sub-heading::before {
        content: ''; display: block;
        width: 3px; height: 16px;
        background: linear-gradient(180deg, #2563eb, #60a5fa);
        border-radius: 2px; flex-shrink: 0;
      }

      .rpf-divider { border: none; border-top: 1px solid #edf1fa; margin: 26px 0; }

      /* ── Fade-in ── */
      @keyframes rpf-fade-in {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      .rpf-card { animation: rpf-fade-in 0.45s cubic-bezier(.22,.68,0,1.2) both; }

      /* ── Progress steps ── */
      .rpf-step-circle {
        width: 26px; height: 26px; border-radius: 50%;
        background: linear-gradient(135deg, #1d4ed8, #3b82f6);
        color: #fff; font-size: 11px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3);
      }
      .rpf-step-label { font-size: 12px; font-weight: 600; color: #4a5578; }
      .rpf-step-line { width: 28px; height: 1.5px; background: #c8d8f8; }

      .rpf-label { font-size: 11.5px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; display: block; }

      /* ── Consent styles ── */
      .consent-checkbox-wrap {
        display: flex; align-items: flex-start; gap: 13px;
        margin-top: 20px;
        padding: 16px 18px;
        background: #f8faff;
        border: 1.5px solid #dde8fb;
        border-radius: 10px;
        cursor: pointer;
        transition: border-color 0.2s, background 0.2s;
      }
      .consent-checkbox-wrap:hover { border-color: #2563eb; background: #f2f7ff; }
      .consent-checkbox-wrap.checked { border-color: #2563eb; background: #eff4ff; }
      .consent-checkbox {
        width: 20px; height: 20px; min-width: 20px;
        border: 2px solid #c5d5ef;
        border-radius: 5px;
        margin-top: 1px;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s, border-color 0.2s;
        background: #fff;
      }
      .consent-checkbox.checked { background: #2563eb; border-color: #2563eb; }
      .consent-sig-line {
        border: none;
        border-bottom: 1.5px solid #b8c8e0;
        background: transparent;
        width: 100%;
        padding: 6px 2px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13.5px;
        color: #1a1f36;
        outline: none;
        transition: border-color 0.2s;
      }
      .consent-sig-line:focus { border-color: #2563eb; }
      .consent-sig-line::placeholder { color: #c0cce0; font-style: italic; }

      @keyframes spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(link);
      document.head.removeChild(style);
    };
  }, []);
  return null;
};

/* ═══════════════════════════════════════════
   FIELD WRAPPER
═══════════════════════════════════════════ */
const Field = ({ label, required, children }) => (
  <div style={{ display: "flex", flexDirection: "column" }}>
    <label className="rpf-label">
      {label}{required && <span style={{ color: "#e03e3e", marginLeft: 2 }}>*</span>}
    </label>
    {children}
  </div>
);

/* ═══════════════════════════════════════════
   CARD WRAPPER
═══════════════════════════════════════════ */
const Card = ({ badge, icon, children, delay = 0, accentColor }) => (
  <div
    className="rpf-card"
    style={{
      background: "#fff",
      borderRadius: 16,
      padding: "30px 34px",
      marginBottom: 22,
      boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(37,99,235,0.06)",
      border: `1px solid ${accentColor ? accentColor + "33" : "rgba(226,232,244,0.8)"}`,
      animationDelay: `${delay}s`,
    }}
  >
    {badge && (
      <div className="rpf-section-badge" style={accentColor ? {
        background: accentColor + "18",
        color: accentColor,
        borderColor: accentColor + "44",
      } : {}}>
        {icon && <span style={{ fontSize: 13 }}>{icon}</span>}
        {badge}
      </div>
    )}
    {children}
  </div>
);

/* ═══════════════════════════════════════════
   ALLERGY TABLE
═══════════════════════════════════════════ */
const ALLERGY_TYPES = ["Food", "Drug", "Environmental", "Insect", "Latex", "Skin", "Other"];
const SEVERITY_OPTS = ["Mild", "Moderate", "Severe", "Life-threatening"];
const REACTION_OPTS = ["Rash / Hives", "Swelling", "Anaphylaxis", "Breathing Difficulty", "Itching", "Vomiting", "Other"];
const severityColor = { Mild: "#16a34a", Moderate: "#d97706", Severe: "#dc2626", "Life-threatening": "#7c3aed" };

const emptyAllergyRow = () => ({ id: Date.now() + Math.random(), type: "", allergen: "", reaction: "", severity: "", notes: "" });

const PatientAllergyTable = ({ data, setData }) => {
  const rows = data.rows || [];
  const setRows = (r) => setData({ ...data, rows: r });
  const addRow    = () => setRows([...rows, emptyAllergyRow()]);
  const deleteRow = (id) => setRows(rows.filter((r) => r.id !== id));
  const updateRow = (id, field, value) =>
    setRows(rows.map((r) => (r.id === id ? { ...r, [field]: value } : r)));

  return (
    <div>
      <div className="rpf-sub-heading">Allergy Records</div>
      {rows.length === 0 ? (
        <div style={{
          textAlign: "center", padding: "30px 0",
          color: "#94a3b8", fontSize: 13.5,
          background: "#f8faff", borderRadius: 10,
          border: "1.5px dashed #d0ddf8",
        }}>
          No allergies recorded. Click <strong style={{ color: "#2563eb" }}>+ Add Allergy</strong> to begin.
        </div>
      ) : (
        <div className="rpf-table-wrapper">
          <table className="rpf-table">
            <thead>
              <tr>
                <th style={{ width: 130 }}>Type</th>
                <th>Allergen / Substance</th>
                <th style={{ width: 180 }}>Reaction</th>
                <th style={{ width: 160 }}>Severity</th>
                <th>Notes</th>
                <th style={{ width: 54 }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <select className="tbl-select" value={row.type} onChange={(e) => updateRow(row.id, "type", e.target.value)}>
                      <option value="">Select</option>
                      {ALLERGY_TYPES.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </td>
                  <td>
                    <input className="tbl-input" placeholder="e.g. Penicillin" value={row.allergen}
                      onChange={(e) => updateRow(row.id, "allergen", e.target.value)} />
                  </td>
                  <td>
                    <select className="tbl-select" value={row.reaction} onChange={(e) => updateRow(row.id, "reaction", e.target.value)}>
                      <option value="">Select</option>
                      {REACTION_OPTS.map((r) => <option key={r}>{r}</option>)}
                    </select>
                  </td>
                  <td>
                    <select className="tbl-select" value={row.severity}
                      onChange={(e) => updateRow(row.id, "severity", e.target.value)}
                      style={row.severity ? { color: severityColor[row.severity], fontWeight: 600, borderColor: severityColor[row.severity] } : {}}>
                      <option value="">Select</option>
                      {SEVERITY_OPTS.map((s) => <option key={s}>{s}</option>)}
                    </select>
                  </td>
                  <td>
                    <input className="tbl-input" placeholder="Additional notes…" value={row.notes}
                      onChange={(e) => updateRow(row.id, "notes", e.target.value)} />
                  </td>
                  <td>
                    <button className="tbl-del-btn" onClick={() => deleteRow(row.id)} title="Remove">✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <button className="tbl-add-btn" onClick={addRow}>
        <span style={{ fontSize: 17, lineHeight: 1 }}>+</span> Add Allergy
      </button>
    </div>
  );
};

/* ═══════════════════════════════════════════
   CONSENT SECTION
═══════════════════════════════════════════ */
const ConsentSection = ({ patientName, patientAge, consent, setConsent }) => {
  const toggle = () => setConsent((prev) => ({ ...prev, agreed: !prev.agreed }));

  const consentText = `I hereby authorise and request the performance of dental services for myself or for ${patientName ? patientName : "[Patient Name]"}, Age: ${patientAge ? patientAge : "___"}. I also give my consent to any advisable and necessary dental procedures, medications, or anesthetics to be administered by the attending dentist or by the supervised staff for diagnostic purposes or dental treatment. I understand and acknowledge that I am financially responsible for the services provided for myself or the above named.`;

  return (
    <Card badge="Patient Consent" icon="✍️" delay={0.18} accentColor="#0e7490">
      {/* Decorative header bar */}
      <div style={{
        background: "linear-gradient(135deg, #ecfeff 0%, #f0f9ff 100%)",
        border: "1px solid #a5d8f3",
        borderRadius: 10,
        padding: "16px 20px",
        marginBottom: 22,
        display: "flex",
        alignItems: "flex-start",
        gap: 14,
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
          background: "linear-gradient(135deg, #0e7490, #0891b2)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 3px 10px rgba(14,116,144,0.3)",
        }}>
          <span style={{ fontSize: 18 }}>📄</span>
        </div>
        <div>
          <p style={{ fontSize: 11, fontWeight: 700, color: "#0e7490", letterSpacing: "0.8px", textTransform: "uppercase", marginBottom: 5 }}>
            Informed Consent Statement
          </p>
          <p style={{ fontSize: 13.5, color: "#1e3a4a", lineHeight: 1.75, fontStyle: "italic" }}>
            "{consentText}"
          </p>
        </div>
      </div>

      {/* Checkbox agreement */}
      <div
        className={`consent-checkbox-wrap ${consent.agreed ? "checked" : ""}`}
        onClick={toggle}
      >
        <div className={`consent-checkbox ${consent.agreed ? "checked" : ""}`}>
          {consent.agreed && (
            <svg width="12" height="10" viewBox="0 0 12 10" fill="none">
              <path d="M1.5 5L4.5 8L10.5 2" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </div>
        <p style={{ fontSize: 13.5, color: consent.agreed ? "#1d4ed8" : "#475569", fontWeight: consent.agreed ? 600 : 400, lineHeight: 1.6, userSelect: "none" }}>
          I have read and understood the above consent statement. I agree to the terms and acknowledge my financial responsibility for dental services rendered.
        </p>
      </div>

      {/* Signature + Date row */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 24,
        marginTop: 26,
      }}>
        <div>
          <label className="rpf-label">Patient / Guardian Signature</label>
          <input
            className="consent-sig-line"
            placeholder="Sign here"
            value={consent.signature || ""}
            onChange={(e) => setConsent((prev) => ({ ...prev, signature: e.target.value }))}
          />
        </div>
        <div>
          <label className="rpf-label">Relationship to Patient</label>
          <input
            className="consent-sig-line"
            placeholder="Self / Parent / Guardian…"
            value={consent.relationship || ""}
            onChange={(e) => setConsent((prev) => ({ ...prev, relationship: e.target.value }))}
          />
        </div>
        <div>
          <label className="rpf-label">Date of Consent</label>
          <input
            type="date"
            className="consent-sig-line"
            style={{ cursor: "pointer" }}
            value={consent.consent_date || new Date().toISOString().split("T")[0]}
            onChange={(e) => setConsent((prev) => ({ ...prev, consent_date: e.target.value }))}
          />
        </div>
      </div>

      {/* Warning if not agreed */}
      {!consent.agreed && (
        <div style={{
          marginTop: 16, padding: "10px 14px",
          background: "#fffbeb", border: "1px solid #fde68a",
          borderRadius: 8, display: "flex", alignItems: "center", gap: 8,
        }}>
          <span style={{ fontSize: 15 }}>⚠️</span>
          <p style={{ fontSize: 12.5, color: "#92400e", fontWeight: 500 }}>
            Patient consent must be acknowledged before saving the record.
          </p>
        </div>
      )}
    </Card>
  );
};

/* ═══════════════════════════════════════════
   MAIN FORM
═══════════════════════════════════════════ */
export default function ReceptionPatientForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit   = Boolean(id);
  const todayDate = new Date().toISOString().split("T")[0];

  const [personal, setPersonal] = useState({
    case_number: "", name: "", date: todayDate,
    gender: "", age: "", dob: "", marital_status: "",
    mobile: "", email: "", referred_by: "",
    blood_group: "", address: "", profession: "",
  });

  const [chiefComplaint, setChiefComplaint] = useState("");
  const [familyDoctor, setFamilyDoctor]     = useState({ doctor_name: "", doctor_address: "", doctor_phone: "" });
  const [medical, setMedical]               = useState({});
  const [allergy, setAllergy]               = useState({ rows: [] });
  const [habits, setHabits]                 = useState({});
  const [women, setWomen]                   = useState({ pregnant: false, due_date: "", nursing_child: false });
  const [consent, setConsent]               = useState({
    agreed: false,
    signature: "",
    relationship: "",
    consent_date: todayDate,
  });
  const [saving, setSaving] = useState(false);

  const p  = (k) => (e) => setPersonal((prev) => ({ ...prev, [k]: e.target.value }));
  const fd = (k) => (e) => setFamilyDoctor((prev) => ({ ...prev, [k]: e.target.value }));

  /* ── Auto-calculate age from DOB ── */
  const handleDobChange = (e) => {
    const dob = e.target.value;
    let age = "";
    if (dob) {
      const today     = new Date();
      const birthDate = new Date(dob);
      let years = today.getFullYear() - birthDate.getFullYear();
      const m   = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) years--;
      age = years >= 0 ? String(years) : "";
    }
    setPersonal((prev) => ({ ...prev, dob, age }));
  };

  useEffect(() => { if (isEdit) loadPatient(); }, [id]);

  const loadPatient = async () => {
    try {
      const res = await api.get(`/patients/${id}`);
      const d   = res.data.patient || {};
      setPersonal({
        case_number: d.case_number || "", name: d.name || "",
        date: d.date || todayDate, gender: d.gender || "",
        age: d.age || "", dob: d.date_of_birth || "",
        marital_status: d.marital_status || "", mobile: d.mobile || "",
        email: d.email || "", referred_by: d.referred_by || "",
        blood_group: d.blood_group || "", address: d.address || "",
        profession: d.profession || "",
      });
      setChiefComplaint(d.chief_complaint || "");
      setMedical(res.data.medical || {});
      const rawAllergy = res.data.allergy;
      setAllergy(rawAllergy && Array.isArray(rawAllergy.rows) ? rawAllergy : { rows: [] });
      setHabits(res.data.habits || {});
      setWomen(res.data.women || {});
      setFamilyDoctor(res.data.family_doctor || {});
      if (res.data.consent) setConsent({ ...consent, ...res.data.consent });
    } catch (err) {
      console.error(err);
      alert("Failed to load patient data.");
    }
  };

  /* ══════════════════════════════════════════
     SAVE PATIENT
     FIXED: chief_complaint is now included in
     the POST and PUT payloads so it actually
     saves to the database and shows in the
     doctor view.
  ══════════════════════════════════════════ */
  const savePatient = async () => {
    if (!personal.mobile) { alert("Mobile number is required."); return; }
    if (!consent.agreed)  { alert("Patient consent must be acknowledged before saving."); return; }
    setSaving(true);
    try {
      let patientId = id;

      // Build payload that includes chief_complaint
      const patientPayload = { ...personal, chief_complaint: chiefComplaint };

      if (isEdit) {
        await api.put(`/patients/${id}`, patientPayload);
      } else {
        const res = await api.post("/patients", patientPayload);
        patientId  = res.data.patient_id;
      }
      await api.put(`/medical/${patientId}`, medical);
      await api.put(`/allergies/${patientId}`, allergy);
      await api.put(`/habits/${patientId}`, habits);
      await api.put(`/family-doctor/${patientId}`, familyDoctor);
      await api.put(`/consent/${patientId}`, consent);
      if (personal.gender === "Female") await api.put(`/women/${patientId}`, women);
      alert("Patient record saved successfully.");
      navigate("/reception");
    } catch (err) {
      console.error(err);
      alert("Failed to save patient record.");
    } finally {
      setSaving(false);
    }
  };

  const grid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 18 };

  return (
    <>
      <GlobalStyles />
      <div style={{
        minHeight: "100vh",
        background: "linear-gradient(145deg, #eef2fb 0%, #e6eaf6 60%, #dde8f8 100%)",
        padding: "38px 24px 60px",
        fontFamily: "'Plus Jakarta Sans', sans-serif",
      }}>
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>

          {/* ══ HEADER ══ */}
          <div style={{
            display: "flex", alignItems: "flex-end",
            justifyContent: "space-between", marginBottom: 34,
          }}>
            <div>
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: "linear-gradient(135deg, #1d4ed8, #3b82f6)",
                color: "#fff", fontSize: 10.5, fontWeight: 700,
                letterSpacing: "1.4px", textTransform: "uppercase",
                padding: "5px 14px", borderRadius: 20, marginBottom: 12,
                boxShadow: "0 3px 10px rgba(37,99,235,0.3)",
              }}>
                <span>🏥</span>
                {isEdit ? "Edit Mode" : "New Registration"}
              </div>
              <h1 style={{
                fontFamily: "'DM Serif Display', serif",
                fontSize: 36, color: "#0d1b3e",
                fontWeight: 400, lineHeight: 1.15,
                letterSpacing: "-0.5px",
              }}>
                {isEdit ? "Update Patient Record" : "Patient Registration"}
              </h1>
              <p style={{ marginTop: 7, color: "#64748b", fontSize: 13.5 }}>
                {isEdit
                  ? "Review and update patient information below."
                  : "Complete all sections to register a new patient."}
              </p>
            </div>

            {/* Step indicator */}
            <div style={{ display: "flex", alignItems: "center", gap: 4, paddingBottom: 6 }}>
              {[["1","Personal"], ["2","Complaint"], ["3","Medical"], ["4","Consent"]].map(([num, label], i) => (
                <div key={label} style={{ display: "flex", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                    <div className="rpf-step-circle" style={num === "4" ? { background: "linear-gradient(135deg, #0e7490, #0891b2)" } : {}}>
                      {num}
                    </div>
                    <span className="rpf-step-label">{label}</span>
                  </div>
                  {i < 3 && <div className="rpf-step-line" style={{ margin: "0 8px" }} />}
                </div>
              ))}
            </div>
          </div>

          {/* ══ PERSONAL INFORMATION ══ */}
          <Card badge="Personal Information" icon="👤" delay={0}>
            <div style={grid}>
              <Field label="Full Name" required>
                <input className="rpf-input" placeholder="e.g. Arjun Mehta" value={personal.name} onChange={p("name")} />
              </Field>
              <Field label="Case Number">
                <input className="rpf-input" placeholder="Auto / Manual" value={personal.case_number} onChange={p("case_number")} />
              </Field>
              <Field label="Registration Date">
                <input type="date" className="rpf-input" value={personal.date} onChange={p("date")} />
              </Field>
              <Field label="Gender">
                <select className="rpf-select rpf-input" value={personal.gender} onChange={p("gender")}>
                  <option value="">Select gender</option>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </Field>
              <Field label="Date of Birth">
                <input type="date" className="rpf-input" value={personal.dob} onChange={handleDobChange} max={todayDate} />
              </Field>
              <Field label="Age (Years)">
                <div style={{ position: "relative" }}>
                  <input
                    className="rpf-input"
                    placeholder="Auto-filled from DOB"
                    value={personal.age}
                    onChange={p("age")}
                    style={{ paddingRight: personal.dob ? 76 : 14 }}
                  />
                  {personal.dob && (
                    <span style={{
                      position: "absolute", right: 10, top: "50%",
                      transform: "translateY(-50%)",
                      fontSize: 10.5, fontWeight: 700, color: "#2563eb",
                      background: "#eff4ff", padding: "2px 8px",
                      borderRadius: 20, pointerEvents: "none", letterSpacing: "0.3px",
                    }}>
                      AUTO
                    </span>
                  )}
                </div>
              </Field>
              <Field label="Marital Status">
                <select className="rpf-select rpf-input" value={personal.marital_status} onChange={p("marital_status")}>
                  <option value="">Select status</option>
                  <option>Single</option>
                  <option>Married</option>
                  <option>Divorced</option>
                  <option>Widowed</option>
                </select>
              </Field>
              <Field label="Mobile Number" required>
                <input className="rpf-input" placeholder="+91 98765 43210" value={personal.mobile} onChange={p("mobile")} />
              </Field>
              <Field label="Email Address">
                <input type="email" className="rpf-input" placeholder="name@example.com" value={personal.email} onChange={p("email")} />
              </Field>
              <Field label="Blood Group">
                <select className="rpf-select rpf-input" value={personal.blood_group} onChange={p("blood_group")}>
                  <option value="">Select</option>
                  {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map((g) => <option key={g}>{g}</option>)}
                </select>
              </Field>
              <Field label="Profession">
                <input className="rpf-input" placeholder="Occupation" value={personal.profession} onChange={p("profession")} />
              </Field>
              <Field label="Referred By">
                <input className="rpf-input" placeholder="Doctor / Source" value={personal.referred_by} onChange={p("referred_by")} />
              </Field>
            </div>
            <div style={{ marginTop: 18 }}>
              <Field label="Address">
                <textarea className="rpf-textarea" placeholder="Street, City, State, PIN Code" value={personal.address} onChange={p("address")} />
              </Field>
            </div>
          </Card>

          {/* ══ CHIEF COMPLAINT ══ */}
          <Card badge="Chief Complaint" icon="🩺" delay={0.06}>
            <Field label="Primary Reason for Visit">
              <textarea
                className="rpf-textarea"
                placeholder="Describe the patient's main complaint, presenting symptoms, and duration…"
                value={chiefComplaint}
                onChange={(e) => setChiefComplaint(e.target.value)}
                style={{ minHeight: 115 }}
              />
            </Field>
          </Card>

          {/* ══ MEDICAL INFORMATION ══ */}
          <Card badge="Medical Information" icon="📋" delay={0.12}>
            <div className="rpf-sub-heading">Family Doctor Details</div>
            <div style={grid}>
              <Field label="Doctor Name">
                <input className="rpf-input" placeholder="Dr. Full Name" value={familyDoctor.doctor_name || ""} onChange={fd("doctor_name")} />
              </Field>
              <Field label="Doctor Phone">
                <input className="rpf-input" placeholder="+91 XXXXX XXXXX" value={familyDoctor.doctor_phone || ""} onChange={fd("doctor_phone")} />
              </Field>
            </div>
            <div style={{ marginTop: 16 }}>
              <Field label="Doctor Address">
                <textarea className="rpf-textarea" placeholder="Clinic / Hospital address" value={familyDoctor.doctor_address || ""} onChange={fd("doctor_address")} />
              </Field>
            </div>

            <hr className="rpf-divider" />

            <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
              <PatientMedical data={medical} setData={setMedical} />
              <PatientAllergyTable data={allergy} setData={setAllergy} />
              <PatientHabits data={habits} setData={setHabits} />
              {personal.gender === "Female" && <PatientWomen data={women} setData={setWomen} />}
            </div>
          </Card>

          {/* ══ CONSENT ══ */}
          <ConsentSection
            patientName={personal.name}
            patientAge={personal.age}
            consent={consent}
            setConsent={setConsent}
          />

          {/* ══ ACTION BUTTONS ══ */}
          <div style={{
            display: "flex", justifyContent: "flex-end",
            alignItems: "center", gap: 12, paddingTop: 4,
          }}>
            <p style={{ marginRight: "auto", fontSize: 12, color: "#94a3b8" }}>
              <span style={{ color: "#e03e3e" }}>*</span> Required fields &amp; consent must be completed before saving
            </p>
            <button className="rpf-cancel-btn" onClick={() => navigate(-1)}>
              Cancel
            </button>
            <button
              className="rpf-save-btn"
              onClick={savePatient}
              disabled={saving || !consent.agreed}
              style={!consent.agreed ? { opacity: 0.55, cursor: "not-allowed" } : {}}
            >
              {saving ? (
                <span style={{ display: "flex", alignItems: "center", gap: 9 }}>
                  <span style={{
                    width: 14, height: 14,
                    border: "2.5px solid rgba(255,255,255,0.35)",
                    borderTopColor: "#fff",
                    borderRadius: "50%",
                    display: "inline-block",
                    animation: "spin 0.7s linear infinite",
                  }} />
                  Saving…
                </span>
              ) : isEdit ? "Update Record" : "Register Patient"}
            </button>
          </div>

        </div>
      </div>
    </>
  );
}