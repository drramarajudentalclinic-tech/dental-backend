import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clinic, doctors, services, technology, protocols, portalSteps, screening, faqs } from "../content";
import * as photos from "../photos";
import logoSrc from "../logo";
import { Bar, Footer, DraftNote, waLink } from "../components/Chrome";
import TechArt from "../components/TechArt";
import ChatBot from "../components/ChatBot";
import { useMotion } from "../motion";

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

/* ── hero: a quick booking card (the clinic emblem sits behind it) ── */
function HeroBook() {
  return (
    <div className="hero-book">
      <img className="hb-mark" src={logoSrc} alt="" aria-hidden="true" />
      <div className="hb-card">
        <div className="hb-head">
          <img src={logoSrc} alt="" />
          <div><b>Book your visit</b><span>Mon – Sat, 11 am – 7 pm · by appointment</span></div>
        </div>
        <BookForm compact />
        <a className="hb-call" href={tel(clinic.phone)}><Icon n="phone" size={16} />Prefer to talk? Call {clinic.phone}</a>
      </div>
    </div>
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
const TECH_ITEMS = technology.flatMap((g) => g.items);
const TECH_ALIAS = {
  "Digital X-ray (RVG)": "Digital X-rays (RVG)", "Endo motor": "Endo motor and rotary files", "Cicada DT Fill": "Cicada DT Fill thermal obturator",
  "Runyes scanner": "Runyes 3DS V3 Pro intra-oral scanner", "Micro-blaster": "Aluminium-oxide micro-blaster", "Surgical guide": "Surgical guide for implants",
  "PRFuge": "PRFuge centrifuge (PRF)", "Ivoclean": "Ivoclean cleaning paste (Ivoclar)", "3-D printer": "ELEGOO Saturn 4 Ultra 16K 3-D printer",
};
const techFor = (tag) => TECH_ITEMS.find((t) => t.name === (TECH_ALIAS[tag] || tag));
/* treatments (protocol titles) that use a technology item */
const sameItem = (a, b) => !!a && !!b && (a === b || a.photo && a.photo === b.photo);   // e.g. RVG shown in two groups
const usedIn = (item) => protocols.filter((p) => (p.uses || []).some(([tag]) => sameItem(techFor(tag), item))).map((p) => p.title);

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
              {usedIn(t).length > 0 && (
                <div className="tc-used"><b>Used in</b>
                  {usedIn(t).map((title) => <button type="button" key={title} onClick={() => showProtocol(title)}>{title}</button>)}
                </div>
              )}
            </div>
          </article>
        ))}
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


/* ── oral cancer screening (DrOroscope) ── */
function Screening() {
  const s = screening;
  return (
    <>
      <div className="scr-top">
        <figure className="scr-photo"><img src={photos.oroscope} alt="DrOroscope hand-held oral screening camera" /></figure>
        <div>
          <span className="kicker">Early detection</span>
          <h2>{s.title}</h2>
          <p className="scr-lead">{s.lead}</p>
          <ul className="scr-tech">{s.tech.map((t) => <li key={t}><Icon n="spark" size={18} />{t}</li>)}</ul>
        </div>
      </div>
      <div className="scr-grid">
        <div className="scr-card">
          <h3>Who should be screened</h3>
          <ul className="scr-list">{s.who.map((t) => <li key={t}><Icon n="check" size={18} />{t}</li>)}</ul>
        </div>
        <div className="scr-card">
          <h3>How we use it</h3>
          <ol className="steps">{s.how.map((t) => <li key={t}><span>{t}</span></li>)}</ol>
        </div>
      </div>
      <div className="scr-benefits">
        {s.benefits.map(([t, d]) => <div key={t}><b>{t}</b><span>{d}</span></div>)}
      </div>
      <div className="scr-study">
        <h3>What the research shows</h3>
        <dl className="scr-stats">{s.study.stats.map(([n, l]) => <div key={l}><dt>{n}</dt><dd>{l}</dd></div>)}</dl>
        <p>{s.study.text}</p>
        <p className="scr-caution"><Icon n="shield" size={18} />{s.study.caution}</p>
        <p className="scr-src">Sources: {s.study.sources.map(([t, u], i) => <span key={u}>{i ? "; " : ""}<a href={u} target="_blank" rel="noreferrer">{t}</a></span>)}</p>
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
  const d0 = doctors[0];
  return (
    <>
      <div className="scroll-progress" aria-hidden="true" />
      <DraftNote />
      <Bar />
      <main id="top">
        {/* ── HERO ── */}
        <section className="hero">
          <div className="hero-glow" aria-hidden="true" />
          <div className="hero-orb o1" aria-hidden="true" /><div className="hero-orb o2" aria-hidden="true" />
          <div className="wrap hero-grid">
            <div className="hero-copy">
              <p className="hero-place"><Icon n="pin" size={16} />Chaitanyapuri, near Dilsukhnagar, Hyderabad</p>
              <h1>{clinic.name}</h1>
              <p className="motto">{clinic.motto}</p>
              {clinic.quote && (
                <figure className="hero-quote">
                  <blockquote>{clinic.quote}</blockquote>
                  {clinic.quoteBy && <figcaption>{clinic.quoteBy}</figcaption>}
                </figure>
              )}
              <p className="lead">{clinic.tagline}</p>
              <div className="hero-doc">
                <span className="ed-mono" aria-hidden="true">{d0.initials}</span>
                <span><b>{d0.name}</b></span>
              </div>
              <div className="hero-actions">
                <a className="btn light" href={tel(clinic.phone)}><Icon n="phone" size={18} />Call {clinic.phone}</a>
                <a className="btn outline-light" href="#treatments">See treatments <Icon n="arrow" size={18} /></a>
              </div>
            </div>
            <HeroBook />
          </div>
        </section>

        {/* ── TRUST STRIP ── */}
        <div className="wrap">
          <dl className="trust trust-2">
            <div><span className="tr-ico"><Icon n="award" /></span><dt>25 years</dt><dd>of dental practice</dd></div>
            <div><span className="tr-ico"><Icon n="tooth" /></span><dt>MDS</dt><dd>Oral Medicine &amp; Radiology</dd></div>
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
          </div>
        </section>

        {/* ── ORAL CANCER SCREENING ── */}
        <section className="sec" id="screening">
          <div className="wrap"><Screening /></div>
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
          <div className="wrap portal-grid">
            <div>
              <span className="kicker light">Patient portal</span>
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

        {/* ── BOOK ── */}
        <section className="sec" id="book">
          <div className="wrap book-grid">
            <div>
              <span className="kicker">Appointments</span>
              <h2>Book an appointment</h2>
              <p className="book-lead">Tell us when suits you and what you need. The clinic will confirm a time on WhatsApp.</p>
              <ul className="book-points">
                <li><Icon n="clock" size={18} />Monday to Saturday, 11 am – 7 pm, by appointment</li>
                <li><Icon n="phone" size={18} />Prefer to talk? Call <a href={tel(clinic.phone)}>{clinic.phone}</a></li>
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
          </div>
        </section>
      </main>
      <Footer />
      <nav className="mobile-bar" aria-label="Contact the clinic">
        <a href={tel(clinic.phone)}><Icon n="phone" size={20} />Call</a>
        <a href={waLink()} target="_blank" rel="noreferrer"><Icon n="chat" size={20} />WhatsApp</a>
        <a href="#book"><Icon n="clock" size={20} />Book</a>
        <button type="button" className="ask" onClick={() => window.dispatchEvent(new Event("open-chat"))}><Icon n="chat" size={20} />Ask us</button>
      </nav>
      <a className={`wa-float${scrolled ? " show" : ""}`} href={waLink()} target="_blank" rel="noreferrer" aria-label="Book an appointment on WhatsApp">
        <Icon n="chat" size={24} /><span>Book on WhatsApp</span>
      </a>
      <ChatBot />
    </>
  );
}