import { Link } from "react-router-dom";
import * as content from "../content";

const { clinic } = content;
const tel = (n) => `tel:${String(n).replace(/[^\d+]/g, "")}`;
export const waLink = (text) => `https://wa.me/${clinic.whatsapp.replace(/\D/g, "")}?text=${encodeURIComponent(text || "Hello, I would like to book an appointment.")}`;

/* The clinic's own logo (public/logo.png). */
export function Logo({ size = 52 }) {
  return <img src="/logo.png" alt="" width={size} height={Math.round(size * 0.92)} className="logo-img" />;
}

/* Full clinic name, set in two lines so it stays readable on phones. */
function BrandName() {
  return (
    <span className="brand-name">
      <span className="bn-1">Sri Satya Sai</span>
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
              <a href="/#treatments">Treatments</a>
              <a href="/#technology">Technology</a>
              <a href="/#doctors">Doctor</a>
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