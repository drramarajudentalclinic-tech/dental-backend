import { Link } from "react-router-dom";
import * as content from "../content";

const { clinic } = content;

export function Logo({ size = 30 }) {
  // a simple molar outline — the clinic's own mark can replace this later
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path d="M9 4c-4 0-6 3-6 7 0 4 2 6 3 9 1 4 1 8 3.5 8 2.4 0 2.5-6 6.5-6s4.1 6 6.5 6c2.5 0 2.5-4 3.5-8 1-3 3-5 3-9 0-4-2-7-6-7-3 0-4 1.5-7 1.5S12 4 9 4z"
        fill="#dcefe9" stroke="#0f3d3e" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M12 10.5c1.4.8 2.7 1.1 4 1.1s2.6-.3 4-1.1" fill="none" stroke="#c4475f" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function Bar({ right }) {
  return (
    <header className="bar">
      <div className="wrap">
        <Link to="/" className="brand"><Logo /><span>{clinic.shortName}</span></Link>
        {right ?? (
          <>
            <nav className="nav" aria-label="Sections">
              <a href="/#treatments">Treatments</a>
              <a href="/#technology">Technology</a>
              <a href="/#protocols">How we work</a>
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
      <div className="wrap" style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <span>© {new Date().getFullYear()} {clinic.name}</span>
        {clinic.registration ? <span>Dental Council Reg. No. {clinic.registration}</span> : <span>{clinic.address[clinic.address.length - 1]}</span>}
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