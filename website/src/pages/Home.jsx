import { useState } from "react";
import { Link } from "react-router-dom";
import { clinic, doctors, services, technology, protocols, portalSteps } from "../content";
import { Bar, Footer, DraftNote, waLink } from "../components/Chrome";
import TechArt from "../components/TechArt";

const UPPER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
const LOWER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];
const TREATED = new Set([16, 46, 26]);
const ACTIVE = new Set([36]);

function ToothChart() {
  const tooth = (n, i) => (
    <div key={n} className={`tooth${ACTIVE.has(n) ? " mark" : TREATED.has(n) ? " done" : ""}`}
      style={{ animationDelay: `${i * 22}ms` }} aria-hidden="true">{n}</div>
  );
  return (
    <figure className="chart" aria-label="Dental chart with the 32 adult teeth numbered">
      <div className="chart-cap"><span>Right</span><span>Upper</span><span>Left</span></div>
      <div className="arch">{UPPER.map(tooth)}</div>
      <div className="mid" />
      <div className="arch">{LOWER.map((n, i) => tooth(n, i + 16))}</div>
      <div className="chart-cap" style={{ marginTop: 8, marginBottom: 0 }}><span /><span>Lower</span><span /></div>
      <div className="legend">
        <span><i style={{ background: "var(--mint)", borderColor: "#9fcbbf" }} />Treated</span>
        <span><i style={{ background: "var(--gum-soft)", borderColor: "var(--gum)" }} />Under treatment</span>
        <span><i style={{ background: "var(--enamel)", borderColor: "var(--line)" }} />Healthy</span>
      </div>
      <figcaption className="chart-note">
        Each finding, X-ray and treatment is recorded against the tooth it belongs to. Tooth 36 here — lower left first molar —
        would show its root canal X-rays, prescription and next visit in one place.
      </figcaption>
    </figure>
  );
}

function Protocols() {
  const [i, setI] = useState(0);
  const p = protocols[i];
  return (
    <div className="proto">
      <div className="proto-tabs" role="tablist" aria-label="Protocols">
        {protocols.map((x, k) => (
          <button key={x.title} role="tab" id={`pt-${k}`} aria-selected={k === i} aria-controls="pt-panel" onClick={() => setI(k)}>{x.title}</button>
        ))}
      </div>
      <div role="tabpanel" id="pt-panel" aria-labelledby={`pt-${i}`}>
        <h3 style={{ marginBottom: 6 }}>{p.title}</h3>
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
        <h2 className="doc-name">{d.name}</h2>
        <div className="doc-q">{d.qualification}</div>
        <div className="doc-title">{d.title}</div>
        <dl className="doc-stats">
          {d.stats.map(([big, small]) => <div key={small}><dt>{big}</dt><dd>{small}</dd></div>)}
        </dl>
        <div className="doc-actions">
          <a className="btn" href={`tel:${clinic.phone.replace(/[^\d+]/g, "")}`}>Call for an appointment</a>
          <a className="btn ghost" href={waLink(`Hello, I would like an appointment with ${d.name}.`)} target="_blank" rel="noreferrer">WhatsApp</a>
        </div>
      </aside>
      <div className="doc-body">
        <h2>About the doctor</h2>
        {d.about.map((p) => <p key={p.slice(0, 20)} className="measure">{p}</p>)}
        <h3>Areas of care</h3>
        <ul className="doc-focus">{d.focus.map((f) => <li key={f}>{f}</li>)}</ul>
        <h3>Education and practice</h3>
        <ol className="doc-time">
          {d.timeline.map(([y, t, w]) => <li key={y}><span className="yr">{y}</span><span><b>{t}</b><br /><span className="muted">{w}</span></span></li>)}
        </ol>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <>
      <DraftNote />
      <Bar />
      <main id="top">
        <section className="hero">
          <div className="wrap hero-grid">
            <div>
              <h1>{clinic.name}</h1>
              <p className="motto">{clinic.motto}</p>
              <p className="lead">{clinic.tagline}</p>
              <div className="hero-actions">
                <a className="btn" href={`tel:${clinic.phone.replace(/[^\d+]/g, "")}`}>Call {clinic.phone}</a>
                <a className="btn ghost" href={waLink()} target="_blank" rel="noreferrer">Book on WhatsApp</a>
              </div>
              <dl className="hero-facts">
                <div><dt>30 years</dt><dd>in practice</dd></div>
                <div><dt>MDS</dt><dd>Oral Medicine &amp; Radiology</dd></div>
                <div><dt>Mon – Sat</dt><dd>11 am – 7 pm, by appointment</dd></div>
              </dl>
            </div>
            <ToothChart />
          </div>
        </section>

        <section className="sec alt" id="treatments">
          <div className="wrap">
            <div className="sec-head measure">
              <h2>Treatments</h2>
              <p className="muted">What we do at the clinic. The doctor explains the options and the cost before any treatment starts.</p>
            </div>
            <dl className="services">
              {services.map(([t, d]) => <div key={t}><dt>{t}</dt><dd>{d}</dd></div>)}
            </dl>
          </div>
        </section>

        <section className="sec" id="technology">
          <div className="wrap">
            <div className="sec-head measure">
              <h2>Technology we use every day</h2>
              <p className="muted">Equipment is only useful if it changes something for the patient. Here is what each one is, and what it changes for you.</p>
            </div>
            <nav className="tech-jump" aria-label="Technology by treatment">
              {technology.map((g, i) => <a key={g.treatment} href={`#tech-${i}`}>{g.treatment}</a>)}
            </nav>
            {technology.map((g, i) => (
              <div className="tech-group" key={g.treatment} id={`tech-${i}`}>
                <h3 className="tech-gh">{g.treatment}</h3>
                <div className="tech">
                  {g.items.map((t) => (
                    <div className="tech-row with-art" key={t.name}>
                      <div className="art-box"><TechArt name={t.art} photo={t.photo} label={t.name} /></div>
                      <div><h4>{t.name}</h4><p className="muted" style={{ marginTop: 4 }}>{t.what}</p></div>
                      <p className="why">{t.why}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="sec alt" id="protocols">
          <div className="wrap">
            <div className="sec-head measure">
              <h2>How we work</h2>
              <p className="muted">The steps we follow, every time: from sterilising instruments to a root canal, a crown and a guided implant.</p>
            </div>
            <Protocols />
          </div>
        </section>

        <section className="sec doctor-sec" id="doctors">
          <div className="wrap">
            {doctors.map((d) => <Doctor key={d.name} d={d} />)}
          </div>
        </section>

        <section className="sec portal-band" id="portal">
          <div className="wrap">
            <div className="measure">
              <h2>Your dental records, online</h2>
              <p style={{ marginTop: 10 }}>Visit summaries, prescriptions, X-rays, scans and receipts — available on your phone when the doctor shares them with you.</p>
            </div>
            <ol className="portal-steps">
              {portalSteps.map(([t, d]) => <li key={t}><b>{t}</b>{d}</li>)}
            </ol>
            <Link className="btn" to="/portal">Log in to the patient portal</Link>
          </div>
        </section>

        <section className="sec" id="visit">
          <div className="wrap">
            <div className="sec-head"><h2>Visit us</h2></div>
            <div className="visit">
              <div>
                <h3>Address</h3>
                <p>{clinic.name}<br />{clinic.address.map((l) => <span key={l}>{l}<br /></span>)}</p>
                {clinic.landmark && <p className="muted" style={{ marginTop: 6, fontSize: 15 }}>{clinic.landmark}</p>}
                {clinic.mapsLink && <p style={{ marginTop: 10 }}><a className="btn ghost small" href={clinic.mapsLink} target="_blank" rel="noreferrer">Directions in Google Maps</a></p>}
              </div>
              <div>
                <h3>Timings</h3>
                <table className="hours"><tbody>{clinic.hours.map(([d, h]) => <tr key={d}><td>{d}</td><td>{h}</td></tr>)}</tbody></table>
                {clinic.hoursNote && <p className="appt-note">{clinic.hoursNote}</p>}
              </div>
              <div>
                <h3>Contact</h3>
                <p>Phone: <a href={`tel:${clinic.phone.replace(/[^\d+]/g, "")}`}>{clinic.phone}</a></p>
                <p>WhatsApp: <a href={`https://wa.me/${clinic.whatsapp.replace(/\D/g, "")}`} target="_blank" rel="noreferrer">{clinic.whatsapp}</a></p>
                <p>Email: <a href={`mailto:${clinic.email}`}>{clinic.email}</a></p>
              </div>
            </div>
            {clinic.mapQuery && (
              <iframe className="map" title="Clinic location on the map" loading="lazy" referrerPolicy="no-referrer-when-downgrade"
                src={`https://maps.google.com/maps?q=${encodeURIComponent(clinic.mapQuery)}&ll=${clinic.mapCenter}&z=17&output=embed`} />
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}