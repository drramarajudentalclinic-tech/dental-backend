"""
Voice to Chart — the AI "tidy-up" for the clinic app.

The app already turns speech into chart entries in the browser (fast and
free). When a sentence is difficult — mixed Telugu / Hindi, unusual words,
many teeth at once — the doctor presses "AI tidy-up" and the text (and, if
allowed, the short voice recording) comes here. The AI returns the same kind
of entries; the doctor still checks every entry before anything is saved.
Nothing is stored here: no text, no recording.

    GET  /api/voice/status      -> {"ai": "gemini"|"anthropic"|"off", "audio": true|false}
    POST /api/voice/normalize   {"mode": "chart"|"perio"|"both"|"treatment"|"advice"|"rx",
                                 "text": "...", "lang": "en-IN", "audio": "<base64 WAV>",
                                 "mime": "audio/wav", "catalogue": ["Amoxicillin 500mg", ...]}
                             -> {"items": [...], "problems": [...], "transcript": "...", "provider": "..."}

SETTINGS (Render → dental-backend → Environment). Keys go ONLY in Render.
  VOICE_AI            auto | gemini | anthropic | off      (default auto:
                      Gemini if GEMINI_API_KEY is set, else Anthropic if
                      ANTHROPIC_API_KEY is set, else off)
  GEMINI_API_KEY      needed to listen to recordings (Gemini understands audio)
  ANTHROPIC_API_KEY   text only
  VOICE_MODEL         optional; defaults: gemini-2.5-flash / claude-haiku-4-5-20251001
  VOICE_DAILY_LIMIT   AI tidy-ups per day for the whole clinic (default 300)
"""
import base64
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request

from flask import Blueprint, jsonify, request

try:
    from auth_utils import require_login
except ImportError:
    try:
        from routes.auth_utils import require_login
    except ImportError:                                   # pragma: no cover
        def require_login(fn):
            return fn

voice_bp = Blueprint("voice", __name__)

# ── what the app accepts (must match the app's lists) ───────────────────────
CONDITIONS = [
    "Abscess", "Attrition", "Bridge", "Calculus", "Caries", "Cervical Abrasion", "Crown",
    "Deep Caries", "Erosion", "Faulty Restoration", "Fluorosis", "Food Impaction", "Fracture",
    "Furcation", "Gingivitis", "Gum Recession", "Hypoplasia", "Impacted", "Implant", "Malposed",
    "Missing", "Mobility I", "Mobility II", "Mobility III", "Occlusal Pits", "Partially Erupted",
    "Periapical Pathology", "Pockets", "Proximal Caries", "Pulpitis", "RC Treated", "Restored",
    "Retained Deciduous", "Root Caries", "Root Stump", "Secondary Caries", "Sensitive Tooth",
    "Stains", "Supernumerary", "Veneer", "Other",
]
TREATMENTS = [
    "A/O Done", "BMP / Cleaning & Shaping Done", "Obturation Done", "Re-RCT Done", "Implant Done",
    "Extraction", "Surgical Extraction", "Composite Restoration", "GIC Restoration",
    "Permanent Cementation", "Temporary Cementation", "Temporary Restoration", "Pulpectomy",
    "Space Maintainer", "Other",
]
ADVICE = [
    "Rct & Crown", "Re-Rct", "Zirconia Crown", "Dmls Crown", "Bridge", "Implant", "Ortho Extraction",
    "Surgical Extraction", "Composite Restoration", "Gic Restoration", "Permanent Cementation",
    "Temporary Cementation", "Temporary Restoration", "Pulpectomy", "Space Maintainer", "Extraction", "Other",
]
FREQUENCIES = ["1 time/day", "2 times/day", "3 times/day", "4 times/day", "At night", "When needed (SOS)"]
WHENS = ["After food", "Before food", "With food", "At bedtime"]
SEVERITIES = ["mild", "moderate", "severe", "critical"]
TEETH = {q * 10 + p for q in (1, 2, 3, 4) for p in range(1, 9)} | {q * 10 + p for q in (5, 6, 7, 8) for p in range(1, 6)}
MODES = ("chart", "perio", "both", "treatment", "advice", "rx")
MAX_AUDIO_BYTES = 6 * 1024 * 1024
AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/wave", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/flac", "audio/aac", "audio/webm"}


# ── which AI ────────────────────────────────────────────────────────────────
def _keys():
    return (os.environ.get("GEMINI_API_KEY", "").strip(), os.environ.get("ANTHROPIC_API_KEY", "").strip())


def provider():
    choice = (os.environ.get("VOICE_AI") or "auto").strip().lower()
    gem, ant = _keys()
    if choice == "off":
        return "off"
    if choice == "gemini":
        return "gemini" if gem else "off"
    if choice == "anthropic":
        return "anthropic" if ant else "off"
    return "gemini" if gem else ("anthropic" if ant else "off")


# ── simple daily limit (whole clinic) ───────────────────────────────────────
_lock = threading.Lock()
_day = {"date": None, "count": 0}


def _allow():
    limit = int(os.environ.get("VOICE_DAILY_LIMIT", "300") or 300)
    today = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 19800))
    with _lock:
        if _day["date"] != today:
            _day["date"], _day["count"] = today, 0
        if _day["count"] >= limit:
            return False
        _day["count"] += 1
    return True


# ── instructions for the AI ─────────────────────────────────────────────────
def _instructions(mode, catalogue):
    common = f"""You turn a dentist's dictation into structured entries for a dental clinic app in Hyderabad, India.
The dentist speaks Indian English and often mixes Telugu or Hindi words, for example:
pannu/pallu/daant = tooth, puchu/pucchu/keeda = caries (decay), noppi/dard = pain, chigurlu/masude = gums,
raktam/khoon = bleeding, kadulutundi/hilta = mobile (loose), teeseyali/nikalna = should be extracted,
paina/upar = upper, kinda/neeche = lower, kudi/daayan = right, edama/baayan = left, ledu = missing,
ayyindi/chesam/ho gaya = done, cheyali/karna hai = to be done (advice).
Teeth use FDI numbers: permanent 11-18, 21-28, 31-38, 41-48; milk teeth 51-55, 61-65, 71-75, 81-85.
"one six" = 16. "upper right first molar" = 16, "lower left second premolar" = 35, "UR6" = 16, "lower left E" = 75,
wisdom tooth / third molar = 8 (18, 28, 38, 48). Ranges like "31 to 41" or "lower anteriors" (33,32,31,41,42,43) list every tooth.
Surfaces are letters from M, O, I, D, B, L (palatal = L, labial/facial = B), e.g. "MOD" -> ["M","O","D"].
Only write down what the dentist actually said. Never invent teeth, findings, medicines or doses.
If something is unclear, leave it out and add a short note to "problems".
Reply with JSON only, no other text, in exactly this shape:
{{"transcript": "<what was said, cleaned up, in English>", "items": [ ... ], "problems": ["..."]}}"""
    if mode in ("chart", "perio"):
        return common + f"""
Each item: {{"kind":"finding","tooth":16,"condition":"<one of the list>","other_text":"<only when condition is Other>",
"surfaces":["M","O","D"],"severity":"<mild|moderate|severe|critical or empty>","notes":"<short, optional>"}}
For something that is for the whole mouth (e.g. "generalised calculus") use {{"kind":"general","label":"Calculus / Tartar","notes":""}}.
Conditions (use these exact names): {", ".join(CONDITIONS)}.
Gum (perio) values: pocket depths go into a "Pockets" finding with notes like "B 5-4-6 · L 4-3-5 mm · bleeding on probing"
and severity 4-5 mm moderate, 6-7 severe, 8+ critical; bleeding alone = "Gingivitis" with notes "bleeding on probing";
recession = "Gum Recession" with notes "3 mm"; mobility grade 1/2/3 = "Mobility I"/"Mobility II"/"Mobility III";
furcation = "Furcation" with notes "Grade II". One item per tooth per condition."""
    if mode in ("both", "treatment", "advice"):
        which = {"both": 'Use "treatment" for what was done today and "advice" for what is planned / advised.',
                 "treatment": 'Every item is "treatment" (done today).',
                 "advice": 'Every item is "advice" (planned / advised).'}[mode]
        return common + f"""
Each item: {{"kind":"treatment" or "advice","label":"<one of the lists>","text":"<the treatment in words when label is Other>",
"teeth":[36,37],"note":"<details said, e.g. working length 21 mm, Protaper F2, implant Ø4.1 × 10 mm 35 Ncm>"}}
{which}
Treatment labels (done today): {", ".join(TREATMENTS)}.
Advice labels: {", ".join(ADVICE)}.
"Access opening" = "A/O Done"; cleaning and shaping / BMP = "BMP / Cleaning & Shaping Done"; scaling, polishing, curettage,
flap surgery, X-rays and anything else = label "Other" with the words in "text"."""
    cat = ", ".join(catalogue[:80]) if catalogue else "(none)"
    return common + f"""
Each item: {{"kind":"medicine","name":"<medicine and strength, e.g. Amoxicillin 500mg>","times":"<one of the list>",
"days":5,"when":"<one of the list or empty>","note":"<instructions, optional>"}}
How often (exact text): {", ".join(FREQUENCIES)}. BD = 2 times/day, TDS = 3 times/day, OD = 1 time/day, HS = At night,
SOS = When needed (SOS), 1-0-1 = 2 times/day, 1-1-1 = 3 times/day, 0-0-1 = At night.
When (exact text): {", ".join(WHENS)}.
The clinic's own medicine list (prefer these names when they match): {cat}.
Never add a medicine, strength or duration that was not said; if the number of days was not said, use "" and add a problem."""


# ── calling the AI ──────────────────────────────────────────────────────────
def _post_json(url, body, headers, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _ask_gemini(system, text, audio=None, mime=None):
    key = _keys()[0]
    model = os.environ.get("VOICE_MODEL") or "gemini-2.5-flash"
    parts = []
    if audio:
        parts.append({"inline_data": {"mime_type": mime or "audio/wav", "data": audio}})
        parts.append({"text": "Listen to the recording above. The browser's own transcript (may contain mistakes) is: "
                              + (text or "(none)")})
    else:
        parts.append({"text": "Dictation: " + text})
    data = _post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 4000, "responseMimeType": "application/json"},
    }, {"x-goog-api-key": key})
    out = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(p.get("text", "") for p in out)


def _ask_anthropic(system, text):
    key = _keys()[1]
    model = os.environ.get("VOICE_MODEL") or "claude-haiku-4-5-20251001"
    data = _post_json("https://api.anthropic.com/v1/messages", {
        "model": model, "max_tokens": 4000, "temperature": 0,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "Dictation: " + text}],
    }, {"x-api-key": key, "anthropic-version": "2023-06-01"})
    return "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text")


def _json_from(reply):
    s = (reply or "").strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.M).strip()
    try:
        return json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    return {}


# ── checking what the AI sent back ──────────────────────────────────────────
def _txt(v, n=200):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def _pick(value, allowed, default=""):
    v = _txt(value, 80)
    for a in allowed:
        if v.lower() == a.lower():
            return a
    return default


def _tooth(v):
    try:
        n = int(str(v).strip())
    except (TypeError, ValueError):
        return None
    return n if n in TEETH else None


def clean_items(mode, items):
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        kind = _txt(it.get("kind"), 20).lower()
        if mode in ("chart", "perio"):
            if kind == "general":
                label = _txt(it.get("label"), 80)
                if label:
                    out.append({"kind": "general", "label": label, "notes": _txt(it.get("notes"))})
                continue
            tooth = _tooth(it.get("tooth"))
            cond = _pick(it.get("condition"), CONDITIONS, "Other")
            other = _txt(it.get("other_text"), 100) if cond == "Other" else ""
            if cond == "Other" and not other:
                other = _txt(it.get("condition"), 100)
            if tooth is None or (cond == "Other" and not other):
                continue
            surf = it.get("surfaces") or []
            if isinstance(surf, str):
                surf = list(surf)
            surf = [s for s in "MOIDBL" if s in {str(x).strip().upper()[:1] for x in surf}]
            out.append({"kind": "finding", "tooth": tooth, "condition": cond, "other_text": other, "surfaces": surf,
                        "severity": _pick(it.get("severity"), SEVERITIES), "notes": _txt(it.get("notes"))})
        elif mode in ("both", "treatment", "advice"):
            if mode != "both":
                kind = mode
            if kind not in ("treatment", "advice"):
                kind = "advice"
            labels = TREATMENTS if kind == "treatment" else ADVICE
            label = _pick(it.get("label"), labels, "Other")
            text = _txt(it.get("text"), 120) if label == "Other" else label
            if label == "Other" and not text:
                text = _txt(it.get("label"), 120)
            if not text:
                continue
            teeth = []
            for t in it.get("teeth") or []:
                n = _tooth(t)
                if n is not None and n not in teeth:
                    teeth.append(n)
            deci = bool(teeth) and all(t >= 51 for t in teeth)
            out.append({"kind": kind, "label": label, "text": text, "teeth": sorted(teeth), "note": _txt(it.get("note")),
                        "chartType": "deciduous" if deci else "permanent"})
        else:
            name = _txt(it.get("name"), 80)
            if not name:
                continue
            days = it.get("days")
            try:
                days = int(days) if str(days).strip() != "" else ""
            except (TypeError, ValueError):
                days = ""
            if days != "" and not (0 < days <= 365):
                days = ""
            out.append({"kind": "medicine", "name": name, "times": _pick(it.get("times"), FREQUENCIES),
                        "days": days, "when": _pick(it.get("when"), WHENS), "note": _txt(it.get("note"), 120)})
    return out[:120]


# ── routes ──────────────────────────────────────────────────────────────────
@voice_bp.route("/voice/status", methods=["GET"])
@require_login
def voice_status():
    p = provider()
    return jsonify({"ai": p, "audio": p == "gemini"})


@voice_bp.route("/voice/normalize", methods=["POST"])
@require_login
def voice_normalize():
    p = provider()
    if p == "off":
        return jsonify({"error": "AI tidy-up is switched off. Add GEMINI_API_KEY (or ANTHROPIC_API_KEY) in Render to use it.",
                        "code": "NOT_CONFIGURED"}), 503
    body = request.get_json(silent=True) or {}
    mode = body.get("mode") if body.get("mode") in MODES else "chart"
    text = _txt(body.get("text"), 4000)
    audio = body.get("audio") or None
    mime = _txt(body.get("mime"), 40).lower().split(";")[0] or "audio/wav"
    catalogue = [_txt(c, 60) for c in (body.get("catalogue") or []) if _txt(c, 60)][:80]
    if audio:
        if p != "gemini" or mime not in AUDIO_TYPES:
            audio = None
        else:
            try:
                if len(base64.b64decode(audio, validate=True)) > MAX_AUDIO_BYTES:
                    return jsonify({"error": "The recording is too long. Please keep it under two minutes."}), 413
            except (ValueError, TypeError):
                audio = None
    if not text and not audio:
        return jsonify({"error": "Nothing was said or typed."}), 400
    if not _allow():
        return jsonify({"error": "Today's AI tidy-up limit has been reached. The entries made in the browser still work."}), 429
    system = _instructions(mode, catalogue)
    try:
        reply = _ask_gemini(system, text, audio, mime) if p == "gemini" else _ask_anthropic(system, text)
    except urllib.error.HTTPError as e:
        print("[voice] AI error:", e.code, e.read()[:300])
        return jsonify({"error": "The AI service refused the request. Please try again in a minute."}), 502
    except Exception as e:                                # timeout, no internet …
        print("[voice] AI not reachable:", type(e).__name__)
        return jsonify({"error": "The AI service could not be reached. The entries made in the browser still work."}), 502
    data = _json_from(reply)
    items = clean_items(mode, data.get("items"))
    problems = [_txt(x, 160) for x in (data.get("problems") or []) if _txt(x, 160)][:10]
    return jsonify({"items": items, "problems": problems, "transcript": _txt(data.get("transcript"), 4000), "provider": p}), 200