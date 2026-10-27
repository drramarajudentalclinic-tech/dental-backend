import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { portal, getSession, setSession } from "../api";
import { Bar, Footer } from "../components/Chrome";

const IMAGE_NAMES = { IOPA: "IOPA X-ray", OPG: "OPG (full-mouth X-ray)", INTRAORAL: "Mouth photo", EXTRAORAL: "Face photo",
  CEPH: "Ceph X-ray", BITEWING: "Bitewing X-ray", RVG: "X-ray", CBCT: "CBCT picture", IMPLANT: "Implant details" };
const imgName = (t) => IMAGE_NAMES[String(t || "").toUpperCase()] || String(t || "Picture");
const money = (n) => `₹${Number(n || 0).toLocaleString("en-IN")}`;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const New = ({ on }) => (on ? <span className="new">New</span> : null);

/* Picture fetched with the login token, shown from memory (no token in any URL). */
function useBlobUrl(load, deps) {
  const [url, setUrl] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true, made = null;
    load().then((b) => { if (!alive) return; made = URL.createObjectURL(b); setUrl(made); }).catch(() => alive && setFailed(true));
    return () => { alive = false; if (made) URL.revokeObjectURL(made); };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  return [url, failed];
}

function Thumb({ im, onOpen }) {
  const [url, failed] = useBlobUrl(() => portal.imageBlob(im.id), [im.id]);
  return (
    <button type="button" className="thumb" onClick={() => onOpen({ kind: "image", item: im })} aria-label={`Open ${imgName(im.type)}`}>
      {url ? <img src={url} alt="" /> : <span className="ph">{failed ? "Could not load" : "Loading…"}</span>}
      <span className="cap"><b>{imgName(im.type)}</b><New on={im.new} />{(im.date || im.description) && <span className="muted" style={{ display: "block", fontSize: 13 }}>{[im.date, im.description].filter(Boolean).join(", ")}</span>}</span>
    </button>
  );
}

function Viewer({ open, onClose }) {
  const { kind, item } = open;
  const [url, failed] = useBlobUrl(() => (kind === "image" ? portal.imageBlob(item.id) : portal.cbctPreview(item.id)), [kind, item.id]);
  const [zipMsg, setZipMsg] = useState("");
  useEffect(() => {
    const k = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", k);
    const prev = document.body.style.overflow; document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", k); document.body.style.overflow = prev; };
  }, [onClose]);
  const title = kind === "image" ? imgName(item.type) : "CBCT 3-D scan — preview";
  const fileName = kind === "image" ? `${imgName(item.type).replace(/\W+/g, "-")}-${item.date || item.id}.${(item.mime_type || "").includes("png") ? "png" : "jpg"}` : `CBCT-preview-${item.id}.png`;
  const zip = async () => {
    setZipMsg("Preparing the download…");
    try {
      const r = await portal.cbctZip(item.id);
      if (r.url) { window.location.href = r.url; setZipMsg(""); }
      else setZipMsg("The full scan file is not available online. Ask at the clinic for a copy on a pen drive or CD.");
    } catch (e) { setZipMsg(e.message); }
  };
  return (
    <div className="viewer" role="dialog" aria-modal="true" aria-label={title}>
      <div className="viewer-bar">
        <div><b>{title}</b>{item.date && <span style={{ opacity: .75 }}> — {item.date}</span>}</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {url && <a className="btn small" href={url} download={fileName}>Download</a>}
          {kind === "cbct" && <button type="button" className="btn small" onClick={zip}>Download full scan (DICOM)</button>}
          <button type="button" className="btn small" onClick={onClose} autoFocus>Close</button>
        </div>
      </div>
      {zipMsg && <div style={{ color: "#fff", padding: "0 16px 10px" }} role="status">{zipMsg}</div>}
      <div className="viewer-img">
        {url ? <img src={url} alt={title} /> : <span style={{ color: "#cfe3df" }}>{failed ? "This file could not be opened. Please try again later." : "Loading…"}</span>}
      </div>
    </div>
  );
}

function printPrescription(rx, patient, clinic) {
  const w = window.open("", "_blank");
  if (!w) return;
  const meds = rx.medicines.map((m, i) => `<tr><td>${i + 1}</td><td><b>${esc(m.name)}</b>${m.dose ? ` ${esc(m.dose)}` : ""}${m.notes ? `<br><small>${esc(m.notes)}</small>` : ""}</td><td>${esc(m.when)}</td><td>${esc(m.food)}</td><td>${esc(m.days)}</td></tr>`).join("");
  const inv = rx.investigations.length ? `<p><b>Investigations:</b> ${rx.investigations.map((i) => esc(i.name + (i.note ? ` (${i.note})` : ""))).join(", ")}</p>` : "";
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Prescription ${esc(rx.date)}</title>
  <style>body{font:15px/1.5 "Segoe UI",system-ui,sans-serif;color:#1d2b2d;margin:32px;max-width:760px}h1{font-size:20px;margin:0}table{width:100%;border-collapse:collapse;margin:14px 0}
  th,td{text-align:left;border-bottom:1px solid #ccd;padding:6px 6px 6px 0;vertical-align:top}th{font-size:13px;color:#555}.top{border-bottom:2px solid #0f3d3e;padding-bottom:10px;margin-bottom:12px}
  .note{font-size:12px;color:#666;margin-top:28px}</style></head><body>
  <div class="top"><h1>${esc(clinic)}</h1><div>${esc(rx.doctor)}</div></div>
  <p><b>${esc(patient.name)}</b> — Case no. ${esc(patient.case_number)}${patient.age ? `, ${esc(patient.age)} yrs` : ""}${patient.gender ? `, ${esc(patient.gender)}` : ""}<br>Date: ${esc(rx.date)}</p>
  ${rx.diagnosis ? `<p><b>Diagnosis:</b> ${esc(rx.diagnosis)}</p>` : ""}
  <table><thead><tr><th>#</th><th>Medicine</th><th>How often</th><th>When</th><th>Days</th></tr></thead><tbody>${meds}</tbody></table>
  ${inv}${rx.advice ? `<p><b>Advice:</b> ${esc(rx.advice)}</p>` : ""}${rx.follow_up ? `<p><b>Next visit:</b> ${esc(rx.follow_up)}</p>` : ""}
  <p class="note">Copy from the patient portal. Take medicines only as advised by your doctor.</p>
  <script>window.onload=function(){window.print()}</script></body></html>`);
  w.document.close();
}

function Prescription({ rx, patient, clinic }) {
  return (
    <div className="rx">
      <div className="rx-top">
        <h3>Prescription<New on={rx.new} /></h3>
        <button type="button" className="btn ghost small no-print" onClick={() => printPrescription(rx, patient, clinic)}>Print or save as PDF</button>
      </div>
      <p className="muted" style={{ fontSize: 15, marginBottom: 8 }}>{[rx.date, rx.doctor].filter(Boolean).join(", ")}</p>
      {rx.diagnosis && <p style={{ marginBottom: 8 }}><b>Diagnosis:</b> {rx.diagnosis}</p>}
      {rx.medicines.length > 0 ? (
        <table className="med">
          <thead><tr><th>Medicine</th><th>How often</th><th>When</th><th>Days</th></tr></thead>
          <tbody>{rx.medicines.map((m, i) => (
            <tr key={i}><td>{m.name}{m.dose ? ` ${m.dose}` : ""}{m.notes && <div className="muted" style={{ fontSize: 14, fontWeight: 400 }}>{m.notes}</div>}</td>
              <td>{m.when}</td><td>{m.food}</td><td>{m.days ? `${m.days}${/^\d+$/.test(m.days) ? " days" : ""}` : ""}</td></tr>
          ))}</tbody>
        </table>
      ) : <p className="muted">No medicines.</p>}
      {rx.investigations.length > 0 && <p style={{ marginTop: 10 }}><b>Tests advised:</b> {rx.investigations.map((i) => i.name + (i.note ? ` (${i.note})` : "")).join(", ")}</p>}
      {rx.advice && <p style={{ marginTop: 6 }}><b>Advice:</b> {rx.advice}</p>}
      {rx.follow_up && <p style={{ marginTop: 6 }}><b>Next visit:</b> {rx.follow_up}</p>}
    </div>
  );
}

function Summary({ v }) {
  const s = v.summary;
  const rows = [["Your complaint", s.chief_complaint], ["Diagnosis", s.diagnosis], ["Treatment done", s.treatment_done],
    ["Treatment plan", s.treatment_plan], ["Advice", s.advice], ["Next visit", s.next_visit]].filter(([, x]) => x);
  return (
    <div className="sum">
      <h3 style={{ marginBottom: 8 }}>Visit summary<New on={v.summary_new} /></h3>
      {rows.length ? <dl>{rows.map(([k, x]) => <div key={k} style={{ display: "contents" }}><dt>{k}</dt><dd>{x}</dd></div>)}</dl>
        : <p className="muted">No notes for this visit.</p>}
    </div>
  );
}

function ScanRow({ cv, onOpen }) {
  return (
    <div className="file">
      <span><b>CBCT 3-D scan</b><New on={cv.new} /><span className="muted" style={{ display: "block", fontSize: 14 }}>{[cv.date, cv.slices ? `${cv.slices} slices` : ""].filter(Boolean).join(", ")}</span></span>
      <button type="button" className="btn ghost small" onClick={() => onOpen({ kind: "cbct", item: cv })}>View</button>
    </div>
  );
}

function ReceiptRow({ r }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const open = async () => {
    const w = window.open("", "_blank");   // opened now, so phones don't block it as a pop-up
    setBusy(true); setErr("");
    try {
      const b = await portal.receiptBlob(r.id);
      const url = URL.createObjectURL(b);
      if (w) w.location.href = url;
      else { const a = document.createElement("a"); a.href = url; a.download = `Receipt-${r.receipt_no}.pdf`; a.click(); }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) { if (w) w.close(); setErr(e.message); }
    finally { setBusy(false); }
  };
  return (
    <div className="file">
      <span><b>Receipt no. {r.receipt_no}</b><New on={r.new} />
        <span className="muted" style={{ display: "block", fontSize: 14 }}>{r.date}, {money(r.amount)}{r.treatments ? ` — ${r.treatments}` : ""}</span>
        {err && <span style={{ color: "#8f1f36", fontSize: 14 }} role="alert">{err}</span>}
      </span>
      <button type="button" className="btn ghost small" disabled={busy} onClick={open}>{busy ? "Opening…" : "Open PDF"}</button>
    </div>
  );
}

function Appointments({ a }) {
  const row = (x, i) => (
    <div className="file" key={i}>
      <span><b>{x.date}{x.time ? `, ${x.time}` : ""}</b><span className="muted" style={{ display: "block", fontSize: 14 }}>{[x.treatment, x.doctor].filter(Boolean).join(", ")}</span></span>
      <span className="muted" style={{ fontSize: 14 }}>{x.status}</span>
    </div>
  );
  return (
    <div style={{ display: "grid", gap: 26 }}>
      <div><h3 style={{ marginBottom: 10 }}>Upcoming</h3>{a.upcoming.length ? <div className="files">{a.upcoming.map(row)}</div> : <p className="muted">No upcoming appointment. Call the clinic to book one.</p>}</div>
      {a.past.length > 0 && <div><h3 style={{ marginBottom: 10 }}>Past</h3><div className="files">{a.past.map(row)}</div></div>}
    </div>
  );
}

export default function PortalRecord() {
  const { pid } = useParams();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState("visits");
  const [view, setView] = useState(null);
  const session = getSession();
  const firstLoad = useRef(true);

  const load = useCallback(async () => {
    try { setD(await portal.record(pid)); setErr(""); }
    catch (e) { if (e.status === 401) nav("/portal", { replace: true }); else setErr(e.message); }
  }, [pid, nav]);
  useEffect(() => {
    if (!getSession()) { nav("/portal", { replace: true }); return; }
    load();
  }, [load, nav]);
  useEffect(() => {
    const out = () => nav("/portal", { replace: true });
    window.addEventListener("portal-logout", out);
    return () => window.removeEventListener("portal-logout", out);
  }, [nav]);
  useEffect(() => { if (d) { document.title = `${d.patient.name} — patient portal`; firstLoad.current = false; } }, [d]);

  const all = useMemo(() => {
    if (!d) return null;
    const rx = [], imgs = [], scans = [];
    d.visits.forEach((v) => { v.prescriptions.forEach((x) => rx.push(x)); v.images.forEach((x) => imgs.push({ ...x, visit: v.date })); v.cbct.forEach((x) => scans.push(x)); });
    return { rx, imgs, scans };
  }, [d]);

  const logout = () => { setSession(null); nav("/portal", { replace: true }); };
  const many = (session?.profiles || []).length > 1;

  const tabs = d ? [
    ["visits", "Visits", d.visits.length],
    ["rx", "Prescriptions", all.rx.length],
    ["images", "X-rays & scans", all.imgs.length + all.scans.length],
    ["receipts", "Receipts", d.receipts.length],
    ...(d.appointments ? [["appts", "Appointments", d.appointments.upcoming.length]] : []),
  ] : [];

  return (
    <div className="p-shell">
      <Bar right={
        <div style={{ display: "flex", gap: 8 }}>
          {many && <Link className="btn ghost small" to="/portal">Switch person</Link>}
          <button type="button" className="btn ghost small" onClick={logout}>Log out</button>
        </div>
      } />
      <main className="p-main">
        <div className="wrap">
          {err && <div className="msg err" role="alert">{err} <Link to="/portal">Back to login</Link></div>}
          {!d && !err && <p className="muted">Loading your record…</p>}
          {d && (
            <>
              <div className="rec-head">
                <div>
                  <h1>{d.patient.name}</h1>
                  <p className="muted">Case no. {d.patient.case_number}{d.patient.age ? `, ${d.patient.age} yrs` : ""}
                    {d.new_items > 0 && <span className="badge" style={{ marginLeft: 10 }}>{d.new_items} new from your doctor</span>}</p>
                </div>
              </div>
              <div className="tabs" role="tablist" aria-label="Record">
                {tabs.map(([k, label, n]) => (
                  <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>{label}<span className="n">{n}</span></button>
                ))}
              </div>

              {tab === "visits" && (d.visits.length === 0 ? (
                <p className="empty">Nothing has been shared yet. After your visit, the doctor can share your summary, prescription and X-rays here.</p>
              ) : d.visits.map((v) => (
                <article className="visit-block" key={v.visit_id}>
                  <div className="visit-date">{v.date}</div>
                  <div className="visit-body">
                    {v.message && <div className="note-from"><b>From your doctor:</b> {v.message}</div>}
                    {v.summary && <Summary v={v} />}
                    {v.prescriptions.map((rx) => <Prescription key={rx.id} rx={rx} patient={d.patient} clinic={d.clinic} />)}
                    {v.images.length > 0 && <div className="thumbs">{v.images.map((im) => <Thumb key={im.id} im={im} onOpen={setView} />)}</div>}
                    {v.cbct.length > 0 && <div className="files">{v.cbct.map((cv) => <ScanRow key={cv.id} cv={cv} onOpen={setView} />)}</div>}
                  </div>
                </article>
              )))}

              {tab === "rx" && (all.rx.length ? <div style={{ display: "grid", gap: 14 }}>{all.rx.map((rx) => <Prescription key={rx.id} rx={rx} patient={d.patient} clinic={d.clinic} />)}</div>
                : <p className="empty">No prescriptions shared yet.</p>)}

              {tab === "images" && (all.imgs.length + all.scans.length ? (
                <div style={{ display: "grid", gap: 18 }}>
                  {all.imgs.length > 0 && <div className="thumbs">{all.imgs.map((im) => <Thumb key={im.id} im={im} onOpen={setView} />)}</div>}
                  {all.scans.length > 0 && <div className="files">{all.scans.map((cv) => <ScanRow key={cv.id} cv={cv} onOpen={setView} />)}</div>}
                </div>
              ) : <p className="empty">No X-rays or scans shared yet.</p>)}

              {tab === "receipts" && (d.receipts.length ? <div className="files">{d.receipts.map((r) => <ReceiptRow key={r.id} r={r} />)}</div>
                : <p className="empty">No receipts shared yet.</p>)}

              {tab === "appts" && d.appointments && <Appointments a={d.appointments} />}
            </>
          )}
        </div>
      </main>
      <Footer />
      {view && <Viewer open={view} onClose={() => setView(null)} />}
    </div>
  );
}