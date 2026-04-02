import { useEffect, useState } from "react";
import api from "../api/api";

const PERMANENT = {
  upperRight: [18,17,16,15,14,13,12,11],
  upperLeft:  [21,22,23,24,25,26,27,28],
  lowerLeft:  [31,32,33,34,35,36,37,38],
  lowerRight: [48,47,46,45,44,43,42,41],
};
const DECIDUOUS = {
  upperRight: [55,54,53,52,51],
  upperLeft:  [61,62,63,64,65],
  lowerLeft:  [71,72,73,74,75],
  lowerRight: [85,84,83,82,81],
};

function todayStr() { return new Date().toISOString().split("T")[0]; }
function fmtDate(d) {
  if (!d) return "";
  const p = String(d).split("T")[0].split("-");
  if (p.length !== 3) return d;
  return `${p[2]}/${p[1]}/${p[0]}`;
}

// ── Dental Chart Modal ────────────────────────────────────────────────────────
function DentalChartModal({ onClose, onConfirm }) {
  const [chartType, setChartType] = useState("permanent");
  const [selected,  setSelected]  = useState(new Set());
  const [note,      setNote]      = useState("");
  const [date,      setDate]      = useState(todayStr());
  const chart = chartType === "permanent" ? PERMANENT : DECIDUOUS;
  const toggle = n => setSelected(p => { const s=new Set(p); s.has(n)?s.delete(n):s.add(n); return s; });
  const sorted = [...selected].sort((a,b)=>a-b);

  return (
    <div style={S.overlay}>
      <div style={S.modal}>
        <div style={S.modalHeader}>
          <span style={S.modalTitle}>🦷 Select Teeth</span>
          <button style={S.closeBtn} onClick={onClose}>✕</button>
        </div>
        <div style={S.toggleRow}>
          {["permanent","deciduous"].map(t=>(
            <button key={t} style={{...S.toggleBtn,...(chartType===t?S.toggleActive:{})}}
              onClick={()=>{setChartType(t);setSelected(new Set());}}>
              {t==="permanent"?"Permanent":"Deciduous"}
            </button>
          ))}
        </div>
        <div style={S.chartWrap}>
          <div style={S.quadrantRow}>
            <div style={S.quadrant}>{chart.upperRight.map(n=><button key={n} style={{...S.tooth,...(selected.has(n)?S.toothSel:{})}} onClick={()=>toggle(n)}>{n}</button>)}</div>
            <div style={S.dividerV}/>
            <div style={S.quadrant}>{chart.upperLeft.map(n=><button key={n} style={{...S.tooth,...(selected.has(n)?S.toothSel:{})}} onClick={()=>toggle(n)}>{n}</button>)}</div>
          </div>
          <div style={S.dividerH}/>
          <div style={S.quadrantRow}>
            <div style={S.quadrant}>{chart.lowerRight.map(n=><button key={n} style={{...S.tooth,...(selected.has(n)?S.toothSel:{})}} onClick={()=>toggle(n)}>{n}</button>)}</div>
            <div style={S.dividerV}/>
            <div style={S.quadrant}>{chart.lowerLeft.map(n=><button key={n} style={{...S.tooth,...(selected.has(n)?S.toothSel:{})}} onClick={()=>toggle(n)}>{n}</button>)}</div>
          </div>
        </div>
        {sorted.length>0&&(
          <div style={S.selectedTeeth}>
            <span style={S.selectedLabel}>IRT: </span>
            {sorted.map((n,i)=><span key={n}>{i>0?" + ":""}<span style={S.toothTag}>{n}</span></span>)}
          </div>
        )}
        <textarea style={S.modalTextarea} placeholder="Enter notes for selected teeth…"
          value={note} onChange={e=>setNote(e.target.value)}/>
        <div style={S.modalDateRow}>
          <span style={S.dateLabel}>Date:</span>
          <span style={S.autoChip}>📅 {fmtDate(todayStr())} <span style={S.autoTag}>auto</span></span>
          <div style={S.manualChip}>
            🗓 {fmtDate(date)} <span style={S.autoTag}>manual</span>
            <input type="date" value={date} onChange={e=>setDate(e.target.value)} style={S.hiddenDate}/>
          </div>
        </div>
        <div style={S.modalActions}>
          <button style={S.cancelBtnSt} onClick={onClose}>Cancel</button>
          <button style={S.okBtnSt} disabled={sorted.length===0||!note.trim()}
            onClick={()=>onConfirm({teeth:sorted,note,date,chartType})}>OK</button>
        </div>
      </div>
    </div>
  );
}

// ── Entry item (with IRT teeth display) ──────────────────────────────────────
function EntryItem({ entry, onEdit, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [text,    setText]    = useState(entry.note||"");
  const save = () => { onEdit(entry.id, text); setEditing(false); };

  const hasTeeth = entry.teeth && entry.teeth.length > 0;

  return (
    <div style={{...S.entryItem,...(entry.auto?S.entryAuto:{})}}>
      <div style={S.entryMeta}>
        <span style={S.entryDate}>📅 {fmtDate(entry.date||todayStr())}</span>
        {entry.auto&&<span style={S.autoBadge}>auto</span>}
      </div>
      {editing?(
        <div>
          <textarea style={S.editArea} value={text} onChange={e=>setText(e.target.value)} autoFocus/>
          <div style={{display:"flex",gap:6,marginTop:6}}>
            <button style={S.saveSm} onClick={save}>Save</button>
            <button style={S.cancelSm} onClick={()=>setEditing(false)}>Cancel</button>
          </div>
        </div>
      ):(
        <div style={{...S.entryText,display:"flex",alignItems:"center",gap:6,flexWrap:"wrap",paddingRight:58}}>
          <span>{entry.note}</span>
          {hasTeeth&&(
            <span style={S.entryIRT}>
              <span style={S.irtLabel}>IRT</span>
              <span style={{fontSize:12,fontWeight:600,color:"#1d4ed8",fontFamily:"'DM Mono',monospace"}}>
                {entry.teeth.join(", ")}
              </span>
            </span>
          )}
        </div>
      )}
      <div style={S.entryBtns}>
        <button style={S.iconBtn} onClick={()=>setEditing(true)} title="Edit">✏️</button>
        <button style={S.iconBtn} onClick={()=>onDelete(entry.id)} title="Delete">🗑️</button>
      </div>
    </div>
  );
}

// ── Entry section ─────────────────────────────────────────────────────────────
function EntrySection({ title, entries, onAdd, onEdit, onDelete, showChart=false, placeholder="" }) {
  const [open,      setOpen]      = useState(false);
  const [text,      setText]      = useState("");
  const [date,      setDate]      = useState(todayStr());
  const [chartOpen, setChartOpen] = useState(false);

  const handleOk = () => {
    if (!text.trim()) return;
    onAdd({ id:Date.now(), note:text.trim(), date, teeth:[] });
    setText(""); setDate(todayStr()); setOpen(false);
  };

  return (
    <div style={S.section}>
      <div style={S.sectionHeader}>
        <span style={S.sectionTitle}>{title}</span>
        <div style={{display:"flex",gap:6}}>
          {showChart&&<button style={S.addBtn} onClick={()=>setChartOpen(true)}>🦷 Chart</button>}
          <button style={S.addBtn} onClick={()=>setOpen(o=>!o)}>+ Add</button>
        </div>
      </div>
      {open&&(
        <div style={S.inputBox}>
          <textarea style={S.inputArea} placeholder={placeholder} value={text} onChange={e=>setText(e.target.value)}/>
          <div style={S.dateRow}>
            <span style={S.dateLabel}>Date:</span>
            <span style={S.autoChip}>📅 {fmtDate(todayStr())} <span style={S.autoTag}>auto</span></span>
            <div style={S.manualChip}>
              🗓 {fmtDate(date)} <span style={S.autoTag}>manual</span>
              <input type="date" value={date} onChange={e=>setDate(e.target.value)} style={S.hiddenDate}/>
            </div>
          </div>
          <div style={{display:"flex",gap:8,justifyContent:"flex-end",marginTop:8}}>
            <button style={S.cancelBtnSt} onClick={()=>setOpen(false)}>Cancel</button>
            <button style={S.okBtnSt} onClick={handleOk} disabled={!text.trim()}>OK</button>
          </div>
        </div>
      )}
      {chartOpen&&(
        <DentalChartModal onClose={()=>setChartOpen(false)}
          onConfirm={data=>{
            onAdd({id:Date.now(),note:data.note,date:data.date,teeth:data.teeth,chartType:data.chartType});
            setChartOpen(false);
          }}/>
      )}
      <div style={S.entryList}>
        {entries.map(e=>(
          <EntryItem key={e.id} entry={e} onEdit={onEdit} onDelete={onDelete}/>
        ))}
        {entries.length===0&&<div style={S.emptyMsg}>No entries yet</div>}
      </div>
    </div>
  );
}

// ── Diagnosis cell — always read-only ────────────────────────────────────────
function DiagnosisReadOnly({ text }) {
  if (!text) return <span style={{color:"#cbd5e1",fontStyle:"italic",fontSize:12}}>—</span>;
  const items = text.split(";").map(s=>s.trim()).filter(Boolean);
  return (
    <div style={{display:"flex",flexDirection:"column",gap:3}}>
      {items.map((item,i)=>(
        <div key={i} style={{display:"flex",alignItems:"flex-start",gap:5}}>
          <span style={{flexShrink:0,marginTop:5,width:5,height:5,borderRadius:"50%",
            background:"#94a3b8",display:"inline-block"}}/>
          <span style={{fontSize:12.5,color:"#1e293b",lineHeight:1.5}}>{item}</span>
        </div>
      ))}
    </div>
  );
}

// ── Read-only row (past records) ─────────────────────────────────────────────
function HistoryRowReadOnly({ r }) {
  return (
    <tr style={{background:"#fafbfc"}}>
      <td style={{fontFamily:"'DM Mono',monospace",fontSize:11.5,color:"#64748b",whiteSpace:"nowrap",verticalAlign:"top"}}>
        {fmtDate(r.created_at||r.updated_at||"")}
      </td>
      <td><DiagnosisReadOnly text={r.diagnosis}/></td>
      <td style={{fontSize:12.5,color:"#64748b",lineHeight:1.5,verticalAlign:"top",fontStyle:"italic"}}>
        {r.advice||r.treatment_plan||"—"}
      </td>
      <td style={{fontSize:12.5,color:"#64748b",lineHeight:1.5,verticalAlign:"top",fontStyle:"italic"}}>
        {r.treatment_done_today||"—"}
      </td>
      <td style={{fontFamily:"'DM Mono',monospace",fontSize:12,verticalAlign:"top",color:"#94a3b8"}}>
        {r.follow_up_date ? (
          <div>
            <div>{fmtDate(r.follow_up_date)}</div>
            {r.follow_up_time && <div style={{fontSize:10.5,color:"#64748b",fontFamily:"'DM Mono',monospace",marginTop:2}}>🕐 {r.follow_up_time}</div>}
          </div>
        ) : "—"}
      </td>
      <td style={{verticalAlign:"top"}}>
        <span style={{fontSize:10,color:"#94a3b8",background:"#f1f5f9",border:"1px solid #e2e8f0",
          borderRadius:4,padding:"2px 6px",whiteSpace:"nowrap"}}>🔒 past</span>
      </td>
    </tr>
  );
}

// ── Editable row (today's records) ───────────────────────────────────────────
function HistoryRow({ r, onSave, onDelete }) {
  const [editing,   setEditing]   = useState(false);
  const [saving,    setSaving]    = useState(false);
  const [adv,       setAdv]       = useState(r.advice||r.treatment_plan||"");
  const [treat,     setTreat]     = useState(r.treatment_done_today||"");
  const [fupManual, setFupManual] = useState(r.follow_up_date||"");

  useEffect(()=>{
    setAdv(r.advice||r.treatment_plan||"");
    setTreat(r.treatment_done_today||"");
    setFupManual(r.follow_up_date||"");
  },[r.id, r.advice, r.treatment_done_today, r.follow_up_date]);

  const handleSave = async () => {
    setSaving(true);
    await onSave(r.id, {
      advice: adv,
      treatment_plan: adv,
      treatment_done_today: treat,
      follow_up_date: fupManual,
    });
    setSaving(false);
    setEditing(false);
  };

  if (editing) {
    return (
      <tr style={{background:"#fffbeb",outline:"2px solid #fcd34d",outlineOffset:-1}}>
        <td style={{fontFamily:"'DM Mono',monospace",fontSize:11.5,color:"#64748b",whiteSpace:"nowrap",verticalAlign:"top",paddingTop:10}}>
          {fmtDate(r.created_at||r.updated_at||todayStr())}
          <div style={{fontSize:9,color:"#a3a3a3",marginTop:2}}>today</div>
        </td>
        <td style={{verticalAlign:"top"}}>
          <DiagnosisReadOnly text={r.diagnosis}/>
          <div style={{marginTop:5,display:"inline-flex",alignItems:"center",gap:4,
            background:"#f8fafc",border:"1px solid #e2e8f0",borderRadius:5,padding:"2px 7px",
            fontSize:10,color:"#94a3b8"}}>🔒 read-only</div>
        </td>
        <td style={{verticalAlign:"top"}}>
          <textarea style={S.histEdit} value={adv} onChange={e=>setAdv(e.target.value)}/>
        </td>
        <td style={{verticalAlign:"top"}}>
          <textarea style={S.histEdit} value={treat} onChange={e=>setTreat(e.target.value)}/>
        </td>
        <td style={{verticalAlign:"top"}}>
          <div style={{position:"relative",display:"inline-flex",alignItems:"center",gap:4,
            background:"#f1f5f9",border:"1.5px solid #e2e8f0",borderRadius:6,padding:"5px 9px",
            fontSize:11.5,color:"#475569",cursor:"pointer",minWidth:100}}>
            🗓 {fupManual?fmtDate(fupManual):"Pick date"}
            <input type="date" value={fupManual} onChange={e=>setFupManual(e.target.value)}
              style={{position:"absolute",opacity:0,inset:0,cursor:"pointer",fontSize:0,width:"100%",height:"100%"}}/>
          </div>
        </td>
        <td style={{verticalAlign:"top"}}>
          <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
            <button className="tbl-btn edit" onClick={handleSave} disabled={saving}>
              {saving?"⏳":"💾"}
            </button>
            <button className="tbl-btn del" onClick={()=>setEditing(false)}>✕</button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td style={{fontFamily:"'DM Mono',monospace",fontSize:11.5,color:"#64748b",whiteSpace:"nowrap",verticalAlign:"top"}}>
        {fmtDate(r.created_at||r.updated_at||todayStr())}
        <div style={{fontSize:9,color:"#22c55e",marginTop:2,fontWeight:600}}>today</div>
      </td>
      <td style={{verticalAlign:"top"}}><DiagnosisReadOnly text={r.diagnosis}/></td>
      <td style={{fontSize:12.5,color:"#1e293b",lineHeight:1.6,verticalAlign:"top"}}>{r.advice||r.treatment_plan||"—"}</td>
      <td style={{fontSize:12.5,color:"#1e293b",lineHeight:1.6,verticalAlign:"top"}}>{r.treatment_done_today||"—"}</td>
      <td style={{fontFamily:"'DM Mono',monospace",fontSize:12,verticalAlign:"top"}}>
        {r.follow_up_date ? (
          <div>
            <div>{fmtDate(r.follow_up_date)}</div>
            {r.follow_up_time && <div style={{fontSize:10.5,color:"#64748b",marginTop:2}}>🕐 {r.follow_up_time}</div>}
          </div>
        ) : "—"}
      </td>
      <td style={{verticalAlign:"top"}}>
        <button className="tbl-btn edit" title="Edit" onClick={()=>setEditing(true)}>✏️</button>
        <button className="tbl-btn del"  title="Delete" onClick={()=>onDelete(r.id)}>🗑️</button>
      </td>
    </tr>
  );
}

// ── Separated Diagnosis Section with dental chart + other findings ──────────
function DiagnosisSection({ dentalEntries, findingEntries, onEditDental, onDeleteDental, onAddManual, onEditManual, onDeleteManual }) {
  const [addOpen, setAddOpen] = useState(false);
  const [addText, setAddText] = useState("");
  const [addDate, setAddDate] = useState(todayStr());
  const [chartOpen, setChartOpen] = useState(false);

  const handleAdd = () => {
    if (!addText.trim()) return;
    onAddManual({ id: Date.now(), note: addText.trim(), date: addDate, teeth: [], manual: true });
    setAddText(""); setAddDate(todayStr()); setAddOpen(false);
  };

  return (
    <div style={S.section}>
      <div style={S.sectionHeader}>
        <span style={S.sectionTitle}>📋 Diagnosis</span>
        <div style={{display:"flex",gap:6}}>
          <button style={S.addBtn} onClick={()=>setChartOpen(true)}>🦷 Chart</button>
          <button style={S.addBtn} onClick={()=>setAddOpen(o=>!o)}>+ Add</button>
        </div>
      </div>

      {/* Auto-fill notice */}
      <div style={S.autoNote}>✅ Auto-filled from Dental Chart &amp; Other Findings</div>

      {addOpen && (
        <div style={S.inputBox}>
          <textarea style={S.inputArea} placeholder="Enter diagnosis manually…" value={addText} onChange={e=>setAddText(e.target.value)} autoFocus/>
          <div style={S.dateRow}>
            <span style={S.dateLabel}>Date:</span>
            <span style={S.autoChip}>📅 {fmtDate(todayStr())} <span style={S.autoTag}>auto</span></span>
            <div style={S.manualChip}>
              🗓 {fmtDate(addDate)} <span style={S.autoTag}>manual</span>
              <input type="date" value={addDate} onChange={e=>setAddDate(e.target.value)} style={S.hiddenDate}/>
            </div>
          </div>
          <div style={{display:"flex",gap:8,justifyContent:"flex-end",marginTop:8}}>
            <button style={S.cancelBtnSt} onClick={()=>setAddOpen(false)}>Cancel</button>
            <button style={S.okBtnSt} onClick={handleAdd} disabled={!addText.trim()}>OK</button>
          </div>
        </div>
      )}

      {chartOpen && (
        <DentalChartModal onClose={()=>setChartOpen(false)}
          onConfirm={data=>{
            onAddManual({id:Date.now(),note:data.note,date:data.date,teeth:data.teeth,chartType:data.chartType});
            setChartOpen(false);
          }}/>
      )}

      {/* Dental Chart sub-section */}
      {dentalEntries.length > 0 && (
        <div style={{marginBottom:10}}>
          <div style={{
            fontSize:10.5, fontWeight:700, color:"#1d4ed8",
            textTransform:"uppercase", letterSpacing:"0.06em",
            background:"#eff6ff", border:"1px solid #bfdbfe",
            borderRadius:"6px 6px 0 0", padding:"5px 10px",
            display:"flex", alignItems:"center", gap:6,
          }}>
            🦷 Dental Chart Conditions
          </div>
          <div style={{border:"1px solid #bfdbfe",borderTop:"none",borderRadius:"0 0 6px 6px",overflow:"hidden"}}>
            {dentalEntries.map(e => (
              <EntryItem key={e.id} entry={e} onEdit={onEditDental} onDelete={onDeleteDental}/>
            ))}
          </div>
        </div>
      )}

      {/* Other Findings sub-section */}
      {findingEntries.length > 0 && (
        <div style={{marginBottom:10}}>
          <div style={{
            fontSize:10.5, fontWeight:700, color:"#0369a1",
            textTransform:"uppercase", letterSpacing:"0.06em",
            background:"#e0f2fe", border:"1px solid #7dd3fc",
            borderRadius:"6px 6px 0 0", padding:"5px 10px",
            display:"flex", alignItems:"center", gap:6,
          }}>
            🔍 Other Findings
          </div>
          <div style={{border:"1px solid #7dd3fc",borderTop:"none",borderRadius:"0 0 6px 6px",overflow:"hidden"}}>
            {findingEntries.map(e => (
              <EntryItem key={e.id} entry={e} onEdit={onEditManual} onDelete={onDeleteManual}/>
            ))}
          </div>
        </div>
      )}

      {dentalEntries.length === 0 && findingEntries.length === 0 && (
        <div style={S.emptyMsg}>Will auto-populate once conditions or findings are recorded</div>
      )}
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Consultation({
  visitId,
  disabled       = false,
  otherFindings  = [],
  dentalChartLog = [],
  patient        = null,
}) {
  const [records,        setRecords]        = useState([]);
  // Separated diagnosis
  const [dentalDiag,     setDentalDiag]     = useState([]);   // auto from dental chart
  const [findingsDiag,   setFindingsDiag]   = useState([]);   // auto from other findings + manual
  const [advice,         setAdvice]         = useState([]);
  const [treatDone,      setTreatDone]      = useState([]);
  const [followUps,      setFollowUps]      = useState([]);
  const [followDate,     setFollowDate]     = useState("");
  const [followTime,     setFollowTime]     = useState("09:00");
  const [showFollowAdd,  setShowFollowAdd]  = useState(false);
  const [showPast,       setShowPast]       = useState(false);
  const [patientInfo,    setPatientInfo]    = useState(patient);

  // Fetch patient info
  useEffect(() => {
    if (patientInfo || !visitId) return;
    api.get(`/visits/${visitId}`)
      .then(res => {
        const v = res.data || {};
        setPatientInfo({
          name:        v.patient?.name        || v.patient_name   || v.name   || "",
          mobile:      v.patient?.mobile      || v.patient_mobile || v.mobile || "",
          case_number: v.patient?.case_number || v.case_number    || "",
        });
      })
      .catch(() => setPatientInfo({ name:"", mobile:"", case_number:"" }));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visitId]);

  const chartLogKey  = JSON.stringify(dentalChartLog);
  const findingsKey  = JSON.stringify(otherFindings);

  // Auto-fill dental chart diagnosis
  useEffect(() => {
    const today = todayStr();
    const condGroups = {};
    dentalChartLog.forEach(row => {
      const rowDate = row.created_at ? row.created_at.split("T")[0] : today;
      if (rowDate !== today) return;
      const condLabel = row.condition==="Other"&&row.other_text ? row.other_text : row.condition;
      if (!condGroups[condLabel]) condGroups[condLabel] = { teeth: [], notes: [] };
      condGroups[condLabel].teeth.push(row.tooth_number);
      if (row.notes) condGroups[condLabel].notes.push(row.notes);
    });

    const auto = [];
    Object.entries(condGroups).forEach(([condLabel, { teeth, notes }]) => {
      const sortedTeeth = [...teeth].sort((a,b)=>a-b);
      const noteStr = notes.length > 0 ? ` — ${notes.join("; ")}` : "";
      auto.push({
        id:   `auto-chart-${condLabel.replace(/\s+/g,"-")}`,
        auto: true,
        date: today,
        teeth: sortedTeeth,
        note: `${condLabel}${noteStr}`,
      });
    });

    setDentalDiag(auto);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartLogKey]);

  // Auto-fill other findings diagnosis (keep manual entries)
  useEffect(() => {
    const today = todayStr();
    const auto = [];
    otherFindings.forEach(f => {
      const fDate = f.value ? f.value.split("T")[0] : today;
      if (fDate !== today) return;
      auto.push({
        id:    `auto-finding-${f.id}`,
        auto:  true,
        date:  today,
        teeth: [],
        note:  f.finding_type,
      });
    });

    setFindingsDiag(prev => [...auto, ...prev.filter(e => !e.auto)]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [findingsKey]);

  // Load history
  useEffect(() => {
    if (!visitId) return;
    Promise.all([
      api.get(`/visits/${visitId}/consultations`).catch(()=>({data:[]})),
      api.get(`/appointments`).catch(()=>({data:[]})),
    ]).then(([cRes, aRes]) => {
      const rows  = cRes.data || [];
      const appts = aRes.data || [];
      const enriched = rows.map(r => {
        if (r.follow_up_time || !r.follow_up_date) return r;
        const match = appts.find(a =>
          a.date === r.follow_up_date &&
          (String(a.visit_id) === String(visitId) ||
           a.case_number === (patientInfo?.case_number || "") ||
           a.name === (patientInfo?.name || ""))
        );
        return match?.time ? { ...r, follow_up_time: match.time } : r;
      });
      setRecords(enriched);
    }).catch(()=>{});
  }, [visitId]);

  const addEntry  = setter => entry => setter(prev=>[...prev,entry]);
  const editEntry = setter => (id,txt) => setter(prev=>prev.map(e=>e.id===id?{...e,note:txt}:e));
  const delEntry  = setter => id => setter(prev=>prev.filter(e=>e.id!==id));

  const resetForm = () => {
    setAdvice([]);
    setTreatDone([]);
    setFollowUps([]);
    setFollowDate("");
    setFollowTime("09:00");
    setShowFollowAdd(false);
    setFindingsDiag(prev => prev.filter(e=>e.auto));
  };

  // Combined diagnosis string for saving: dental chart + other findings
  const buildDiagnosisText = () => {
    const fmtEntry = e => {
      if (e.teeth && e.teeth.length > 0)
        return `${e.note} IRT ${e.teeth.sort((a,b)=>a-b).join(", ")}`;
      return e.note;
    };
    const dentalParts   = dentalDiag.map(fmtEntry);
    const findingsParts = findingsDiag.map(fmtEntry);
    const all = [...dentalParts, ...findingsParts].filter(Boolean);
    return all.join("; ");
  };

  const saveAll = async () => {
    try {
      const diagText = buildDiagnosisText();
      const fmtE = e => {
        if (e.teeth && e.teeth.length > 0)
          return `${e.note} IRT ${e.teeth.sort((a,b)=>a-b).join(", ")}`;
        return e.note;
      };
      const followUpDate = followUps.length>0 ? followUps[followUps.length-1].date : "";
      const payload = {
        diagnosis:            diagText,
        advice:               advice.map(fmtE).join("; "),
        treatment_plan:       advice.map(e=>e.note).join("; "),
        treatment_done_today: treatDone.map(fmtE).join("; "),
        follow_up_date:       followUpDate,
        follow_up_time:       followUps.length>0 ? (followUps[followUps.length-1].time || "") : "",
      };

      await api.post(`/visits/${visitId}/consultations`, payload);

      if (followUps.length > 0) {
        for (const f of followUps) {
          try {
            await api.post(`/appointments`, {
              source:      "consultation",
              name:        patientInfo?.name        || "Patient",
              mobile:      patientInfo?.mobile      || "",
              case_number: patientInfo?.case_number || "",
              date:        f.date,
              time:        f.time || "09:00",
              treatment:   "Follow-up",
              notes:       diagText ? `Follow-up for: ${diagText}` : "Follow-up appointment",
              status:      "pending",
            });
          } catch(apptErr) {
            console.warn("Could not create follow-up appointment:", f.date, apptErr);
          }
        }
      }

      const savedTime = followUps.length>0 ? (followUps[followUps.length-1].time || "") : "";
      const savedDate = followUps.length>0 ? followUps[followUps.length-1].date : "";
      const res = await api.get(`/visits/${visitId}/consultations`);
      const rows = res.data||[];
      if (rows.length > 0 && savedTime) {
        const last = rows[rows.length-1];
        if (!last.follow_up_time && last.follow_up_date === savedDate) {
          rows[rows.length-1] = { ...last, follow_up_time: savedTime };
        }
      }
      setRecords(rows);
      resetForm();
    } catch(err) { console.error("Save failed", err); }
  };

  const updateRecord = async (id, payload) => {
    try {
      await api.put(`/consultations/${id}`, payload);
      setRecords(prev => prev.map(r => r.id===id ? {...r,...payload} : r));
    } catch(err) {
      console.error("Update failed", err);
      api.get(`/visits/${visitId}/consultations`).then(res=>setRecords(res.data||[])).catch(()=>{});
      throw err;
    }
  };

  const deleteRecord = async (id) => {
    if (!window.confirm("Delete this consultation record?")) return;
    try {
      await api.delete(`/consultations/${id}`);
      setRecords(prev => prev.filter(r=>r.id!==id));
    } catch(err) { console.error("Delete failed", err); }
  };

  return (
    <>
      <style>{css}</style>
      <div className="cons-root">

        {/* Header */}
        <div className="cons-header">
          <div className="cons-header-icon">🩺</div>
          <div>
            <div className="cons-header-title">Consultation</div>
            <div className="cons-header-sub">Doctor's notes &amp; advice</div>
          </div>
        </div>

        <div className="cons-grid">

          {/* DIAGNOSIS — separated dental + findings */}
          <div className="cons-col">
            <DiagnosisSection
              dentalEntries={dentalDiag}
              findingEntries={findingsDiag}
              onEditDental={editEntry(setDentalDiag)}
              onDeleteDental={delEntry(setDentalDiag)}
              onAddManual={addEntry(setFindingsDiag)}
              onEditManual={editEntry(setFindingsDiag)}
              onDeleteManual={delEntry(setFindingsDiag)}
            />
          </div>

          {/* ADVICE & TREATMENT PLAN */}
          <div className="cons-col">
            <EntrySection
              title="💊 Advice & Treatment Plan"
              entries={advice}
              onAdd={addEntry(setAdvice)}
              onEdit={editEntry(setAdvice)}
              onDelete={delEntry(setAdvice)}
              showChart={true}
              placeholder="Enter advice or treatment plan…"
            />
          </div>

          {/* TREATMENT DONE TODAY */}
          <div className="cons-col">
            <EntrySection
              title="✅ Treatment Done Today"
              entries={treatDone}
              onAdd={addEntry(setTreatDone)}
              onEdit={editEntry(setTreatDone)}
              onDelete={delEntry(setTreatDone)}
              showChart={true}
              placeholder="Enter treatment done today…"
            />
          </div>
        </div>

        {/* NEXT FOLLOW-UP DATE */}
        <div className="cons-followup">
          <div className="cons-followup-header">
            <span className="cons-section-title">🗓 Next Follow-up Date</span>
            {!disabled&&<button className="add-btn" onClick={()=>setShowFollowAdd(o=>!o)}>+ Add</button>}
          </div>
          {showFollowAdd&&(
            <div className="followup-input" style={{alignItems:"flex-start",flexDirection:"column",gap:10}}>
              <div style={{fontSize:11.5,color:"#64748b",fontWeight:500}}>Choose a date:</div>
              <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
                <button
                  style={{
                    display:"flex",alignItems:"center",gap:6,
                    background: followDate===todayStr()?"#dcfce7":"#f1f5f9",
                    border: followDate===todayStr()?"1.5px solid #16a34a":"1.5px solid #e2e8f0",
                    borderRadius:8,padding:"7px 13px",fontSize:12.5,
                    color: followDate===todayStr()?"#15803d":"#475569",
                    fontFamily:"'DM Mono',monospace",cursor:"pointer",fontWeight:600,
                    transition:"all .14s"
                  }}
                  onClick={()=>setFollowDate(todayStr())}>
                  📅 {fmtDate(todayStr())}
                  <span style={{fontSize:10,background:"#d1fae5",color:"#059669",borderRadius:4,padding:"1px 5px",fontWeight:700}}>
                    today
                  </span>
                </button>
                <input
                  type="date"
                  value={followDate!==todayStr() ? followDate : ""}
                  min={todayStr()}
                  onChange={e=>setFollowDate(e.target.value)}
                  style={{
                    padding:"7px 13px",
                    border: followDate&&followDate!==todayStr()?"1.5px solid #3b82f6":"1.5px solid #e2e8f0",
                    borderRadius:8,fontSize:12.5,
                    fontFamily:"'DM Mono',monospace",cursor:"pointer",fontWeight:600,
                    background: followDate&&followDate!==todayStr()?"#eff6ff":"#f8fafc",
                    color: followDate&&followDate!==todayStr()?"#1d4ed8":"#64748b",
                    outline:"none",transition:"all .14s"
                  }}/>
              </div>
              {followDate&&(
                <div style={{display:"flex",flexDirection:"column",gap:8,width:"100%"}}>
                  <div style={{display:"flex",alignItems:"center",gap:8,padding:"7px 12px",
                    background:"#f0fdf4",border:"1px solid #bbf7d0",borderRadius:8}}>
                    <span style={{fontSize:12,color:"#15803d",fontWeight:600}}>
                      ✅ Follow-up: {fmtDate(followDate)}
                    </span>
                  </div>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <span style={{fontSize:11.5,color:"#64748b",fontWeight:500,whiteSpace:"nowrap"}}>🕐 Appointment time:</span>
                    <input
                      type="time"
                      value={followTime}
                      onChange={e=>setFollowTime(e.target.value)}
                      style={{padding:"6px 10px",border:"1.5px solid #e2e8f0",borderRadius:7,
                        fontFamily:"'DM Mono',monospace",fontSize:13,outline:"none",
                        background:"#f8fafc",color:"#1e293b",cursor:"pointer"}}/>
                  </div>
                </div>
              )}
              <div style={{display:"flex",gap:8}}>
                <button
                  className="ok-btn"
                  disabled={!followDate}
                  style={{opacity:followDate?1:0.45,cursor:followDate?"pointer":"not-allowed"}}
                  onClick={()=>{
                    if(!followDate) return;
                    setFollowUps(prev=>[...prev,{id:Date.now(),date:followDate,time:followTime}]);
                    setFollowDate("");
                    setFollowTime("09:00");
                    setShowFollowAdd(false);
                  }}>
                  ✔ Confirm Date
                </button>
                <button className="cancel-btn" onClick={()=>{setFollowDate("");setFollowTime("09:00");setShowFollowAdd(false);}}>
                  Cancel
                </button>
              </div>
            </div>
          )}
          <div className="followup-list">
            {followUps.map(f=>(
              <div key={f.id} className="followup-chip">
                📅 {fmtDate(f.date)}{f.time && <span style={{marginLeft:5,color:"#64748b",fontFamily:"'DM Mono',monospace",fontSize:11}}>🕐 {f.time}</span>}
                {!disabled&&(
                  <button className="chip-del"
                    onClick={()=>setFollowUps(prev=>prev.filter(x=>x.id!==f.id))}>✕</button>
                )}
              </div>
            ))}
            {followUps.length===0&&<span className="empty-msg">No follow-up date added yet</span>}
          </div>
        </div>

        {/* SAVE */}
        {!disabled&&(
          <div className="cons-save-row">
            <button className="save-all-btn" onClick={saveAll}>💾 Save Consultation</button>
          </div>
        )}

        {/* CONSULTATION HISTORY */}
        {records.length > 0 && (() => {
          const today = todayStr();
          const todayRecs = records.filter(r => {
            const d = (r.created_at||r.updated_at||"").split("T")[0];
            return d === today;
          });
          const pastRecs = records.filter(r => {
            const d = (r.created_at||r.updated_at||"").split("T")[0];
            return d !== today;
          });

          const tableHead = (
            <thead>
              <tr>
                <th style={{width:"10%",whiteSpace:"nowrap"}}>Date</th>
                <th style={{width:"22%"}}>
                  Diagnosis
                  <span style={{display:"inline-block",marginLeft:6,fontSize:9,color:"#94a3b8",
                    background:"#f1f5f9",border:"1px solid #e2e8f0",borderRadius:4,
                    padding:"1px 5px",verticalAlign:"middle",fontWeight:400}}>🔒 read-only</span>
                </th>
                <th style={{width:"22%"}}>Advice &amp; Treatment Plan</th>
                <th style={{width:"22%"}}>Treatment Done</th>
                <th style={{width:"13%"}}>Follow-up</th>
                <th style={{width:"11%"}}>Action</th>
              </tr>
            </thead>
          );

          return (
            <div className="cons-table-wrap">
              {todayRecs.length > 0 && (
                <>
                  <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                    <div className="cons-table-title" style={{marginBottom:0}}>Today's Consultations</div>
                    <span style={{fontSize:11,color:"#22c55e",background:"#f0fdf4",border:"1px solid #bbf7d0",
                      borderRadius:20,padding:"2px 9px",fontWeight:600}}>
                      {fmtDate(today)}
                    </span>
                  </div>
                  <table className="cons-table" style={{marginBottom:16}}>
                    {tableHead}
                    <tbody>
                      {todayRecs.map(r=>(
                        <HistoryRow key={r.id} r={r}
                          onSave={updateRecord}
                          onDelete={deleteRecord}/>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {pastRecs.length > 0 && (
                <div style={{marginTop:4}}>
                  <button onClick={()=>setShowPast(p=>!p)} style={{
                    display:"flex",alignItems:"center",gap:8,
                    padding:"8px 14px",borderRadius:9,
                    border:"1.5px solid #e2e8f0",background:"#f8fafc",
                    fontSize:12.5,fontWeight:600,color:"#475569",
                    cursor:"pointer",fontFamily:"'DM Sans',sans-serif",
                    transition:"all .15s",width:"100%",justifyContent:"space-between"}}>
                    <span>
                      🗂 Past Consultations
                      <span style={{marginLeft:8,fontSize:11,background:"#e2e8f0",
                        borderRadius:20,padding:"1px 8px",fontWeight:700,color:"#64748b"}}>
                        {pastRecs.length}
                      </span>
                    </span>
                    <span style={{fontSize:14,color:"#94a3b8",transition:"transform .2s",
                      transform:showPast?"rotate(180deg)":"rotate(0deg)"}}>▼</span>
                  </button>
                  {showPast && (
                    <div style={{marginTop:8,border:"1.5px solid #e2e8f0",borderRadius:10,overflow:"hidden"}}>
                      <div style={{padding:"7px 14px",background:"#f8fafc",borderBottom:"1px solid #e2e8f0",
                        fontSize:11,color:"#94a3b8",fontWeight:600,letterSpacing:".05em",textTransform:"uppercase"}}>
                        🔒 Past records are read-only
                      </div>
                      <table className="cons-table">
                        {tableHead}
                        <tbody>
                          {pastRecs.map(r=>(
                            <HistoryRowReadOnly key={r.id} r={r}/>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const S = {
  overlay:      {position:"fixed",inset:0,background:"rgba(15,23,42,0.55)",zIndex:1000,display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(4px)"},
  modal:        {background:"#fff",borderRadius:16,padding:24,width:"min(640px,95vw)",maxHeight:"90vh",overflowY:"auto",boxShadow:"0 20px 60px rgba(0,0,0,0.2)"},
  modalHeader:  {display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16},
  modalTitle:   {fontSize:15,fontWeight:600,color:"#1e293b",fontFamily:"'DM Sans',sans-serif"},
  closeBtn:     {border:"none",background:"#f1f5f9",borderRadius:8,width:30,height:30,cursor:"pointer",fontSize:13,color:"#64748b"},
  toggleRow:    {display:"flex",gap:8,marginBottom:14},
  toggleBtn:    {flex:1,padding:"7px 0",borderRadius:8,border:"1.5px solid #e2e8f0",background:"#f8fafc",fontSize:13,fontWeight:500,cursor:"pointer",color:"#64748b",fontFamily:"'DM Sans',sans-serif",transition:"all 0.15s"},
  toggleActive: {background:"#3b82f6",color:"#fff",borderColor:"#3b82f6"},
  chartWrap:    {background:"#f8fafc",borderRadius:12,padding:12,marginBottom:12,border:"1px solid #e2e8f0"},
  quadrantRow:  {display:"flex",alignItems:"center",justifyContent:"center"},
  quadrant:     {display:"flex",gap:3,padding:"6px 8px",flexWrap:"wrap",justifyContent:"center"},
  dividerV:     {width:2,background:"#cbd5e1",alignSelf:"stretch",margin:"0 2px"},
  dividerH:     {height:2,background:"#cbd5e1",margin:"3px 0"},
  tooth:        {width:32,height:32,borderRadius:7,border:"1.5px solid #e2e8f0",background:"#fff",fontSize:10,fontWeight:600,cursor:"pointer",color:"#475569",fontFamily:"'DM Mono',monospace",transition:"all 0.12s"},
  toothSel:     {background:"#3b82f6",color:"#fff",borderColor:"#2563eb",transform:"scale(1.1)"},
  selectedTeeth:{display:"flex",flexWrap:"wrap",gap:4,alignItems:"center",marginBottom:10,padding:"8px 10px",background:"#eff6ff",borderRadius:8,border:"1px solid #bfdbfe"},
  selectedLabel:{fontSize:11,color:"#3b82f6",fontWeight:700},
  toothTag:     {background:"#3b82f6",color:"#fff",borderRadius:5,padding:"2px 7px",fontSize:11,fontWeight:600,fontFamily:"'DM Mono',monospace"},
  toothTagSm:   {background:"#dbeafe",color:"#1d4ed8",borderRadius:4,padding:"1px 5px",fontSize:10,fontWeight:600,fontFamily:"'DM Mono',monospace"},
  modalTextarea:{width:"100%",minHeight:68,padding:"10px 12px",border:"1.5px solid #e2e8f0",borderRadius:10,fontFamily:"'DM Sans',sans-serif",fontSize:13,resize:"vertical",outline:"none",marginBottom:12,boxSizing:"border-box"},
  modalDateRow: {display:"flex",alignItems:"center",gap:8,marginBottom:14,flexWrap:"wrap"},
  dateLabel:    {fontSize:12,color:"#64748b",fontWeight:500},
  autoChip:     {display:"flex",alignItems:"center",gap:4,background:"#f1f5f9",border:"1.5px solid #e2e8f0",borderRadius:7,padding:"5px 10px",fontSize:12,color:"#475569",fontFamily:"'DM Mono',monospace"},
  autoTag:      {fontSize:10,color:"#94a3b8"},
  manualChip:   {display:"flex",alignItems:"center",gap:4,background:"#f1f5f9",border:"1.5px solid #e2e8f0",borderRadius:7,padding:"5px 10px",fontSize:12,color:"#475569",fontFamily:"'DM Mono',monospace",cursor:"pointer",position:"relative"},
  hiddenDate:   {position:"absolute",opacity:0,width:"100%",height:"100%",top:0,left:0,cursor:"pointer",fontSize:0},
  modalActions: {display:"flex",gap:8,justifyContent:"flex-end"},
  okBtnSt:      {padding:"8px 20px",background:"#3b82f6",color:"#fff",border:"none",borderRadius:8,fontSize:13,fontWeight:500,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"},
  cancelBtnSt:  {padding:"8px 16px",background:"#f1f5f9",color:"#64748b",border:"none",borderRadius:8,fontSize:13,fontWeight:500,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"},
  section:      {marginBottom:0},
  sectionHeader:{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8},
  sectionTitle: {fontSize:13,fontWeight:600,color:"#1e293b"},
  addBtn:       {padding:"5px 11px",background:"#eff6ff",color:"#3b82f6",border:"1.5px solid #bfdbfe",borderRadius:7,fontSize:12,fontWeight:500,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"},
  inputBox:     {background:"#f8fafc",border:"1.5px solid #e2e8f0",borderRadius:10,padding:12,marginBottom:10},
  inputArea:    {width:"100%",minHeight:68,padding:"9px 11px",border:"1.5px solid #e2e8f0",borderRadius:8,fontFamily:"'DM Sans',sans-serif",fontSize:13,resize:"vertical",outline:"none",boxSizing:"border-box",marginBottom:8,background:"#fff"},
  dateRow:      {display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"},
  entryList:    {display:"flex",flexDirection:"column",gap:8,marginTop:6},
  entryItem:    {background:"#fff",border:"1.5px solid #e9eef4",borderRadius:10,padding:"10px 12px",position:"relative",animation:"fadeIn 0.2s ease"},
  entryAuto:    {background:"#f0fdf4",border:"1.5px solid #bbf7d0"},
  entryMeta:    {display:"flex",alignItems:"center",gap:6,marginBottom:4,flexWrap:"wrap"},
  entryDate:    {fontSize:11,color:"#94a3b8",fontFamily:"'DM Mono',monospace"},
  entryIRT:     {display:"inline-flex",alignItems:"center",gap:4,background:"#eff6ff",border:"1px solid #bfdbfe",borderRadius:6,padding:"1px 8px",flexShrink:0},
  irtLabel:     {fontSize:10,fontWeight:700,color:"#7c3aed",marginRight:2},
  autoBadge:    {fontSize:10,background:"#dcfce7",color:"#16a34a",borderRadius:5,padding:"1px 7px",fontWeight:600},
  entryText:    {fontSize:13,color:"#1e293b",lineHeight:1.5,paddingRight:58},
  entryBtns:    {position:"absolute",top:8,right:8,display:"flex",gap:4},
  iconBtn:      {width:26,height:26,border:"1.5px solid #e2e8f0",borderRadius:6,background:"#fff",display:"flex",alignItems:"center",justifyContent:"center",cursor:"pointer",fontSize:12},
  editArea:     {width:"100%",minHeight:55,padding:"7px 9px",border:"1.5px solid #3b82f6",borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontSize:13,resize:"vertical",outline:"none",boxSizing:"border-box",boxShadow:"0 0 0 3px rgba(59,130,246,0.1)"},
  histEdit:     {width:"100%",minHeight:52,padding:"6px 8px",border:"1.5px solid #3b82f6",borderRadius:7,fontFamily:"'DM Sans',sans-serif",fontSize:12,resize:"vertical",outline:"none",boxSizing:"border-box",background:"#fffbeb"},
  saveSm:       {padding:"4px 12px",background:"#3b82f6",color:"#fff",border:"none",borderRadius:6,fontSize:12,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"},
  cancelSm:     {padding:"4px 12px",background:"#f1f5f9",color:"#64748b",border:"none",borderRadius:6,fontSize:12,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"},
  emptyMsg:     {fontSize:12,color:"#cbd5e1",fontStyle:"italic",padding:"6px 0"},
  autoNote:     {fontSize:11,color:"#16a34a",background:"#f0fdf4",border:"1px solid #bbf7d0",borderRadius:7,padding:"5px 10px",marginBottom:10},
};

const css = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
@keyframes fadeIn { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }

.cons-root { font-family:'DM Sans',sans-serif; background:#f8fafc; border-radius:16px; padding:24px; border:1px solid #e2e8f0; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.cons-header { display:flex; align-items:center; gap:12px; margin-bottom:22px; padding-bottom:16px; border-bottom:1px solid #e9eef4; }
.cons-header-icon { width:38px; height:38px; background:linear-gradient(135deg,#dbeafe,#bfdbfe); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; }
.cons-header-title { font-size:15px; font-weight:600; color:#1e293b; }
.cons-header-sub   { font-size:12px; color:#94a3b8; }
.cons-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-bottom:16px; }
@media(max-width:800px){ .cons-grid{ grid-template-columns:1fr; } }
.cons-col { background:#fff; border:1.5px solid #e9eef4; border-radius:12px; padding:14px; }
.cons-followup { background:#fff; border:1.5px solid #e9eef4; border-radius:12px; padding:14px; margin-bottom:16px; }
.cons-followup-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.cons-section-title { font-size:13px; font-weight:600; color:#1e293b; }
.followup-input { display:flex; gap:8px; align-items:center; margin-bottom:10px; flex-wrap:wrap; }
.followup-date-input { padding:7px 10px; border:1.5px solid #e2e8f0; border-radius:8px; font-size:13px; font-family:'DM Sans',sans-serif; outline:none; }
.followup-date-input:focus { border-color:#3b82f6; }
.ok-btn { padding:7px 16px; background:#3b82f6; color:#fff; border:none; border-radius:7px; font-size:12px; font-weight:500; cursor:pointer; font-family:'DM Sans',sans-serif; }
.ok-btn:disabled { background:#93c5fd; cursor:not-allowed; }
.cancel-btn { padding:7px 14px; background:#f1f5f9; color:#64748b; border:none; border-radius:7px; font-size:12px; cursor:pointer; font-family:'DM Sans',sans-serif; }
.add-btn { padding:5px 12px; background:#eff6ff; color:#3b82f6; border:1.5px solid #bfdbfe; border-radius:7px; font-size:12px; font-weight:500; cursor:pointer; font-family:'DM Sans',sans-serif; }
.followup-list { display:flex; flex-wrap:wrap; gap:8px; }
.followup-chip { display:flex; align-items:center; gap:6px; background:#eff6ff; border:1.5px solid #bfdbfe; border-radius:8px; padding:5px 10px; font-size:12px; color:#1d4ed8; font-family:'DM Mono',monospace; animation:fadeIn 0.2s ease; }
.chip-del { border:none; background:none; color:#93c5fd; cursor:pointer; font-size:11px; padding:0; }
.chip-del:hover { color:#ef4444; }
.empty-msg { font-size:12px; color:#cbd5e1; font-style:italic; }
.cons-save-row { display:flex; justify-content:flex-end; margin-bottom:18px; }
.save-all-btn { padding:10px 26px; background:#3b82f6; color:#fff; border:none; border-radius:9px; font-size:14px; font-weight:500; cursor:pointer; font-family:'DM Sans',sans-serif; box-shadow:0 2px 8px rgba(59,130,246,0.25); transition:background 0.15s; }
.save-all-btn:hover { background:#2563eb; }
.cons-table-wrap { margin-top:4px; }
.cons-table-title { font-size:11.5px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; }
.cons-table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; border-radius:10px; overflow:hidden; border:1px solid #e9eef4; }
.cons-table th { background:#f8fafc; padding:10px 12px; text-align:left; font-size:12px; color:#64748b; border-bottom:1px solid #e9eef4; }
.cons-table td { padding:10px 12px; border-bottom:1px solid #f1f5f9; color:#1e293b; vertical-align:top; }
.cons-table tr:last-child td { border-bottom:none; }
.tbl-btn { border:1.5px solid #e2e8f0; background:#fff; border-radius:6px; padding:3px 8px; cursor:pointer; font-size:12px; margin-right:4px; transition:all 0.15s; }
.tbl-btn.edit:hover { border-color:#3b82f6; background:#eff6ff; }
.tbl-btn.del:hover  { border-color:#ef4444; background:#fef2f2; }
`;