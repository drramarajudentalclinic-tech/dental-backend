/* Website chat assistant — clinic timings, appointments, directions and
   after-treatment care, in English, Telugu and Hindi.
   • Topic buttons always work (answers come from ../chatContent.js).
   • Typed questions go to the clinic server's AI (/api/chatbot) when it is
     switched on; otherwise they are matched to the nearest topic. */
import { useEffect, useRef, useState } from "react";
import { clinic } from "../content";
import { waLink } from "./Chrome";
import { LANGS, UI, TOPICS, matchTopic } from "../chatContent";

const BASE = (import.meta.env.VITE_API_URL || "https://dental-backend-xojn.onrender.com/api").replace(/\/+$/, "");
const PHONE = "+919908894449";
const LKEY = "ssd_chat_lang";

function savedLang() {
  try { const l = localStorage.getItem(LKEY); return UI[l] ? l : "en"; } catch { return "en"; }
}

/* make links and phone numbers clickable */
function Rich({ text }) {
  const parts = String(text).split(/(https?:\/\/[^\s]+|\+91[\s-]?\d{5}[\s-]?\d{5}|\b108\b)/g);
  return parts.map((p, i) => {
    if (/^https?:\/\//.test(p)) return <a key={i} href={p} target="_blank" rel="noreferrer">{p.replace(/^https?:\/\//, "")}</a>;
    if (/^\+91/.test(p)) return <a key={i} href={`tel:${p.replace(/[\s-]/g, "")}`}>{p}</a>;
    if (p === "108") return <a key={i} href="tel:108">108</a>;
    return p;
  });
}

function Lines({ lines }) {
  const out = [];
  let list = [];
  const flush = () => { if (list.length) { out.push(<ul key={`u${out.length}`}>{list}</ul>); list = []; } };
  lines.forEach((l, i) => {
    const t = l.trim();
    if (!t) return;
    const m = t.match(/^[•\-*]\s+(.*)$/);
    if (m) list.push(<li key={i}><Rich text={m[1]} /></li>);
    else { flush(); out.push(<p key={i}><Rich text={t} /></p>); }
  });
  flush();
  return out;
}

const Ico = {
  chat: <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" /><path d="M8.5 11h.01M12 11h.01M15.5 11h.01" strokeWidth="2.6" /></svg>,
  close: <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>,
  send: <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 12l16-8-6 16-2.5-6.5L4 12z" /></svg>,
  phone: <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z" /></svg>,
};

export default function ChatBot() {
  const [open, setOpen] = useState(false);
  const [lang, setLangState] = useState(savedLang);
  const [view, setView] = useState("main");          // main | care
  const [msgs, setMsgs] = useState([{ from: "bot", hello: true }]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [ai, setAi] = useState(null);                 // null = not checked yet
  const scroller = useRef(null);
  const input = useRef(null);
  const ui = UI[lang];

  const setLang = (l) => { setLangState(l); try { localStorage.setItem(LKEY, l); } catch { /* private mode */ } };

  // open from other buttons on the page:  window.dispatchEvent(new Event("open-chat"))
  useEffect(() => {
    const h = () => setOpen(true);
    window.addEventListener("open-chat", h);
    return () => window.removeEventListener("open-chat", h);
  }, []);

  useEffect(() => {
    if (!open || ai !== null) return;
    fetch(`${BASE}/chatbot/status`).then((r) => (r.ok ? r.json() : { ai: false })).then((j) => setAi(!!j.ai)).catch(() => setAi(false));
  }, [open, ai]);

  useEffect(() => {
    if (!open) return;
    const k = (e) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [open]);

  useEffect(() => { if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight; }, [msgs, busy, open, view]);

  const add = (...m) => setMsgs((prev) => [...prev, ...m]);

  const topicMsg = (t, l = lang) => ({ from: "bot", lang: l, topic: t.id, lines: t.a[l], note: t.group === "care" || t.urgent, action: t.action });

  const pick = (t) => {
    add({ from: "me", lines: [t.title[lang]] }, topicMsg(t));
  };

  // text of the conversation for the AI (last 10 messages)
  const history = (list) => list
    .filter((m) => !m.hello && !m.error && m.lines?.length)
    .map((m) => ({ role: m.from === "me" ? "user" : "assistant", content: m.lines.join("\n") }))
    .slice(-10);

  const offline = (q) => {
    const t = matchTopic(q);
    return t ? topicMsg(t) : { from: "bot", lines: [ui.notFound], error: true };
  };

  const ask = async (e) => {
    e?.preventDefault();
    const q = text.trim();
    if (!q || busy) return;
    setText("");
    const mine = { from: "me", lines: [q] };
    const next = [...msgs, mine];
    setMsgs(next);
    if (!ai) { add(offline(q)); return; }
    setBusy(true);
    try {
      const r = await fetch(`${BASE}/chatbot`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history(next), lang }),
      });
      const j = await r.json().catch(() => ({}));
      if (r.ok && j.reply) add({ from: "bot", lines: String(j.reply).split("\n"), note: true, ai: true });
      else if (r.status === 429) add({ from: "bot", lines: [j.error || ui.notFound], error: true });
      else {
        if (j.code === "NOT_CONFIGURED") setAi(false);
        add(offline(q));
      }
    } catch {
      add(offline(q));
    } finally {
      setBusy(false);
      input.current?.focus();
    }
  };

  const goBook = () => {
    setOpen(false);
    document.getElementById("book")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const chips = view === "main" ? TOPICS.filter((t) => t.group === "clinic") : TOPICS.filter((t) => t.group === "care");

  return (
    <>
      <button type="button" className={`chat-launch${open ? " is-open" : ""}`} onClick={() => setOpen((o) => !o)}
        aria-expanded={open} aria-controls="clinic-chat" aria-label={open ? ui.close : ui.open}>
        {open ? Ico.close : Ico.chat}
        {!open && <span className="chat-launch-txt">{ui.open}</span>}
      </button>

      {open && (
        <section id="clinic-chat" className="chat" role="dialog" aria-label={ui.title}>
          <header className="chat-head">
            <div className="chat-av" aria-hidden="true">{Ico.chat}</div>
            <div className="chat-ttl">
              <b>{ui.title}</b>
              <small>{ui.sub}</small>
            </div>
            <button type="button" className="chat-x" onClick={() => setOpen(false)} aria-label={ui.close}>{Ico.close}</button>
          </header>
          <div className="chat-langs" role="group" aria-label="Language">
            {LANGS.map(([k, label]) => (
              <button key={k} type="button" className={lang === k ? "on" : ""} aria-pressed={lang === k} onClick={() => setLang(k)} lang={k}>{label}</button>
            ))}
          </div>

          <div className="chat-body" ref={scroller} aria-live="polite">
            {msgs.map((m, i) => {
              if (m.hello) return (
                <div key={i} className="cm bot"><p>{ui.hello}</p>{ai === false && <p className="cm-hint">{ui.aiOff}</p>}</div>
              );
              const L = UI[m.lang || lang];
              return (
                <div key={i} className={`cm ${m.from}${m.error ? " err" : ""}`} lang={m.from === "bot" ? (m.lang || undefined) : undefined}>
                  <Lines lines={m.lines} />
                  {m.action === "book" && <button type="button" className="cm-act" onClick={goBook}>{L.bookForm} →</button>}
                  {m.action === "map" && <a className="cm-act" href={clinic.mapsLink} target="_blank" rel="noreferrer">{L.maps} →</a>}
                  {m.note && <p className="cm-note">{L.note}</p>}
                </div>
              );
            })}
            {busy && <div className="cm bot typing" aria-label={ui.thinking}><span /><span /><span /></div>}
          </div>

          <div className="chat-chips">
            {view === "care" && <button type="button" className="chip back" onClick={() => setView("main")}>{ui.back}</button>}
            {view === "care" && <span className="chip-q">{ui.pickTreatment}</span>}
            {chips.map((t) => (
              <button key={t.id} type="button" className={`chip${t.urgent ? " urgent" : ""}`} onClick={() => pick(t)}>{t.title[lang]}</button>
            ))}
            {view === "main" && <button type="button" className="chip care" onClick={() => setView("care")}>{ui.aftercare} →</button>}
          </div>

          <form className="chat-form" onSubmit={ask}>
            <input ref={input} value={text} onChange={(e) => setText(e.target.value)} placeholder={ui.placeholder} maxLength={600}
              aria-label={ui.placeholder} enterKeyHint="send" />
            <button type="submit" disabled={!text.trim() || busy} aria-label={ui.send}>{Ico.send}</button>
          </form>
          <div className="chat-foot">
            <a href={`tel:${PHONE}`}>{Ico.phone}{ui.call} {clinic.phone}</a>
            <a href={waLink()} target="_blank" rel="noreferrer" className="wa">{ui.whatsapp}</a>
          </div>
        </section>
      )}
    </>
  );
}