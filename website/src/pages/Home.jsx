import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clinic, doctors, services, technology, protocols, portalSteps } from "../content";
import logoSrc from "../logo";
import { Bar, Footer, DraftNote, waLink } from "../components/Chrome";
import TechArt from "../components/TechArt";

const tel = (n) => `tel:${String(n).replace(/[^\d+]/g, "")}`;

/* ── small line icons (drawn for this site) ── */
const I = {
  phone: <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />,
  chat: <path d="M4 5h16v11H8l-4 4zM8 9h8M8 12h5" />,
  pin: <><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  award: <><circle cx="12" cy="9" r="5" /><path d="M9 13.5 7.5 21 12 18.5 16.5 21 15 13.5" /></>,
  shield: <path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z M9 12l2 2 4-4" />,
  spark: <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" />,
  tooth: <path d="M8 3c-3 0-4.5 2.2-4.5 5 0 3 1.5 4.5 2.2 6.8.8 3 .8 6.2 2.6 6.2 1.8 0 1.9-4.5 4.7-4.5s2.9 4.5 4.7 4.5c1.8 0 1.8-3.2 2.6-6.2.7-2.3 2.2-3.8 2.2-6.8 0-2.8-1.5-5-4.5-5-2.2 0-3 1.1-5 1.1S10.2 3 8 3z" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  check: <path d="M5 12.5 10 17 19 7" />,
  lock: <><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></>,
};
const Icon = ({ n, size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{I[n]}</svg>
);

/* ── hero: the clinic emblem with the doctor ── */
function HeroEmblem({ d }) {
  return (
    <div className="emblem">
      <div className="emblem-disc"><img src={logoSrc} alt="Sri Satya Sai Oral Health Centre emblem" /></div>
      <div className="emblem-doc">
        <span className="ed-mono" aria-hidden="true">{d.initials}</span>
        <span><b>{d.name}</b><small>{d.qualification}</small>{clinic.registration && <small>Reg. No. {clinic.registration}</small>}</span>
      </div>
    </div>
  );
}

/* ── treatments: the first 9, then the rest on request ── */
function Treatments() {
  const [all, setAll] = useState(false);
  const list = all ? services : services.slice(0, 9);
  return (
    <>
      <div className="t-grid">
        {list.map(([t, d]) => (
          <article className="t-card" key={t}>
            <span className="t-ico"><Icon n="tooth" size={22} /></span>
            <h3>{t}</h3>
            <p>{d}</p>
          </article>
        ))}
      </div>
      {services.length > 9 && (
        <div className="center">
          <button type="button" className="btn ghost" onClick={() => setAll((x) => !x)} aria-expanded={all}>
            {all ? "Show fewer treatments" : `Show all ${services.length} treatments`}
          </button>
        </div>
      )}
    </>
  );
}

/* ── technology: one tab per treatment, cards with photos ── */
function Technology() {
  const [g, setG] = useState(0);
  const group = technology[g];
  return (
    <>
      <div className="seg" role="tablist" aria-label="Technology by treatment">
        {technology.map((x, k) => (
          <button key={x.treatment} role="tab" aria-selected={k === g} aria-controls="tech-panel" id={`tg-${k}`} onClick={() => setG(k)}>
            {x.treatment}<span className="seg-n">{x.items.length}</span>
          </button>
        ))}
      </div>
      <div className="tech-grid" role="tabpanel" id="tech-panel" aria-labelledby={`tg-${g}`} key={g}>
        {group.items.map((t) => (
          <article className={`tc${t.photo ? " tc-photo" : ""}`} key={t.name}>
            <div className="tc-media"><TechArt name={t.art} photo={t.photo} label={t.name} /></div>
            <div className="tc-body">
              <h3>{t.name}</h3>
              <p className="tc-what">{t.what}</p>
              <p className="tc-why"><b>For you</b>{t.why}</p>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

function Protocols() {
  const [i, setI] = useState(0);
  const p = protocols[i];
  return (
    <div className="proto">
      <div className="proto-tabs" role="tablist" aria-label="Protocols">
        {protocols.map((x, k) => (
          <button key={x.title} role="tab" id={`pt-${k}`} aria-selected={k === i} aria-controls="pt-panel" onClick={() => setI(k)}>
            {x.title}<span>{x.steps.length} steps</span>
          </button>
        ))}
      </div>
      <div className="proto-panel" role="tabpanel" id="pt-panel" aria-labelledby={`pt-${i}`} key={i}>
        <h3>{p.title}</h3>
        <ol className="steps">{p.steps.map((s) => <li key={s}><span>{s}</span></li>)}</ol>
      </div>
    </div>
  );
}

function Doctor({ d }) {
  return (
    <div className="doctor">
      <aside className="doc-card">
        <div className="doc-mono" aria-hidden="true">{d.initials}</div>
        <h3 className="doc-name">{d.name}</h3>
        <div className="doc-q">{d.qualification}</div>
        <div className="doc-title">{d.title}</div>
        {clinic.registration && <div className="doc-reg">Dental Council Reg. No. {clinic.registration}</div>}
        <dl className="doc-stats">
          {d.stats.map(([big, small]) => <div key={small}><dt>{big}</dt><dd>{small}</dd></div>)}
        </dl>
        <div className="doc-actions">
          <a className="btn" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call for an appointment</a>
          <a className="btn ghost" href={waLink(`Hello, I would like an appointment with ${d.name}.`)} target="_blank" rel="noreferrer"><Icon n="chat" size={18} />WhatsApp</a>
        </div>
      </aside>
      <div className="doc-body">
        <h2>About the doctor</h2>
        {d.about.map((p) => <p key={p.slice(0, 20)} className="measure">{p}</p>)}
        <h3>Areas of care</h3>
        <ul className="doc-focus">{d.focus.map((f) => <li key={f}><Icon n="check" size={18} />{f}</li>)}</ul>
        <h3>Education and practice</h3>
        <ol className="doc-time">
          {d.timeline.map(([y, t, w]) => <li key={y}><span className="yr">{y}</span><span><b>{t}</b><br /><span className="muted">{w}</span></span></li>)}
        </ol>
      </div>
    </div>
  );
}

/* ── a phone showing the patient portal (illustration, sample data) ── */
function PortalPhone() {
  return (
    <div className="phone" aria-hidden="true">
      <div className="phone-notch" />
      <div className="phone-screen">
        <div className="ps-top"><b>Your record</b><span className="ps-new">3 new</span></div>
        <div className="ps-card ps-msg">From your doctor: root canal started on 36. Next sitting in 7 days.</div>
        <div className="ps-card"><span className="ps-ico"><Icon n="tooth" size={18} /></span><span><b>Visit summary</b><small>Diagnosis, treatment done, advice</small></span></div>
        <div className="ps-card"><span className="ps-ico"><Icon n="check" size={18} /></span><span><b>Prescription</b><small>2 medicines · print or save</small></span></div>
        <div className="ps-xray"><div /><div /><div /></div>
        <div className="ps-card"><span className="ps-ico"><Icon n="shield" size={18} /></span><span><b>Receipt</b><small>PDF</small></span></div>
      </div>
    </div>
  );
}

export default function Home() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 520);
    on(); window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  const d0 = doctors[0];
  return (
    <>
      <DraftNote />
      <Bar />
      <main id="top">
        {/* ── HERO ── */}
        <section className="hero">
          <div className="hero-glow" aria-hidden="true" />
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <p className="hero-place"><Icon n="pin" size={16} />Chaitanyapuri, near Dilsukhnagar, Hyderabad</p>
              <h1>{clinic.name}</h1>
              <p className="motto">{clinic.motto}</p>
              <p className="lead">{clinic.tagline}</p>
              <div className="hero-actions">
                <a className="btn light" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call {clinic.phone}</a>
                <a className="btn outline-light" href={waLink()} target="_blank" rel="noreferrer"><Icon n="chat" size={18} />Book on WhatsApp</a>
              </div>
              <p className="hero-note"><Icon n="clock" size={16} />Mon – Sat, 11 am – 7 pm · by appointment</p>
            </div>
            <HeroEmblem d={d0} />
          </div>
        </section>

        {/* ── TRUST STRIP ── */}
        <div className="wrap">
          <dl className="trust">
            <div><span className="tr-ico"><Icon n="award" /></span><dt>25 years</dt><dd>of dental practice</dd></div>
            <div><span className="tr-ico"><Icon n="tooth" /></span><dt>MDS</dt><dd>Oral Medicine &amp; Radiology</dd></div>
            <div><span className="tr-ico"><Icon n="spark" /></span><dt>Personalised dentistry</dt><dd>a treatment plan made for you, explained before we begin</dd></div>
            <div><span className="tr-ico"><Icon n="shield" /></span><dt>Sealed &amp; sterilised</dt><dd>every instrument, every patient</dd></div>
          </dl>
        </div>

        {/* ── TREATMENTS ── */}
        <section className="sec" id="treatments">
          <div className="wrap">
            <header className="sec-head">
              <h2>Treatments</h2>
              <p>Everything from a check-up to implants and full-mouth rehabilitation. The doctor explains the options and the cost before any treatment starts.</p>
            </header>
            <Treatments />
          </div>
        </section>

        {/* ── TECHNOLOGY ── */}
        <section className="sec sec-tint" id="technology">
          <div className="wrap">
            <header className="sec-head">
              <h2>Technology we use every day</h2>
              <p>Choose a treatment to see the equipment we use for it: what each one is, and what it changes for you.</p>
            </header>
            <Technology />
          </div>
        </section>

        {/* ── PROTOCOLS ── */}
        <section className="sec" id="protocols">
          <div className="wrap">
            <header className="sec-head">
              <h2>How we work</h2>
              <p>The steps we follow every time: from sterilising instruments to a root canal, a crown and a guided implant.</p>
            </header>
            <Protocols />
          </div>
        </section>

        {/* ── DOCTOR ── */}
        <section className="sec sec-tint" id="doctors">
          <div className="wrap"><Doctor d={d0} /></div>
        </section>

        {/* ── PORTAL ── */}
        <section className="sec portal-band" id="portal">
          <div className="wrap portal-grid">
            <div>
              <h2>Your dental records, on your phone</h2>
              <p className="pb-lead">Visit summaries, prescriptions, X-rays, scans and receipts, available when the doctor shares them with you.</p>
              <ol className="portal-steps">
                {portalSteps.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}
              </ol>
              <Link className="btn light" to="/portal"><Icon n="lock" size={18} />Log in to the patient portal</Link>
            </div>
            <PortalPhone />
          </div>
        </section>

        {/* ── VISIT ── */}
        <section className="sec" id="visit">
          <div className="wrap">
            <header className="sec-head"><h2>Visit us</h2><p>{clinic.hoursNote}</p></header>
            <div className="visit">
              {clinic.mapQuery && (
                <iframe className="map" title="Clinic location on the map" loading="lazy" referrerPolicy="no-referrer-when-downgrade"
                  src={`https://maps.google.com/maps?q=${encodeURIComponent(clinic.mapQuery)}&ll=${clinic.mapCenter}&z=17&output=embed`} />
              )}
              <div className="visit-card">
                <div className="vc-row"><span className="vc-ico"><Icon n="pin" /></span><div><b>Address</b>
                  <p>{clinic.address.map((l) => <span key={l}>{l}<br /></span>)}</p>
                  {clinic.mapsLink && <a className="link-arrow" href={clinic.mapsLink} target="_blank" rel="noreferrer">Get directions <Icon n="arrow" size={16} /></a>}</div></div>
                <div className="vc-row"><span className="vc-ico"><Icon n="clock" /></span><div><b>Timings</b>
                  <table className="hours"><tbody>{clinic.hours.map(([d, h]) => <tr key={d}><td>{d}</td><td>{h}</td></tr>)}</tbody></table></div></div>
                <div className="vc-row"><span className="vc-ico"><Icon n="phone" /></span><div><b>Appointments</b>
                  <p><a href={tel(clinic.phone)}>{clinic.phone}</a><br /><a href={`mailto:${clinic.email}`}>{clinic.email}</a></p></div></div>
                <div className="vc-actions">
                  <a className="btn" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call now</a>
                  <a className="btn ghost" href={waLink()} target="_blank" rel="noreferrer"><Icon n="chat" size={18} />WhatsApp</a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
      <a className={`wa-float${scrolled ? " show" : ""}`} href={waLink()} target="_blank" rel="noreferrer" aria-label="Book an appointment on WhatsApp">
        <Icon n="chat" size={24} /><span>Book on WhatsApp</span>
      </a>
    </>
  );
}