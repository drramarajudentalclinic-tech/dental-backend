import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import * as content from "../content";
import logoSrc from "../logo";

const { clinic } = content;
const tel = (n) => `tel:${String(n).replace(/[^\d+]/g, "")}`;
/* Clinic hours: Monday–Saturday, 11 am – 7 pm, India time (whatever the visitor's own clock says). */
export function clinicOpenNow() {
  const ist = new Date(Date.now() + 330 * 60000);            // UTC + 5:30
  const day = ist.getUTCDay(), mins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
  return day !== 0 && mins >= 11 * 60 && mins < 19 * 60;
}
const digits = (n) => String(n || "").replace(/\D/g, "");
const MAIN_WA = digits(clinic.whatsapp);
const AFTER_WA = digits(clinic.afterHoursWhatsapp);
/* WhatsApp goes to the clinic number in clinic hours, and to the message-only number when closed. */
export const waNumberNow = () => (AFTER_WA && !clinicOpenNow() ? AFTER_WA : MAIN_WA);
export const waLink = (text) => `https://wa.me/${waNumberNow()}?text=${encodeURIComponent(text || "Hello, I would like to book an appointment.")}`;

/* When the clinic will reply to an after-hours message (India time):
   before 11 am Mon–Sat → today; after 7 pm Mon–Fri and Sunday → tomorrow; after 7 pm Saturday → Monday. */
export function replyWhen() {
  const ist = new Date(Date.now() + 330 * 60000);
  const day = ist.getUTCDay(), mins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
  if (day !== 0 && mins < 11 * 60) return "today after 11 am";
  if (day === 6) return "on Monday morning after 11 am";
  return "tomorrow morning after 11 am";
}

/* true while the clinic is closed; checked again every 30 seconds */
export function useClinicClosed() {
  const [closed, setClosed] = useState(() => !clinicOpenNow());
  useEffect(() => {
    const id = setInterval(() => setClosed(!clinicOpenNow()), 30000);
    return () => clearInterval(id);
  }, []);
  // a WhatsApp link drawn earlier still goes to the right number when it is clicked
  useEffect(() => {
    if (!AFTER_WA) return undefined;
    const onClick = (e) => {
      const a = e.target.closest && e.target.closest('a[href*="wa.me/"]');
      if (!a) return;
      const want = waNumberNow(), other = want === AFTER_WA ? MAIN_WA : AFTER_WA;
      if (a.href.includes(`wa.me/${other}`)) a.href = a.href.replace(`wa.me/${other}`, `wa.me/${want}`);
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);
  return closed;
}

/* Shown only while the clinic is closed: the message-only number for appointments. */
export function AfterHoursNote({ variant = "strip" }) {
  const closed = useClinicClosed();
  const [, setTick] = useState(0);                 // redraw each minute so the reply time stays right past midnight
  useEffect(() => { const id = setInterval(() => setTick((t) => t + 1), 60000); return () => clearInterval(id); }, []);
  if (!closed || !AFTER_WA) return null;
  return (
    <div className={`ah-note ah-${variant}`} role="note">
      <span className="ah-text">
        <b>Clinic closed now.</b> For appointments, <b>message only</b> on WhatsApp:{" "}
        <a href={waLink()} target="_blank" rel="noreferrer" className="ah-num">{clinic.afterHoursWhatsapp}</a>.{" "}
        We will respond as soon as possible, {replyWhen()}.
      </span>
      <span className="ah-tag">Message only · no calls</span>
    </div>
  );
}

/* The clinic's own logo (built in: src/logo.js). */
export function Logo({ size = 52 }) {
  return <img src={logoSrc} alt="" width={size} height={Math.round(size * 0.92)} className="logo-img" />;
}

/* Full clinic name, set in two lines so it stays readable on phones. */
function BrandName() {
  return (
    <span className="brand-name">
      <span className="bn-1">Sri Satya Sai</span>{" "}
      <span className="bn-2">Oral Health Center &amp; Dental Clinic</span>
    </span>
  );
}

export function Bar({ right }) {
  return (
    <header className="bar">
      <div className="wrap">
        <Link to="/" className="brand" aria-label={clinic.name}><Logo /><BrandName /></Link>
        {right ?? (
          <>
            <nav className="nav" aria-label="Sections">
              <a href="/#doctors">Doctor</a>
              <a href="/#treatments">Treatments</a>
              <a href="/#technology">Technology</a>
              <a href="/#book" className="nav-book">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" /></svg>
                Book a visit
              </a>
              <a href="/#visit">Visit us</a>
            </nav>
            <Link className="btn small" to="/portal">Patient login</Link>
          </>
        )}
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="foot">
      <div className="wrap foot-grid">
        <div className="foot-brand">
          <Logo size={64} />
          <div>
            <b>{clinic.name}</b>
            <span className="foot-motto">{clinic.motto}</span>
          </div>
        </div>
        <div>
          <b>Address</b>
          <p>{clinic.address.map((l) => <span key={l}>{l}<br /></span>)}</p>
          {clinic.mapsLink && <a href={clinic.mapsLink} target="_blank" rel="noreferrer">Directions in Google Maps</a>}
        </div>
        <div>
          <b>Appointments</b>
          <p><a href={tel(clinic.phone)}>{clinic.phone}</a><br /><a href={waLink()} target="_blank" rel="noreferrer">WhatsApp</a><br />
            {clinic.hours.map(([d, h]) => <span key={d}>{d}: {h}<br /></span>)}</p>
        </div>
      </div>
      <div className="wrap foot-base">
        <span>© {new Date().getFullYear()} {clinic.name}</span>
        {clinic.registration && <span>Dental Council Reg. No. {clinic.registration}</span>}
      </div>
    </footer>
  );
}

/* Shown only while content.js still has [placeholders]. */
const hasPlaceholders = (function find(v) {
  if (typeof v === "string") return /\[[^\]]+\]/.test(v);
  if (Array.isArray(v)) return v.some(find);
  if (v && typeof v === "object") return Object.values(v).some(find);
  return false;
})({ ...content });
export function DraftNote() {
  if (!hasPlaceholders) return null;
  return <div className="draft" role="note">Draft website — some clinic details are still being filled in.</div>;
}