import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { portal, getSession, setSession } from "../api";
import { Bar, Footer } from "../components/Chrome";

const digits = (s) => String(s || "").replace(/\D/g, "");
const RESEND_SECONDS = 30;

export default function PortalLogin() {
  const nav = useNavigate();
  const [session, setS] = useState(getSession());
  const [step, setStep] = useState(session ? "profiles" : "mobile");
  const [mobile, setMobile] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [info, setInfo] = useState("");
  const [wait, setWait] = useState(0);
  const codeRef = useRef(null);

  useEffect(() => { document.title = "Patient login — Sri Satya Sai Dental"; }, []);
  useEffect(() => {
    if (wait <= 0) return undefined;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);
  // refresh the profile list (new-item counts) when coming back to this page
  useEffect(() => {
    if (step !== "profiles" || !session) return;
    portal.me().then((r) => { const s = { ...session, profiles: r.profiles }; setSession(s); setS(s); }).catch((e) => {
      if (e.status === 401) { setS(null); setStep("mobile"); }
    });
  }, [step]); // eslint-disable-line react-hooks/exhaustive-deps

  const m10 = digits(mobile).replace(/^91(?=\d{10}$)/, "").replace(/^0(?=\d{10}$)/, "");
  const mobileOk = /^[6-9]\d{9}$/.test(m10);

  const sendCode = async (e) => {
    e?.preventDefault();
    if (!mobileOk) { setErr("Enter your 10-digit mobile number — the one registered at the clinic."); return; }
    setBusy(true); setErr(""); setInfo("");
    try {
      const r = await portal.requestCode(m10);
      setInfo(r.message || "If this number is registered for the portal, a 6-digit code has been sent by SMS.");
      setStep("code"); setCode(""); setWait(RESEND_SECONDS);
      setTimeout(() => codeRef.current?.focus(), 50);
    } catch (x) { setErr(x.message); }
    finally { setBusy(false); }
  };

  const verify = async (e) => {
    e?.preventDefault();
    if (digits(code).length !== 6) { setErr("Enter the 6-digit code from the SMS."); return; }
    setBusy(true); setErr("");
    try {
      const r = await portal.verifyCode(m10, digits(code));
      const s = { token: r.token, mobile: r.mobile, profiles: r.profiles, at: Date.now() };
      setSession(s); setS(s);
      if (r.profiles.length === 1) nav(`/portal/record/${r.profiles[0].patient_id}`, { replace: true });
      else setStep("profiles");
    } catch (x) { setErr(x.message); }
    finally { setBusy(false); }
  };

  const logout = () => { setSession(null); setS(null); setStep("mobile"); setMobile(""); setCode(""); setInfo(""); setErr(""); };

  return (
    <div className="p-shell">
      <Bar right={session ? <button type="button" className="btn ghost small" onClick={logout}>Log out</button> : null} />
      <main className="p-main">
        <div className="wrap">
          <div className="p-card login">
            {step === "mobile" && (
              <form onSubmit={sendCode} noValidate>
                <h1>Patient login</h1>
                <p className="muted">See the visit summaries, prescriptions, X-rays and receipts your doctor has shared with you.</p>
                <div className="field">
                  <label htmlFor="mobile">Mobile number registered at the clinic</label>
                  <div className="prefix">
                    <span>+91</span>
                    <input id="mobile" type="tel" inputMode="numeric" autoComplete="tel-national" maxLength={14}
                      value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="98765 43210" autoFocus />
                  </div>
                </div>
                {err && <div className="msg err" role="alert">{err}</div>}
                <button className="btn" style={{ width: "100%" }} disabled={busy}>{busy ? "Sending…" : "Send code"}</button>
                <p className="muted" style={{ fontSize: 14.5, marginTop: 16 }}>
                  The portal is switched on by the doctor at your visit. If you don't receive a code, ask at the reception desk.
                </p>
              </form>
            )}

            {step === "code" && (
              <form onSubmit={verify} noValidate>
                <h1>Enter the code</h1>
                {info && <div className="msg ok" role="status" style={{ marginTop: 12 }}>{info} Sent to +91 {m10.slice(0, 2)}••••••{m10.slice(-2)}.</div>}
                <div className="field">
                  <label htmlFor="otp">6-digit code</label>
                  <input id="otp" ref={codeRef} className="otp-input" type="text" inputMode="numeric" autoComplete="one-time-code"
                    maxLength={6} value={code} onChange={(e) => setCode(digits(e.target.value).slice(0, 6))} placeholder="••••••" />
                </div>
                {err && <div className="msg err" role="alert">{err}</div>}
                <button className="btn" style={{ width: "100%" }} disabled={busy}>{busy ? "Checking…" : "Log in"}</button>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, gap: 10, flexWrap: "wrap" }}>
                  <button type="button" className="linkbtn" onClick={() => { setStep("mobile"); setErr(""); }}>Change number</button>
                  <button type="button" className="linkbtn" disabled={wait > 0 || busy} onClick={sendCode}>
                    {wait > 0 ? `Send a new code in ${wait}s` : "Send a new code"}
                  </button>
                </div>
              </form>
            )}

            {step === "profiles" && session && (
              <div>
                <h1>Whose record?</h1>
                <p className="muted">These family members use {session.mobile ? `the number ${session.mobile}` : "this number"} at the clinic.</p>
                <div className="profiles">
                  {(session.profiles || []).map((p) => (
                    <button key={p.patient_id} type="button" className="profile" onClick={() => nav(`/portal/record/${p.patient_id}`)}>
                      <span>
                        <b style={{ color: "var(--ink)", fontSize: 18 }}>{p.name}</b>
                        <span className="muted" style={{ display: "block", fontSize: 14.5 }}>
                          Case no. {p.case_number}{p.age ? `, ${p.age} yrs` : ""}
                        </span>
                      </span>
                      {p.new_items > 0 && <span className="badge">{p.new_items} new</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
