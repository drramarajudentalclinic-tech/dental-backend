import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { portal, getSession, setSession } from "../api";
import { Bar, Footer, Logo } from "../components/Chrome";
import { clinic as CLINIC, doctors } from "../content";

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

function Prescription({ rx, patient, clinic, compact = false }) {
  return (
    <div className={"rx" + (compact ? " rx-compact" : "")}>
      <div className="rx-top">
        <div className="rx-title"><span className="rx-sym" aria-hidden="true">℞</span>
          <div><h3>Prescription<New on={rx.new} /></h3><p className="muted">{[rx.date, rx.doctor].filter(Boolean).join(" · ")}</p></div></div>
        <button type="button" className="btn ghost small no-print" onClick={() => printPrescription(rx, patient, clinic)}>Print or save as PDF</button>
      </div>
      {rx.diagnosis && !compact && <p className="rx-line"><b>Diagnosis</b> {rx.diagnosis}</p>}
      {rx.medicines.length > 0 ? (
        <table className="med">
          <thead><tr><th>#</th><th>Medicine</th><th>How often</th><th>When</th><th>Days</th></tr></thead>
          <tbody>{rx.medicines.map((m, i) => (
            <tr key={i}><td className="med-n">{i + 1}</td><td><b>{m.name}</b>{m.dose ? ` ${m.dose}` : ""}{m.notes && <div className="muted" style={{ fontSize: 14, fontWeight: 400 }}>{m.notes}</div>}</td>
              <td data-l="How often">{m.when || "—"}</td><td data-l="When">{m.food || "—"}</td><td data-l="Days">{m.days ? `${m.days}${/^\d+$/.test(m.days) ? " days" : ""}` : "—"}</td></tr>
          ))}</tbody>
        </table>
      ) : <p className="muted">No medicines.</p>}
      {rx.investigations.length > 0 && <p className="rx-line"><b>Tests advised</b> {rx.investigations.map((i) => i.name + (i.note ? ` (${i.note})` : "")).join(", ")}</p>}
      {rx.advice && <p className="rx-line"><b>Advice</b> {rx.advice}</p>}
      {rx.follow_up && <p className="rx-line"><b>Next visit</b> {rx.follow_up}</p>}
    </div>
  );
}

/* Notes are often written as "item; item" — show them as a list so each item reads on its own line. */
function Multi({ text }) {
  const parts = String(text).split(/\s*;\s*/).filter(Boolean);
  return parts.length > 1 ? <ul className="cs-list">{parts.map((x, i) => <li key={i}>{x}</li>)}</ul> : <>{text}</>;
}

function Summary({ v }) {
  const s = v.summary;
  const rows = [["Chief complaint", s.chief_complaint], ["Diagnosis", s.diagnosis], ["Treatment done", s.treatment_done],
    ["Treatment plan", s.treatment_plan], ["Advice", s.advice], ["Next visit", s.next_visit]].filter(([, x]) => x);
  if (!rows.length) return <p className="muted">No notes for this visit.</p>;
  return (
    <table className="cs-table">
      <tbody>{rows.map(([k, x]) => <tr key={k}><th scope="row">{k}</th><td><Multi text={x} /></td></tr>)}</tbody>
    </table>
  );
}

/* Small section heading inside a visit */
const Sub = ({ children, extra }) => <div className="cs-sub"><h4>{children}</h4>{extra}</div>;

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
    <tr>
      <td data-l="Receipt no."><b>{r.receipt_no}</b><New on={r.new} /></td>
      <td data-l="Date">{r.date}</td>
      <td data-l="For">{r.treatments || "—"}{err && <div style={{ color: "#8f1f36", fontSize: 14 }} role="alert">{err}</div>}</td>
      <td data-l="Amount" className="num">{money(r.amount)}</td>
      <td className="no-print"><button type="button" className="btn ghost small" disabled={busy} onClick={open}>{busy ? "Opening…" : "Open PDF"}</button></td>
    </tr>
  );
}

function Receipts({ list }) {
  const total = list.reduce((t, r) => t + Number(r.amount || 0), 0);
  return (
    <table className="cs-grid">
      <thead><tr><th>Receipt no.</th><th>Date</th><th>For</th><th className="num">Amount</th><th className="no-print"></th></tr></thead>
      <tbody>{list.map((r) => <ReceiptRow key={r.id} r={r} />)}</tbody>
      <tfoot><tr><th colSpan={3}>Total paid</th><th className="num">{money(total)}</th><th className="no-print"></th></tr></tfoot>
    </table>
  );
}

function Appointments({ a }) {
  const table = (rows) => (
    <table className="cs-grid">
      <thead><tr><th>Date</th><th>Time</th><th>For</th><th>Doctor</th><th>Status</th></tr></thead>
      <tbody>{rows.map((x, i) => (
        <tr key={i}><td data-l="Date"><b>{x.date}</b></td><td data-l="Time">{x.time || "—"}</td><td data-l="For">{x.treatment || "—"}</td>
          <td data-l="Doctor">{x.doctor || "—"}</td><td data-l="Status"><span className={"st st-" + String(x.status || "").toLowerCase().replace(/\W+/g, "-")}>{x.status || "—"}</span></td></tr>
      ))}</tbody>
    </table>
  );
  return (
    <div className="cs-stack">
      <section className="cs-card"><Sub>Upcoming</Sub>{a.upcoming.length ? table(a.upcoming) : <p className="muted">No upcoming appointment. Call the clinic on {CLINIC.phone} to book one.</p>}</section>
      {a.past.length > 0 && <section className="cs-card"><Sub>Past</Sub>{table(a.past)}</section>}
    </div>
  );
}

const TAB_ICONS = {
  visits: <path d="M7 3h10v4H7zM5 5H4v16h16V5h-1M8 12h8M8 16h5" />,
  rx: <path d="M6 3h7a4 4 0 0 1 0 8H6zM6 11v10M11 11l8 10M19 13l-6 8" />,
  images: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="m21 17-5-5-9 8" /></>,
  receipts: <path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h3" />,
  appts: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></>,
};

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

  const doc = doctors[0] || {};
  const nextAppt = d?.appointments?.upcoming?.[0];
  const lastVisit = d?.visits?.[0]?.date;
  const printSheet = () => { setTab("visits"); setTimeout(() => window.print(), 150); };

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
              {/* ── case sheet header: clinic letterhead + patient details ── */}
              <section className="cs-head">
                <div className="cs-letter">
                  <Logo size={54} />
                  <div className="cs-clinic"><b>{d.clinic || CLINIC.name}</b>
                    <span>{[doc.name, doc.qualification, CLINIC.registration && `Reg. ${CLINIC.registration}`].filter(Boolean).join(" · ")}</span></div>
                  <span className="cs-tag">Patient case sheet</span>
                </div>
                <dl className="cs-pt">
                  <div className="cs-pt-name"><dt>Patient</dt><dd>{d.patient.name}</dd></div>
                  <div><dt>Case no.</dt><dd>{d.patient.case_number || "—"}</dd></div>
                  <div><dt>Age / Sex</dt><dd>{[d.patient.age ? `${d.patient.age} yrs` : "", d.patient.gender].filter(Boolean).join(" / ") || "—"}</dd></div>
                  <div><dt>Last visit</dt><dd>{lastVisit || "—"}</dd></div>
                  <div><dt>Next appointment</dt><dd>{nextAppt ? `${nextAppt.date}${nextAppt.time ? `, ${nextAppt.time}` : ""}` : "Not booked"}</dd></div>
                </dl>
                <div className="cs-head-foot no-print">
                  {d.new_items > 0 ? <span className="badge">{d.new_items} new from your doctor</span> : <span className="muted">Everything shared by your doctor is listed below.</span>}
                  <button type="button" className="btn small" onClick={printSheet}>Print case sheet</button>
                </div>
              </section>

              {/* ── sections ── */}
              <div className="cs-tabs no-print" role="tablist" aria-label="Record">
                {tabs.map(([k, label, n]) => (
                  <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{TAB_ICONS[k]}</svg>
                    <span className="lbl">{label}</span><span className="n">{n}</span>
                  </button>
                ))}
              </div>

              {tab === "visits" && (d.visits.length === 0 ? (
                <p className="empty">Nothing has been shared yet. After your visit, the doctor can share your summary, prescription and X-rays here.</p>
              ) : <div className="cs-stack">{d.visits.map((v, idx) => (
                <article className="cs-card cs-visit" key={v.visit_id}>
                  <header className="cs-vh">
                    <span className="cs-vno">Visit {d.visits.length - idx}</span>
                    <time>{v.date}</time>
                    <New on={v.summary_new} />
                  </header>
                  {v.message && <div className="note-from"><b>Message from your doctor:</b> {v.message}</div>}
                  {v.summary && <><Sub>Clinical notes</Sub><Summary v={v} /></>}
                  {v.prescriptions.length > 0 && <><Sub>Medicines</Sub>{v.prescriptions.map((rx) => <Prescription key={rx.id} rx={rx} patient={d.patient} clinic={d.clinic} compact />)}</>}
                  {(v.images.length > 0 || v.cbct.length > 0) && <><Sub>X-rays and photos</Sub>
                    {v.images.length > 0 && <div className="thumbs">{v.images.map((im) => <Thumb key={im.id} im={im} onOpen={setView} />)}</div>}
                    {v.cbct.length > 0 && <div className="files" style={{ marginTop: 10 }}>{v.cbct.map((cv) => <ScanRow key={cv.id} cv={cv} onOpen={setView} />)}</div>}</>}
                </article>
              ))}</div>)}

              {tab === "rx" && (all.rx.length ? <div className="cs-stack">{all.rx.map((rx) => <section className="cs-card" key={rx.id}><Prescription rx={rx} patient={d.patient} clinic={d.clinic} /></section>)}</div>
                : <p className="empty">No prescriptions shared yet.</p>)}

              {tab === "images" && (all.imgs.length + all.scans.length ? (
                <div className="cs-stack">
                  {Object.entries(all.imgs.reduce((g, im) => { const k = im.visit || im.date || "Other"; (g[k] = g[k] || []).push(im); return g; }, {})).map(([date, list]) => (
                    <section className="cs-card" key={date}><Sub>{date}</Sub><div className="thumbs">{list.map((im) => <Thumb key={im.id} im={im} onOpen={setView} />)}</div></section>
                  ))}
                  {all.scans.length > 0 && <section className="cs-card"><Sub>CBCT 3-D scans</Sub><div className="files">{all.scans.map((cv) => <ScanRow key={cv.id} cv={cv} onOpen={setView} />)}</div></section>}
                </div>
              ) : <p className="empty">No X-rays or scans shared yet.</p>)}

              {tab === "receipts" && (d.receipts.length ? <section className="cs-card"><Receipts list={d.receipts} /></section>
                : <p className="empty">No receipts shared yet.</p>)}

              {tab === "appts" && d.appointments && <Appointments a={d.appointments} />}

              <p className="cs-foot-note">This is a copy of your record as shared by your doctor. For any question about your treatment, call {CLINIC.phone} (Monday – Saturday, 11 am – 7 pm).</p>
            </>
          )}
        </div>
      </main>
      <Footer />
      {view && <Viewer open={view} onClose={() => setView(null)} />}
    </div>
  );
}
