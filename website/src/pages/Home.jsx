import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { clinic, doctors, services, technology, protocols, portalSteps, screening, faqs, YEARS } from "../content";
import * as photos from "../photos";
import logoSrc from "../logo";
import { Bar, Footer, DraftNote, waLink } from "../components/Chrome";
import TechArt from "../components/TechArt";
import ChatBot from "../components/ChatBot";
import { useMotion } from "../motion";
import { useEffects } from "../effects";

const tel = (n) => `tel:${String(n).replace(/[^\d+]/g, "")}`;
/* treatment information pages (plain pages in public/treatments, made for search engines and for sharing) */
const TREATMENT_PAGES = [
  ["dental-implants", "Dental implants"],
  ["root-canal-treatment", "Root canal treatment"],
  ["crowns-and-bridges", "Crowns and bridges"],
  ["braces-and-aligners", "Braces and clear aligners"],
  ["dentures", "Complete and partial dentures"],
  ["wisdom-tooth-removal", "Wisdom tooth removal and extractions"],
  ["gum-treatment", "Gum treatment and flap surgery"],
  ["laser-dentistry", "Laser dentistry"],
  ["oral-cancer-screening", "Oral cancer screening and mouth lesions"],
  ["teeth-cleaning", "Teeth cleaning and check-ups"],
  ["tooth-coloured-fillings", "Tooth-coloured fillings"],
  ["veneers", "Veneers and laminates"],
  ["childrens-dentistry", "Children's dentistry"],
];

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
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  metro: <><rect x="5" y="3" width="14" height="14" rx="3" /><path d="M5 11h14M9 17l-2 4M15 17l2 4M9 14h.01M15 14h.01" /></>,
  road: <path d="M8 3 5 21M16 3l3 18M12 5v2M12 11v2M12 17v2" />,
  nav: <path d="M3 11 21 3l-8 18-2-8z" />,
  share: <><circle cx="18" cy="5" r="2.5" /><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="19" r="2.5" /><path d="m8.2 10.8 7.6-4.4M8.2 13.2l7.6 4.4" /></>,
  lock: <><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></>,
  note: <path d="M7 3h10v4H7zM5 5H4v16h16V5h-1M8 12h8M8 16h5" />,
  rx: <path d="M6 3h7a4 4 0 0 1 0 8H6zM6 11v10M11 11l8 10M19 13l-6 8" />,
  image: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="m21 17-5-5-9 8" /></>,
  cube: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z" /><path d="m4 7.5 8 4.5 8-4.5M12 12v9" /></>,
  bill: <path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h3" />,
  cal: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></>,
};
const Icon = ({ n, size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{I[n]}</svg>
);

/* ── back to top: appears after scrolling; the ring fills as you read down the page ── */
function BackToTop() {
  const [p, setP] = useState(0);
  useEffect(() => {
    const on = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setP(max > 0 ? Math.min(1, window.scrollY / max) : 0);
    };
    on(); window.addEventListener("scroll", on, { passive: true }); window.addEventListener("resize", on);
    return () => { window.removeEventListener("scroll", on); window.removeEventListener("resize", on); };
  }, []);
  const C = 2 * Math.PI * 21;
  return (
    <button type="button" className={"to-top" + (p > 0.12 ? " show" : "")} aria-label="Back to top"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <circle className="tt-track" cx="24" cy="24" r="21" />
        <circle className="tt-ring" cx="24" cy="24" r="21" style={{ strokeDasharray: C, strokeDashoffset: C * (1 - p) }} />
        <path className="tt-arrow" d="M24 31V17M18 23l6-6 6 6" />
      </svg>
    </button>
  );
}

/* ── getting here: metro, landmark, road + direction buttons ── */
function GettingHere() {
  const [lat, lng] = (clinic.mapCenter || "").split(",");
  const dir = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  const share = `https://wa.me/?text=${encodeURIComponent(`${clinic.name}\n${clinic.address.join(", ")}\nMap: ${clinic.mapsLink}`)}`;
  const tips = [
    ["metro", "By metro", "Chaitanyapuri station on the Red line (Miyapur – LB Nagar). The clinic is opposite Metro Pillar No. 1563."],
    ["pin", "Landmark", "Rajanigandha Apartments, ground floor (G-15), opposite Metro Pillar No. 1563, near Dilsukhnagar."],
    ["road", "By road", "On the Dilsukhnagar – LB Nagar main road, under the metro line. Auto and cab drivers know Chaitanyapuri."],
  ];
  return (
    <div className="getting-here">
      <div className="gh-tips">
        {tips.map(([ico, t, d]) => (
          <div className="gh-tip" key={t}>
            <span className="gh-ico" aria-hidden="true"><Icon n={ico} size={22} /></span>
            <div><b>{t}</b><p>{d}</p></div>
          </div>
        ))}
      </div>
      <div className="gh-actions">
        <a className="btn" href={dir} target="_blank" rel="noreferrer"><Icon n="nav" size={18} />Get directions</a>
        <a className="btn ghost" href={clinic.mapsLink} target="_blank" rel="noreferrer"><Icon n="pin" size={18} />Open in Google Maps</a>
        <a className="btn ghost" href={share} target="_blank" rel="noreferrer"><Icon n="share" size={18} />Send location on WhatsApp</a>
      </div>
    </div>
  );
}

/* ── open now / closed badge: Mon–Sat 11 am – 7 pm, India time (whatever the visitor's own clock says) ── */
const WEEK_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const OPEN_H = 11, CLOSE_H = 19;
function clinicStatus() {
  const ist = new Date(Date.now() + 330 * 60000);            // UTC + 5:30
  const day = ist.getUTCDay(), mins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
  const openDay = (d) => d !== 0;                             // closed on Sunday
  if (openDay(day) && mins >= OPEN_H * 60 && mins < CLOSE_H * 60) {
    const left = CLOSE_H * 60 - mins;
    return { open: true, soon: left <= 60, short: "Open now", text: left <= 60 ? `Open now · closes in ${left} min` : "Open now · closes 7 pm" };
  }
  if (openDay(day) && mins < OPEN_H * 60) return { open: false, short: "Closed now", text: "Closed now · opens today 11 am" };
  let d = (day + 1) % 7;
  while (!openDay(d)) d = (d + 1) % 7;
  return { open: false, short: "Closed now", text: `Closed now · opens ${d === (day + 1) % 7 ? "tomorrow" : WEEK_DAYS[d]} 11 am` };
}
function OpenBadge() {
  const [st, setSt] = useState(clinicStatus);
  useEffect(() => { const id = setInterval(() => setSt(clinicStatus()), 30000); return () => clearInterval(id); }, []);
  return (
    <span className={"open-badge" + (st.open ? " is-open" : "") + (st.soon ? " is-soon" : "")} role="status">
      <i aria-hidden="true" /><span className="ob-full">{st.text}</span><span className="ob-short">{st.short}</span>
    </span>
  );
}

/* ── extras placed inside the menu bar (home page): open-now on the left, call + WhatsApp before Patient login ── */
function BarExtras() {
  const [host, setHost] = useState(null);
  useEffect(() => { setHost(document.querySelector(".bar .wrap")); }, []);
  if (!host) return null;
  return createPortal(
    <>
      <div className="bar-left"><OpenBadge /></div>
      <div className="bar-icons">
        <a className="bar-ico call" href={tel(clinic.phone)} aria-label={`Call the clinic: ${clinic.phone}`}>
          <Icon n="phone" size={18} /><span className="bar-tip">Call {clinic.phone}</span>
        </a>
        <a className="bar-ico wa" href={waLink()} target="_blank" rel="noreferrer" aria-label="Message the clinic on WhatsApp">
          <Icon n="chat" size={18} /><span className="bar-tip">WhatsApp us</span>
        </a>
      </div>
    </>,
    host
  );
}


/* ── what happens at the first visit ── */
const FIRST_VISIT = [
  ["pin", "Arrive and register", "Reception notes your details and medical history. Bring old X-rays, reports and the list of medicines you take."],
  ["tooth", "Check-up", "Dr. Rama Raju examines your teeth, gums and the soft tissues of the mouth. An X-ray is taken only if it is needed."],
  ["spark", "Your plan, explained", "The options, number of visits and cost are explained in plain words before anything starts. You decide."],
  ["check", "Treatment or next date", "If treatment is needed, it may start the same day, or your next appointment is fixed before you leave."],
];
function FirstVisit() {
  const ref = useRef(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {   // show the steps once they scroll into view (always shown if the browser can't tell)
    const el = ref.current;
    if (!el || !("IntersectionObserver" in window)) { setSeen(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } }, { threshold: 0.15 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <section className={"sec first-visit" + (seen ? " fv-in" : "")} id="first-visit" ref={ref}>
      <div className="wrap">
        <header className="sec-head"><span className="kicker">Your first visit</span><h2>What happens when you come in</h2>
          <p>Four simple steps, so you know what to expect before you arrive.</p></header>
        <ol className="fv-steps">
          {FIRST_VISIT.map(([ico, t, d], k) => (
            <li key={t} style={{ "--rd": k * 120 + "ms" }}>
              <span className="fv-num" aria-hidden="true">{k + 1}</span>
              <span className="fv-ico" aria-hidden="true"><Icon n={ico} size={22} /></span>
              <h3>{t}</h3>
              <p>{d}</p>
            </li>
          ))}
        </ol>
        <div className="fv-bring">
          <b>Please bring:</b>
          <span>Old X-rays or scans</span><span>Medical reports</span><span>List of current medicines</span><span>Any dental prescriptions</span>
        </div>
      </div>
    </section>
  );
}

/* ── treatments: the first 9, then the rest on request ── */
function Treatments() {
  const [all, setAll] = useState(false);
  const list = all ? services : services.slice(0, 12);
  return (
    <>
      <div className="t-grid">
        {list.map(([t, d, proto]) => (
          <article className="t-card" key={t}>
            <span className="t-ico"><Icon n="tooth" size={22} /></span>
            <h3>{t}</h3>
            <p>{d}</p>
            {proto && <button type="button" className="t-more" onClick={() => showProtocol(proto)}>See the steps <Icon n="arrow" size={16} /></button>}
          </article>
        ))}
      </div>
      {services.length > 12 && (
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
/* Treatment cards and equipment cards can open a protocol ("See the steps"). */
const showProtocol = (title) => window.dispatchEvent(new CustomEvent("show-protocol", { detail: title }));

/* ── equipment ↔ treatment links ── */
const TECH_ITEMS = technology.flatMap((g) => g.items.flatMap((it) => [it, ...(it.slides || [])]));
const TECH_ALIAS = {
  "Digital X-ray (RVG)": "Digital X-rays (RVG) and hand-held portable X-ray", "Endo motor": "Endo motor and rotary files", "Cicada DT Fill": "Cicada DT Fill thermal obturator",
  "Runyes scanner": "Runyes 3DS V3 Pro intra-oral scanner", "Micro-blaster": "Aluminium-oxide micro-blaster", "Surgical guide": "Surgical guide for implants",
  "PRFuge": "PRFuge centrifuge (PRF)", "Ivoclean": "Ivoclean cleaning paste (Ivoclar)", "3-D printer": "ELEGOO Saturn 4 Ultra 16K 3-D printer",
  "Laser therapy unit": "Advanced laser therapy unit", "Dental laser": "Dental laser (soft-tissue)", "BioActive RCS": "SafeEndo BioActive RCS (bioceramic sealer)",
  "Electrosurgery unit": "Solid-state electrosurgery unit",
  "Germicidal UV lamp": "Germicidal UV-C lamp",
};
const techFor = (tag) => TECH_ITEMS.find((t) => t.name === (TECH_ALIAS[tag] || tag));
/* treatments (protocol titles) that use a technology item */
const sameItem = (a, b) => !!a && !!b && (a === b || a.photo && a.photo === b.photo);   // e.g. RVG shown in two groups
const usedIn = (item) => protocols.filter((p) => (p.uses || []).some(([tag]) => sameItem(techFor(tag), item))).map((p) => p.title);

/* one equipment card; an item with `slides` shows them one after another (PRFuge → PRF & GRF box) */
function TechCard({ t }) {
  const pages = [t, ...(t.slides || [])];
  const [i, setI] = useState(0);
  const [hold, setHold] = useState(false);
  useEffect(() => {
    if (pages.length < 2 || hold) return undefined;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return undefined;
    const id = setInterval(() => setI((x) => (x + 1) % pages.length), 2800);   // quick; pauses while the pointer is on the card
    return () => clearInterval(id);
  }, [pages.length, hold]);
  const cur = pages[i];
  const used = usedIn(cur);
  return (
    <article className={`tc${cur.photo ? " tc-photo" : ""}${pages.length > 1 ? " tc-slides" : ""}${pages.length > 1 && hold ? " paused" : ""}`}
      onMouseEnter={() => setHold(true)} onMouseLeave={() => setHold(false)} onFocus={() => setHold(true)} onBlur={() => setHold(false)}>
      <div className="tc-media">
        {pages.map((pg, k) => (
          <div key={pg.name} className={`tc-slide${k === i ? " on" : ""}`} aria-hidden={k !== i}>
            <TechArt name={pg.art} photo={pg.photo} label={pg.name} />
          </div>
        ))}
        {pages.length > 1 && (
          <div className="tc-dots" role="tablist" aria-label={`${t.name}: pictures`}>
            {pages.map((pg, k) => (
              <button key={pg.name} type="button" role="tab" aria-selected={k === i} aria-label={pg.name} onClick={() => setI(k)} />
            ))}
          </div>
        )}
        {pages.length > 1 && (
          <>
            <button type="button" className="tc-arrow prev" aria-label="Previous" onClick={() => setI((x) => (x - 1 + pages.length) % pages.length)}>‹</button>
            <button type="button" className="tc-arrow next" aria-label="Next" onClick={() => setI((x) => (x + 1) % pages.length)}>›</button>
          </>
        )}
      </div>
      <div className="tc-body" key={cur.name}>
        {pages.length > 1 && <span className="tc-step">{i + 1} of {pages.length}</span>}
        <h3>{cur.name}</h3>
        <p className="tc-what">{cur.what}</p>
        <p className="tc-why"><b>For you</b>{cur.why}</p>
        {used.length > 0 && (
          <div className="tc-used"><b>Used in</b>
            {used.map((title) => <button type="button" key={title} onClick={() => showProtocol(title)}>{title}</button>)}
          </div>
        )}
      </div>
    </article>
  );
}

function Technology() {
  const [g, setG] = useState(0);
  useEffect(() => {
    const on = (e) => {
      const k = technology.findIndex((x) => x.treatment.startsWith(e.detail));
      if (k >= 0) { setG(k); document.getElementById("technology")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
    };
    window.addEventListener("show-tech", on);
    return () => window.removeEventListener("show-tech", on);
  }, []);
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
        {group.items.map((t) => <TechCard key={t.name} t={t} />)}
      </div>
    </>
  );
}


function Protocols() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const on = (e) => {
      const k = protocols.findIndex((x) => x.title === e.detail);
      if (k >= 0) { setI(k); document.getElementById("protocols")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
    };
    window.addEventListener("show-protocol", on);
    return () => window.removeEventListener("show-protocol", on);
  }, []);
  const p = protocols[i];
  const groups = [...new Set(protocols.map((x) => x.group))];
  return (
    <div className="proto">
      <div className="proto-nav">
        <label className="proto-select">Choose a treatment
          <select value={i} onChange={(e) => setI(Number(e.target.value))}>
            {groups.map((g) => (
              <optgroup key={g} label={g}>
                {protocols.map((x, k) => x.group === g && <option key={x.title} value={k}>{x.title}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <div className="proto-tabs" role="tablist" aria-label="Treatment protocols">
          {groups.map((g) => (
            <div className="proto-group" key={g}>
              <span className="proto-gh">{g}</span>
              {protocols.map((x, k) => x.group === g && (
                <button key={x.title} role="tab" id={`pt-${k}`} aria-selected={k === i} aria-controls="pt-panel" onClick={() => setI(k)}>
                  {x.title}<span>{x.steps.length} steps</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="proto-panel" role="tabpanel" id="pt-panel" aria-labelledby={`pt-${i}`} key={i}>
        <span className="proto-cat">{p.group}</span>
        <h3>{p.title}</h3>
        {p.uses?.length > 0 && (
          <div className="proto-eq">
            <b className="proto-eq-h">Equipment used in this treatment</b>
            <ul>
              {p.uses.map(([tag, purpose, onlyWhere]) => {
                const item = techFor(tag);
                return (
                  <li key={tag}>
                    <span className="pe-thumb">{item ? <TechArt name={item.art} photo={item.photo} label={tag} /> : null}</span>
                    <span className="pe-text"><b>{tag}</b>{onlyWhere && <em>where needed</em>}<span>{purpose}</span></span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        <ol className="steps">{p.steps.map((s) => <li key={s}><span>{s}</span></li>)}</ol>
        <div className="proto-cta">
          <span>Questions about this treatment?</span>
          <a className="btn small" href={waLink(`Hello, I have a question about ${p.title.toLowerCase()}.`)} target="_blank" rel="noreferrer"><Icon n="chat" size={16} />Ask on WhatsApp</a>
        </div>
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
        {d.inventions?.length > 0 && <div className="doc-inv-chip">🏅 Founder &amp; patent holder of {d.inventions.length} dental devices</div>}
        <div className="doc-inv-chip doc-ceo-chip">CEO, Raamah Biocare Pvt. Ltd.</div>
        <dl className="doc-stats">
          {d.stats.map(([big, small]) => <div key={small}><dt>{big}</dt><dd>{small}</dd></div>)}
        </dl>
        <div className="doc-actions">
          <a className="btn" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call for an appointment</a>
          <a className="btn ghost" href={waLink(`Hello, I would like an appointment with ${d.name}.`)} target="_blank" rel="noreferrer"><Icon n="chat" size={18} />WhatsApp</a>
        </div>
      </aside>
      <div className="doc-body">
        <span className="kicker">Your dentist</span>
        <h2>About the doctor</h2>
        {d.about.map((p) => <p key={p.slice(0, 20)} className="measure">{p}</p>)}
        {d.inventions?.length > 0 && (
          <>
            <h3>Founder and patent holder</h3>
            <p className="muted doc-inv-lead">Devices invented by Dr. D. Rama Raju, made in India by Raamah Biocare Pvt. Ltd. (where he is CEO), and used at the clinic.</p>
            <div className="doc-inv">
              {d.inventions.map((x) => (
                <button key={x.name} type="button" className="doc-inv-card" onClick={() => window.dispatchEvent(new CustomEvent("show-tech", { detail: x.tab }))}>
                  <span className="dic-img"><img src={x.photo} alt="" loading="lazy" decoding="async" /></span>
                  <b>{x.name}</b>
                  <small>{x.line}</small>
                  <span className="dic-badge">Patent holder</span>
                </button>
              ))}
            </div>
          </>
        )}
        <h3>Areas of care</h3>
        <ul className="doc-focus">{d.focus.map((f) => <li key={f}><Icon n="check" size={18} />{f}</li>)}</ul>
        <h3>Education and practice</h3>
        <ol className="doc-time">
          {d.timeline.map(([t, w]) => <li key={t}><span><b>{t}</b><br /><span className="muted">{w}</span></span></li>)}
        </ol>
      </div>
    </div>
  );
}


/* ── oral cancer screening (DrOroscope) ── */
function Screening() {
  const s = screening;
  return (
    <>
      <div className="scr-top">
        <figure className="scr-photo"><img src={photos.oroscope} alt="DrOroscope hand-held oral screening camera" loading="lazy" decoding="async" /></figure>
        <div>
          <span className="kicker">Early detection</span>
          <h2>{s.title}</h2>
          <p className="scr-lead">{s.lead}</p>
        </div>
      </div>
      <div className="scr-benefits">
        {s.benefits.map(([t, d]) => <div key={t}><b>{t}</b><span>{d}</span></div>)}
      </div>
    </>
  );
}


/* ── appointment request: fills a WhatsApp message (nothing is stored on the website) ── */
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SLOTS = ["Morning (11 am – 1 pm)", "Afternoon (1 – 4 pm)", "Evening (4 – 7 pm)"];
function BookForm({ compact = false }) {
  const [f, setF] = useState({ name: "", phone: "", day: "", slot: "", reason: "", note: "" });
  const [err, setErr] = useState("");
  const set = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const send = (e) => {
    e.preventDefault();
    const digits = f.phone.replace(/\D/g, "").replace(/^91(?=\d{10}$)/, "");
    if (!f.name.trim()) { setErr("Please enter your name."); return; }
    if (!/^[6-9]\d{9}$/.test(digits)) { setErr("Please enter a 10-digit mobile number."); return; }
    setErr("");
    const text = [
      "Hello, I would like to book an appointment.",
      `Name: ${f.name.trim()}`,
      `Mobile: ${digits}`,
      f.day && `Preferred day: ${f.day}`,
      f.slot && `Preferred time: ${f.slot}`,
      f.reason && `Reason: ${f.reason}`,
      f.note.trim() && `Note: ${f.note.trim()}`,
    ].filter(Boolean).join("\n");
    window.open(waLink(text), "_blank", "noopener");
  };
  return (
    <form className={`book-form${compact ? " compact" : ""}`} onSubmit={send} noValidate>
      {compact ? (
        <div className="bf-grid">
          <label className="bf-wide">Your name<input value={f.name} onChange={set("name")} autoComplete="name" required /></label>
          <label className="bf-wide">Mobile number<input value={f.phone} onChange={set("phone")} type="tel" inputMode="numeric" autoComplete="tel-national" placeholder="98765 43210" required /></label>
          <label>Preferred day<select value={f.day} onChange={set("day")}><option value="">Any day</option>{DAYS.map((d) => <option key={d}>{d}</option>)}</select></label>
          <label>Reason<select value={f.reason} onChange={set("reason")}><option value="">Choose</option>
            {services.map(([t]) => <option key={t}>{t}</option>)}<option>Tooth pain or swelling</option><option>Other</option></select></label>
        </div>
      ) : (
      <div className="bf-grid">
        <label>Your name<input value={f.name} onChange={set("name")} autoComplete="name" required /></label>
        <label>Mobile number<input value={f.phone} onChange={set("phone")} type="tel" inputMode="numeric" autoComplete="tel-national" placeholder="98765 43210" required /></label>
        <label>Preferred day<select value={f.day} onChange={set("day")}><option value="">Any day</option>{DAYS.map((d) => <option key={d}>{d}</option>)}</select></label>
        <label>Preferred time<select value={f.slot} onChange={set("slot")}><option value="">Any time</option>{SLOTS.map((d) => <option key={d}>{d}</option>)}</select></label>
        <label className="bf-wide">Reason for the visit<select value={f.reason} onChange={set("reason")}><option value="">Choose (optional)</option>
          {services.map(([t]) => <option key={t}>{t}</option>)}<option>Tooth pain or swelling</option><option>Other</option></select></label>
        <label className="bf-wide">Anything else (optional)<textarea value={f.note} onChange={set("note")} rows={3} /></label>
      </div>
      )}
      {err && <p className="bf-err" role="alert">{err}</p>}
      <button className="btn bf-send" type="submit"><Icon n="chat" size={18} />Send request on WhatsApp</button>
      <p className="bf-note">{compact ? "Opens WhatsApp with your request ready to send. The clinic confirms the time." : "This opens WhatsApp with your request ready to send. The clinic replies to confirm the time. Nothing is saved on this website."}</p>
    </form>
  );
}

function Faq() {
  return (
    <div className="faq">
      {faqs.map(([q, a]) => (
        <details key={q}>
          <summary>{q}<span className="faq-plus" aria-hidden="true" /></summary>
          <p>{a}</p>
        </details>
      ))}
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
  useMotion();
  useEffects();
  useEffect(() => {   // home page: the masthead shows the clinic name, so the menu bar hides its own
    document.documentElement.classList.add("is-home");
    return () => document.documentElement.classList.remove("is-home");
  }, []);
  const d0 = doctors[0];
  return (
    <>
      <div className="scroll-progress" aria-hidden="true" />
      <DraftNote />
      {/* ── MASTHEAD: logo + full clinic name, motto, area (the menu bar sits below it) ── */}
      <header className="masthead">
        <div className="hero-head">
          <div className="mh-name">
            <img className="mh-logo" src={logoSrc} alt="" aria-hidden="true" />
            <h1 className="hero-name">{clinic.name}</h1>
          </div>
          <h2 className="motto">
            <span className="sr-only">{clinic.motto}</span>
            {clinic.motto.split(" ").map((w, i, all) => (
              <span key={i} className={"mw" + (i >= all.length - 2 ? " hl" : "")} style={{ "--wi": i }} aria-hidden="true">{w}</span>
            ))}
          </h2>
          <p className="hero-place"><Icon n="pin" size={16} />Chaitanyapuri, near Dilsukhnagar, Hyderabad</p>
        </div>
      </header>
      <Bar />
      <BarExtras />
      <main id="top">
        {/* ── HERO ── */}
        <section className="hero">
          <div className="hero-glow" aria-hidden="true" />
          <div className="hero-orb o1" aria-hidden="true" /><div className="hero-orb o2" aria-hidden="true" />
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <p className="lead">{clinic.tagline}</p>
              <a className="hero-doc" href="#doctors">
                <span className="ed-mono" aria-hidden="true"><Icon n="user" size={20} /></span>
                <span><b>Know about your doctor</b><small>Qualifications, experience and the dental devices he invented</small></span>
                <Icon n="arrow" size={18} />
              </a>
              <div className="hero-actions">
                <a className="btn light" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call {clinic.phone}</a>
                <a className="btn outline-light" href="#treatments">See treatments <Icon n="arrow" size={18} /></a>
              </div>
              <a className="hero-portal" href="#portal"><span className="pb-new">New</span>Your dental records, X-rays and prescriptions on your phone<Icon n="arrow" size={16} /></a>
            </div>
            {clinic.pillars?.length > 0 && (
              <ul className="hero-pillars hero-side">
                {clinic.pillars.map(([t, d], k) => (
                  <li key={t}>
                    <span className="hp-ico" aria-hidden="true"><Icon n={k === 0 ? "spark" : "shield"} size={18} /></span>
                    <span><b>{t}</b><small>{d}</small></span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* ── TRUST STRIP ── */}
        <div className="wrap">
          <dl className="trust trust-4 trust-three">
            <div><span className="tr-ico"><Icon n="tooth" /></span><dt>MDS</dt><dd>Master of Dental Surgery</dd></div>
            <div className="tr-pink"><span className="tr-ico"><Icon n="spark" /></span><dt>4 devices</dt><dd>invented and patented by Dr. Rama Raju</dd></div>
            <div><span className="tr-ico"><Icon n="shield" /></span><dt>Since {clinic.since || "1999"}</dt><dd>caring for patients in Chaitanyapuri</dd></div>
          </dl>
        </div>

        {/* ── TREATMENTS ── */}
        <section className="sec" id="treatments">
          <div className="wrap">
            <header className="sec-head">
              <span className="kicker">What we do</span>
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
              <span className="kicker">Equipment</span>
              <h2>Technology we use every day</h2>
              <p>Choose a treatment to see the equipment we use for it: what each one is, and what it changes for you.</p>
            </header>
            <Technology />
            {/* oral cancer screening, part of the technology section */}
            <div className="tech-screening" id="screening"><Screening /></div>
          </div>
        </section>

        {/* ── PROTOCOLS ── */}
        <section className="sec sec-tint" id="protocols">
          <div className="wrap">
            <header className="sec-head">
              <span className="kicker">Treatment protocols</span>
              <h2>How we work</h2>
              <p>The steps we follow for each treatment, and the equipment we use at each step. Choose a treatment to see its protocol.</p>
            </header>
            <Protocols />
          </div>
        </section>

        {/* ── DOCTOR ── */}
        <section className="sec" id="doctors">
          <div className="wrap"><Doctor d={d0} /></div>
        </section>

        {/* ── PORTAL ── */}
        <section className="sec portal-band" id="portal">
          <div className="wrap"><div className="pb-frame"><div className="portal-grid">
            <div>
              <div className="pb-flag"><Icon n="lock" size={15} />Your clinic records, online</div>
              <span className="kicker light">Patient portal</span>
              <h2>Your dental records, <em className="pb-hl">on your phone</em></h2>
              <p className="pb-lead">After each visit, see what your doctor shares with you, any time, on your phone. No files to carry, no papers to lose.</p>
              <ul className="pb-chips">
                {[["note", "Visit summaries"], ["rx", "Prescriptions"], ["image", "X-rays and photos"], ["bill", "Receipts"], ["cal", "Appointments"]].map(([i, t]) => (
                  <li key={t}><Icon n={i} size={16} />{t}</li>
                ))}
              </ul>
              <ol className="portal-steps pb-steps">
                {portalSteps.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}
              </ol>
              <div className="pb-actions">
                <Link className="btn light pb-cta" to="/portal"><Icon n="lock" size={18} />Log in to the patient portal</Link>
                <span className="pb-safe"><Icon n="shield" size={16} />Secure login with a one-time code sent to your registered mobile.</span>
              </div>
            </div>
            <figure className="pb-photo"><img src={photos.portalScreens} alt="Patient record on the clinic computer and in the patient portal on a phone" loading="lazy" decoding="async" /></figure>
          </div></div></div>
        </section>

        {/* ── FIRST VISIT ── */}
        <FirstVisit />

        {/* ── BOOK ── */}
        <section className="sec" id="book">
          <div className="wrap book-grid">
            <div>
              <span className="kicker">Appointments</span>
              <h2>Book an appointment</h2>
              <p className="book-lead">Tell us when suits you and what you need. The clinic will confirm a time on WhatsApp.</p>
              <ul className="book-points">
                <li><Icon n="clock" size={18} />Monday to Saturday, 11 am – 7 pm, by appointment</li>
                <li><Icon n="phone" size={18} /><span>Prefer to talk? Call <a href={tel(clinic.phone)}>{clinic.phone}</a><small className="book-hours">Call between 11:00 am and 7:00 pm, Monday to Saturday. Sunday is a holiday.</small></span></li>
                <li><Icon n="pin" size={18} />Opposite Metro Pillar No. 1563, Chaitanyapuri</li>
              </ul>
            </div>
            <BookForm />
          </div>
        </section>

        {/* ── FAQ ── */}
        <section className="sec sec-tint" id="faq">
          <div className="wrap faq-grid">
            <header className="sec-head"><span className="kicker">FAQ</span><h2>Common questions</h2><p>Short answers to what patients ask most. For anything else, call or WhatsApp the clinic.</p></header>
            <Faq />
          </div>
        </section>

        {/* ── VISIT ── */}
        <section className="sec" id="visit">
          <div className="wrap">
            <header className="sec-head"><span className="kicker">Find us</span><h2>Visit us</h2><p>{clinic.hoursNote}</p></header>
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
            <GettingHere />
          </div>
        </section>
        <section className="treat-links" aria-label="Treatment information">
          <div className="wrap">
            <h2>Treatment information</h2>
            <p>How each treatment is done at the clinic, step by step.</p>
            <ul>{TREATMENT_PAGES.map(([slug, name]) => <li key={slug}><a href={`/treatments/${slug}.html`}>{name}</a></li>)}</ul>
            <p><a href="/treatments/">All treatments →</a> · <a href="/aftercare/">Aftercare instructions →</a></p>
          </div>
        </section>
      </main>
      <Footer />
      <nav className="mobile-bar" aria-label="Contact the clinic">
        <a className="mb-call" href={tel(clinic.phone)}><Icon n="phone" size={20} />Call</a>
        <a className="mb-wa" href={waLink()} target="_blank" rel="noreferrer"><Icon n="chat" size={20} />WhatsApp</a>
        <a href="#book"><Icon n="clock" size={20} />Book</a>
        <button type="button" className="ask" onClick={() => window.dispatchEvent(new Event("open-chat"))}><Icon n="chat" size={20} />Ask us</button>
      </nav>
      <a className={`wa-float${scrolled ? " show" : ""}`} href={waLink()} target="_blank" rel="noreferrer" aria-label="Book an appointment on WhatsApp">
        <Icon n="chat" size={24} /><span>Book on WhatsApp</span>
      </a>
      <BackToTop />
      <ChatBot />
    </>
  );
}