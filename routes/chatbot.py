"""
Website chat assistant for Sri Satya Sai Oral Health Center & Dental Clinic.

POST /api/chatbot   {"messages": [{"role": "user"|"assistant", "content": "..."}], "lang": "en"|"te"|"hi"}
  -> {"reply": "...", "provider": "anthropic"|"gemini"}
  -> 503 {"error": ..., "code": "NOT_CONFIGURED"} when no AI key is set
     (the website then answers from its built-in topics instead)

Answers clinic questions (timings, appointments, location) and post-treatment
care, using ONLY the clinic's own instruction sheets below. It does not
diagnose or prescribe, and sends emergencies to the clinic / 108.
No login needed. Messages are not stored.

SETTINGS (Render → dental-backend → Environment). Keys go only in Render.
  CHATBOT_PROVIDER   anthropic | gemini | off   (default off)
  ANTHROPIC_API_KEY  for anthropic
  GEMINI_API_KEY     for gemini
  CHATBOT_MODEL      optional; defaults: claude-haiku-4-5-20251001 / gemini-2.5-flash
  CHATBOT_DAILY_LIMIT  total questions per day for the whole site (default 400)
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque

from flask import Blueprint, jsonify, request

chatbot_bp = Blueprint("chatbot", __name__)

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


CLINIC_FACTS = """
CLINIC: Sri Satya Sai Oral Health Center & Dental Clinic (Sri Satya Sai Oral Health Centre).
DOCTOR: Dr. D. Rama Raju, BDS, MDS (Oral Medicine & Radiology), Dental Council Reg. No. A-1096, 25 years of experience. BDS and MDS from Osmania Medical College, Hyderabad. Member, Indian Dental Association.
ADDRESS: G-15, Ground Floor, Rajanigandha Apartments, Opposite Metro Pillar No. 1563, Chaitanyapuri, Hyderabad – 500060, Telangana (near Dilsukhnagar).
GOOGLE MAPS: https://maps.app.goo.gl/F8Zp631MJP9MvKtk7
TIMINGS: Monday to Saturday, 11:00 am – 7:00 pm. Sunday holiday. BY APPOINTMENT ONLY.
APPOINTMENTS / CONTACT: Call or WhatsApp +91 99088 94449. Also +91 99490 94449. Email drramarajudentalclinic@gmail.com. The website has a "Book an appointment" form that sends a WhatsApp request.
FEES: Depend on the treatment; the doctor explains the options and the cost before starting. Do not quote prices.
TREATMENTS: check-ups and cleaning (oral prophylaxis), composite and GIC fillings, root canal treatment, crowns and bridges, dental implants with surgical guides (Straumann, Nobel Biocare, Osstem, DIO, Neo Biotech, Noris, Adin, Alpha-Bio), complete and partial dentures, veneers and laminates, braces and clear aligners, extractions and wisdom tooth removal, gum treatment (curettage, flap surgery, laser flap surgery), low-level laser therapy, bone grafts and PRF, oral lesions and oral cancer screening (DrOroscope, only where needed), children's dentistry, TMJ/bite problems, emergencies.
PATIENT PORTAL: patients can see records the doctor shares (visit summaries, prescriptions, X-rays, receipts) at the website's "Patient login" using their registered mobile number and an SMS code.
"""

RULES = """
You are the website assistant of the clinic above. Follow these rules strictly:
1. Answer ONLY questions about this clinic (timings, appointments, location, contact, treatments offered, what to expect) and post-treatment care / instructions. Use ONLY the facts and the clinic's instruction sheets given here. If the answer is not here, say you are not sure and ask them to call or WhatsApp +91 99088 94449. Never invent prices, timings, doctors or services.
2. Reply in the SAME language and script the patient writes in: Telugu (తెలుగు script), Hindi (देवनागरी), or English. If they write Telugu or Hindi in English letters, reply the same way. If a preferred language is given, use it when the message language is unclear.
3. Be short, warm and clear: 2–8 short lines or bullet points. Use simple words a patient understands.
4. You are not a doctor. Do not diagnose, do not name or suggest specific medicines or doses — say "take the medicines prescribed by the doctor". For any new or worrying symptom, advise calling the clinic.
5. EMERGENCY: if the patient mentions difficulty breathing or swallowing, swelling spreading to the eye or neck, heavy bleeding that does not stop with pressure, high fever, or a serious injury, tell them first to call the clinic immediately at +91 99088 94449 and, if severe or after hours, go to the nearest hospital emergency or call 108.
6. To book an appointment, give the phone/WhatsApp number and mention the booking form on the website. You cannot book or confirm a time yourself.
7. Do not ask for or repeat personal medical details beyond what is needed. Do not discuss other clinics or unrelated topics; politely bring the conversation back.
8. Plain text only (no markdown headings, no tables). Bullets with "•" are fine.
"""


def _system_text():
    return (RULES + "\n\n=== CLINIC FACTS ===\n" + CLINIC_FACTS +
            "\n\n=== CLINIC POST-TREATMENT INSTRUCTION SHEETS ===\n" + _read("chatbot_kb_docs.txt") +
            "\n\n=== ADDITIONAL AFTER-CARE (advanced treatments) ===\n" + _read("chatbot_kb_extra.txt"))


# ── limits (per server process) ─────────────────────────────────────────────
_lock = threading.Lock()
_ip_hits = {}                 # ip -> deque[timestamps]
_day = {"date": None, "count": 0}
MAX_MSG_CHARS, MAX_TURNS = 600, 10


def _ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else (request.remote_addr or ""))[:64]


def _allow():
    now = time.time()
    today = time.strftime("%Y-%m-%d")
    limit = int(os.environ.get("CHATBOT_DAILY_LIMIT") or 400)
    with _lock:
        if _day["date"] != today:
            _day["date"], _day["count"] = today, 0
            _ip_hits.clear()
        if _day["count"] >= limit:
            return "The assistant is resting for today. Please call or WhatsApp +91 99088 94449."
        q = _ip_hits.setdefault(_ip(), deque())
        while q and now - q[0] > 3600:
            q.popleft()
        if len([t for t in q if now - t < 60]) >= 6 or len(q) >= 40:
            return "Too many questions in a short time. Please wait a little, or call +91 99088 94449."
        q.append(now)
        _day["count"] += 1
    return None


# ── providers ───────────────────────────────────────────────────────────────
def _post_json(url, body, headers, timeout=25):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _anthropic(system, msgs):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    model = os.environ.get("CHATBOT_MODEL") or "claude-haiku-4-5-20251001"
    data = _post_json("https://api.anthropic.com/v1/messages", {
        "model": model, "max_tokens": 700, "temperature": 0.2,
        # the long instruction text is cached, so repeated questions cost much less
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": m["role"], "content": m["content"]} for m in msgs],
    }, {"x-api-key": key, "anthropic-version": "2023-06-01"})
    return "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text").strip()


def _gemini(system, msgs):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    model = os.environ.get("CHATBOT_MODEL") or "gemini-2.5-flash"
    data = _post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in msgs],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
    }, {"x-goog-api-key": key})
    parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(p.get("text", "") for p in parts).strip()


PROVIDERS = {"anthropic": _anthropic, "gemini": _gemini}


def provider_name():
    p = (os.environ.get("CHATBOT_PROVIDER") or "off").strip().lower()
    return p if p in PROVIDERS else "off"


@chatbot_bp.route("/chatbot/status", methods=["GET"])
def chatbot_status():
    return jsonify({"ai": provider_name() != "off"})


@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    prov = provider_name()
    if prov == "off":
        return jsonify({"error": "The AI assistant is not switched on.", "code": "NOT_CONFIGURED"}), 503
    data = request.get_json(silent=True) or {}
    raw = data.get("messages") or []
    msgs = []
    for m in raw[-MAX_TURNS:]:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            continue
        text = str(m.get("content") or "").strip()[:MAX_MSG_CHARS]
        if text:
            msgs.append({"role": m["role"], "content": text})
    while msgs and msgs[0]["role"] != "user":          # must start with the patient
        msgs.pop(0)
    if not msgs or msgs[-1]["role"] != "user":
        return jsonify({"error": "Please type a question."}), 400
    blocked = _allow()
    if blocked:
        return jsonify({"error": blocked, "code": "LIMIT"}), 429
    lang = {"te": "Telugu", "hi": "Hindi", "en": "English"}.get(str(data.get("lang") or ""), "")
    system = _system_text() + (f"\n\nPreferred language selected on the website: {lang}." if lang else "")
    try:
        reply = PROVIDERS[prov](system, msgs)
    except urllib.error.HTTPError as e:
        print("[chatbot] provider error:", e.code, e.read(300).decode("utf-8", "replace"))
        reply = None
    except Exception as e:
        print("[chatbot] provider error:", type(e).__name__, str(e)[:200])
        reply = None
    if not reply:
        return jsonify({"error": "The assistant could not answer just now. Please call or WhatsApp +91 99088 94449.",
                        "code": "UNAVAILABLE"}), 502
    return jsonify({"reply": reply[:4000], "provider": prov})