"""
PATIENT PORTAL — server side
══════════════════════════════════════════════════════════════════════════════
Patients log in with their registered mobile number and a one-time SMS code,
and see ONLY what the doctor has chosen to share with them. Nothing is visible
until the doctor shares it; anything can be withdrawn at any time.

  Doctor (clinic app, doctor login only)            /api/portal-admin/...
    GET  /portal-admin/patients/<pid>                  everything of the patient, with "shared" marks
    POST /portal-admin/patients/<pid>/access           {enabled, show_appointments}
    POST /portal-admin/patients/<pid>/share            {items:[{type,id}], message}
    POST /portal-admin/patients/<pid>/unshare          {items:[{type,id}]}
    GET  /portal-admin/overview                        small summary for the dashboard
      item types: visit_summary (id = visit id) · prescription · image · cbct · receipt

  Patient (portal website)                          /api/portal/...
    POST /portal/otp/request   {mobile}                sends a 6-digit code (same answer whether or not the number is known)
    POST /portal/otp/verify    {mobile, code}          -> {token, profiles}
    GET  /portal/me                                    profiles on this mobile number (family)
    GET  /portal/patients/<pid>/record                 the shared record
    GET  /portal/files/image/<id>                      {url} private 1-hour link (cloud) or {url:null}
    GET  /portal/files/image/<id>/data                 the picture (when not in the cloud)
    GET  /portal/files/receipt/<id>                    receipt PDF
    GET  /portal/files/cbct/<id>/preview               PNG preview of a CBCT scan
    GET  /portal/files/cbct/<id>/zip                   {url} private link to the original scan ZIP (cloud only)

Safety
  * A patient's login token (role "patient") is refused by EVERY other address
    of the server (before_app_request below) — it opens only /api/portal/.
  * Each request re-checks: the profile belongs to the logged-in mobile number,
    the doctor has the portal switched on for that profile, and the item is shared.
  * Codes: 6 digits, stored only as a keyed hash, valid 5 minutes, 5 tries;
    at most 3 codes per number per 15 minutes and 8 per day, 30 per hour per network address.
  * Every login and every file opened is logged (portal_log).

Settings (Render -> dental-backend -> Environment)
  PORTAL_SMS_PROVIDER   off (default) | test | http
                        test = the code is NOT sent; it is printed in the server log (clinic testing only)
  PORTAL_SMS_URL        the provider's address, with {mobile} (10 digits), {mobile91} (91 + 10 digits) and {otp},
                        e.g. 2Factor:  https://2factor.in/API/V1/<API_KEY>/SMS/{mobile}/{otp}/<TEMPLATE_NAME>
  PORTAL_SMS_METHOD     GET (default) | POST
  PORTAL_SMS_HEADERS    optional JSON, e.g. {"authkey": "..."}
  PORTAL_SMS_BODY       optional POST body with the same placeholders (JSON text)
  PORTAL_SMS_OK_TEXT    optional: text the provider's answer must contain on success (e.g. "Success")
  PORTAL_TOKEN_HOURS    login lasts this long (default 8)
  PORTAL_OTP_SECRET     optional; otherwise JWT_SECRET_KEY is used to key the code hashes
"""
import hashlib
import hmac
import io
import json
import os
import secrets
import threading
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, Response, current_app, jsonify, request, send_file
from sqlalchemy import or_
from werkzeug.exceptions import HTTPException

from database import db
from models import Patient, Visit

portal_bp = Blueprint("portal", __name__)

IST = timedelta(hours=5, minutes=30)
CLINIC_NAME = "Sri Satya Sai Oral Health Center & Dental Clinic"
ITEM_TYPES = ("visit_summary", "prescription", "image", "cbct", "receipt")


def _module(name):
    """Another routes file (works whether it is imported as `x` or `routes.x`)."""
    import importlib
    import sys
    for full in (name, f"routes.{name}"):
        if full in sys.modules:
            return sys.modules[full]
    for full in (name, f"routes.{name}"):
        try:
            return importlib.import_module(full)
        except Exception:
            continue
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  Tables (made by themselves)
# ═════════════════════════════════════════════════════════════════════════════
class PortalAccess(db.Model):
    __tablename__ = "portal_access"
    __table_args__ = {"extend_existing": True}
    patient_id        = db.Column(db.Integer, primary_key=True, autoincrement=False)
    enabled           = db.Column(db.Boolean, nullable=False, default=False)
    show_appointments = db.Column(db.Boolean, nullable=False, default=True)
    enabled_at        = db.Column(db.DateTime)
    enabled_by        = db.Column(db.String(120))


class PortalShare(db.Model):
    __tablename__ = "portal_shares"
    __table_args__ = {"extend_existing": True}
    id         = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, nullable=False, index=True)
    visit_id   = db.Column(db.Integer, index=True)
    item_type  = db.Column(db.String(20), nullable=False)
    item_id    = db.Column(db.Integer, nullable=False)
    message    = db.Column(db.Text)
    shared_at  = db.Column(db.DateTime, default=datetime.utcnow)
    shared_by  = db.Column(db.String(120))
    revoked_at = db.Column(db.DateTime)
    revoked_by = db.Column(db.String(120))
    seen_at    = db.Column(db.DateTime)


class PortalOtp(db.Model):
    __tablename__ = "portal_otps"
    __table_args__ = {"extend_existing": True}
    id         = db.Column(db.Integer, primary_key=True)
    mobile     = db.Column(db.String(15), nullable=False, index=True)
    code_hash  = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts   = db.Column(db.Integer, nullable=False, default=0)
    used_at    = db.Column(db.DateTime)
    ip         = db.Column(db.String(64))


class PortalLog(db.Model):
    __tablename__ = "portal_log"
    __table_args__ = {"extend_existing": True}
    id         = db.Column(db.Integer, primary_key=True)
    at         = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    mobile     = db.Column(db.String(15))
    patient_id = db.Column(db.Integer, index=True)
    action     = db.Column(db.String(30))
    detail     = db.Column(db.String(200))
    ip         = db.Column(db.String(64))


_ready = {"ok": False}
_ready_lock = threading.Lock()


def ensure_portal_tables(app=None):
    if _ready["ok"]:
        return
    with _ready_lock:
        if _ready["ok"]:
            return
        try:
            def make():
                for model in (PortalAccess, PortalShare, PortalOtp, PortalLog):
                    model.__table__.create(bind=db.engine, checkfirst=True)
            if app is not None:
                with app.app_context():
                    make()
            else:
                make()
            _ready["ok"] = True
        except Exception as exc:
            print("[portal] could not prepare the portal tables:", type(exc).__name__, str(exc)[:200])


# ═════════════════════════════════════════════════════════════════════════════
#  Errors, roles, small helpers
# ═════════════════════════════════════════════════════════════════════════════
class PortalError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


def _guard(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        try:
            ensure_portal_tables()
            return fn(*a, **kw)
        except PortalError as exc:
            db.session.rollback()
            return jsonify({"error": exc.message}), exc.status
        except HTTPException as exc:
            db.session.rollback()
            return jsonify({"error": "Not found." if exc.code == 404 else (exc.description or "Request failed")}), exc.code or 500
        except Exception as exc:
            db.session.rollback()
            print("[portal] request failed:", type(exc).__name__, str(exc)[:300])
            return jsonify({"error": "Something went wrong. Please try again."}), 500
    return wrapped


def _jwt_claims(required):
    from flask_jwt_extended import get_jwt, verify_jwt_in_request
    try:
        verify_jwt_in_request(optional=not required)
        return get_jwt() or {}
    except Exception:
        if required:
            raise PortalError("Please log in again.", 401)
        return {}


def _staff_role():
    """'doctor' / 'reception' of a clinic login ('' if none)."""
    try:
        role = str(_jwt_claims(False).get("role") or "").strip().lower()
        if role:
            return role
    except Exception:
        pass
    try:
        au = _module("auth_utils")
        return str(au.get_current_role() or "").strip().lower() if au else ""
    except Exception:
        return ""


def _staff_name():
    try:
        mh = _module("medical_history")
        name = (mh.current_actor() or {}).get("name") if mh else None
        if name:
            return str(name)[:120]
    except Exception:
        pass
    try:   # the clinic login: token identity = users.id
        from flask_jwt_extended import get_jwt_identity
        import models as _m
        ident = get_jwt_identity()
        U = getattr(_m, "User", None)
        if U is not None and ident and str(ident).isdigit():
            u = db.session.get(U, int(ident))
            if u is not None and getattr(u, "username", None):
                return str(u.username)[:120]
    except Exception:
        pass
    return "Doctor"


def _doctor_only():
    if _staff_role() not in ("doctor", "admin"):
        raise PortalError("Only the doctor can decide what patients see in the portal.", 403)


def _ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() or request.remote_addr or "")[:64]


def _digits(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _mobile(raw):
    d = _digits(raw)
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if len(d) != 10 or d[0] not in "6789":
        raise PortalError("Please enter your 10-digit mobile number.")
    return d


def _masked(m):
    return f"{m[:2]}••••••{m[-2:]}" if m and len(m) >= 4 else ""


def _ist(dt, fmt="%d %b %Y"):
    if not dt:
        return None
    if isinstance(dt, datetime):
        return (dt + IST).strftime(fmt)
    try:
        return dt.strftime(fmt)
    except Exception:
        return str(dt)


def _log(action, detail="", mobile=None, patient_id=None):
    try:
        db.session.add(PortalLog(action=action, detail=str(detail or "")[:200], mobile=mobile,
                                 patient_id=patient_id, ip=_ip()))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _patients_on_mobile(m):
    """Patients whose registered mobile is this number (family members may share one)."""
    cands = Patient.query.filter(Patient.mobile.ilike(f"%{m[-4:]}%")).all()
    return [p for p in cands if _digits(p.mobile)[-10:] == m]


def _access(pid):
    return db.session.get(PortalAccess, pid)


def _enabled_profiles(m):
    out = []
    for p in _patients_on_mobile(m):
        a = _access(p.id)
        if a is not None and a.enabled:
            out.append(p)
    return out


# ═════════════════════════════════════════════════════════════════════════════
#  Keep patients OUT of every clinic address
# ═════════════════════════════════════════════════════════════════════════════
@portal_bp.before_app_request
def _patients_only_in_portal():
    if request.method == "OPTIONS" or request.path.startswith("/api/portal/"):
        return None
    try:
        from flask_jwt_extended import get_jwt, verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        if (get_jwt() or {}).get("role") == "patient":
            return jsonify({"error": "This login is for the patient portal only."}), 403
    except Exception:
        pass
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  SMS
# ═════════════════════════════════════════════════════════════════════════════
def _otp_secret():
    s = (os.environ.get("PORTAL_OTP_SECRET") or os.environ.get("JWT_SECRET_KEY")
         or current_app.config.get("JWT_SECRET_KEY") or current_app.config.get("SECRET_KEY") or "")
    if not s:
        raise PortalError("The portal is not set up on the server yet (no secret key).", 503)
    return str(s).encode()


def _hash(m, code):
    return hmac.new(_otp_secret(), f"{m}:{code}".encode(), hashlib.sha256).hexdigest()


def sms_mode():
    mode = (os.environ.get("PORTAL_SMS_PROVIDER") or "off").strip().lower()
    return mode if mode in ("off", "test", "http") else "off"


def _send_sms(m, code):
    mode = sms_mode()
    if mode == "test":
        print(f"[portal] TEST MODE — login code for {_masked(m)} ({m}): {code}  (not sent by SMS)")
        return
    if mode != "http":
        raise PortalError("Portal login by SMS is not switched on yet. Please contact the clinic.", 503)
    url_t = (os.environ.get("PORTAL_SMS_URL") or "").strip()
    if not url_t:
        raise PortalError("Portal login by SMS is not set up yet. Please contact the clinic.", 503)
    vals = {"mobile": m, "mobile91": "91" + m, "otp": code}
    fill = lambda t, enc: t.format(**{k: (urllib.parse.quote(v) if enc else v) for k, v in vals.items()})
    try:
        url = fill(url_t, True)
        method = (os.environ.get("PORTAL_SMS_METHOD") or "GET").strip().upper()
        headers = json.loads(os.environ.get("PORTAL_SMS_HEADERS") or "{}")
        body = os.environ.get("PORTAL_SMS_BODY")
        data = fill(body, False).encode() if (body and method == "POST") else None
        if data and not any(k.lower() == "content-type" for k in headers):
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            answer = r.read(4000).decode("utf-8", "replace")
        ok_text = (os.environ.get("PORTAL_SMS_OK_TEXT") or "").strip()
        if ok_text and ok_text.lower() not in answer.lower():
            raise RuntimeError("provider answer: " + answer[:160])
    except PortalError:
        raise
    except Exception as exc:
        print("[portal] SMS could not be sent:", type(exc).__name__, str(exc)[:200])
        raise PortalError("The code could not be sent just now. Please try again in a minute.", 502)


# ═════════════════════════════════════════════════════════════════════════════
#  PATIENT LOGIN
# ═════════════════════════════════════════════════════════════════════════════
OTP_MINUTES, OTP_TRIES = 5, 5


@portal_bp.route("/portal/otp/request", methods=["POST"])
@_guard
def otp_request():
    data = request.get_json(force=True, silent=True) or {}
    m = _mobile(data.get("mobile"))
    now = datetime.utcnow()
    if PortalOtp.query.filter(PortalOtp.ip == _ip(), PortalOtp.created_at >= now - timedelta(hours=1)).count() >= 30:
        raise PortalError("Too many attempts from this network. Please try again later.", 429)
    if PortalOtp.query.filter(PortalOtp.mobile == m, PortalOtp.created_at >= now - timedelta(minutes=15)).count() >= 3:
        raise PortalError("Too many codes asked for this number. Please wait 15 minutes.", 429)
    if PortalOtp.query.filter(PortalOtp.mobile == m, PortalOtp.created_at >= now - timedelta(days=1)).count() >= 8:
        raise PortalError("Too many codes asked for this number today. Please try tomorrow or contact the clinic.", 429)
    generic = {"sent": True, "message": "If this number is registered for the portal, a 6-digit code has been sent by SMS.",
               "expires_minutes": OTP_MINUTES, "mobile": _masked(m)}
    known = bool(_enabled_profiles(m))
    code = f"{secrets.randbelow(10**6):06d}"
    # a row is written either way, so the limits above also hold for numbers that are not registered
    db.session.add(PortalOtp(mobile=m, code_hash=_hash(m, code) if known else "-", ip=_ip(),
                             expires_at=now + timedelta(minutes=OTP_MINUTES)))
    db.session.commit()
    if known:
        _send_sms(m, code)
        _log("code_sent", "", m)
    else:
        _log("code_unknown_number", "", m)
    return jsonify(generic)


@portal_bp.route("/portal/otp/verify", methods=["POST"])
@_guard
def otp_verify():
    data = request.get_json(force=True, silent=True) or {}
    m = _mobile(data.get("mobile"))
    code = _digits(data.get("code"))[:6]
    if len(code) != 6:
        raise PortalError("Please enter the 6-digit code.")
    now = datetime.utcnow()
    row = (PortalOtp.query.filter(PortalOtp.mobile == m, PortalOtp.used_at.is_(None), PortalOtp.expires_at > now)
           .order_by(PortalOtp.id.desc()).first())
    if row is None or row.code_hash == "-":
        _log("login_failed", "no valid code", m)
        raise PortalError("This code is not valid or has expired. Please ask for a new code.", 401)
    if row.attempts >= OTP_TRIES:
        raise PortalError("Too many wrong tries. Please ask for a new code.", 429)
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, _hash(m, code)):
        db.session.commit()
        _log("login_failed", "wrong code", m)
        left = OTP_TRIES - row.attempts
        raise PortalError(f"Wrong code. {left} tr{'y' if left == 1 else 'ies'} left." if left else
                          "Wrong code. Please ask for a new code.", 401)
    row.used_at = now
    db.session.commit()
    profiles = _enabled_profiles(m)
    if not profiles:
        raise PortalError("The portal is not switched on for this number. Please contact the clinic.", 403)
    from flask_jwt_extended import create_access_token
    hours = max(1, min(72, int(float(os.environ.get("PORTAL_TOKEN_HOURS") or 8))))
    token = create_access_token(identity=f"patient:{m}", expires_delta=timedelta(hours=hours),
                                additional_claims={"role": "patient", "mobile": m})
    _log("login", f"{len(profiles)} profile(s)", m)
    return jsonify({"token": token, "expires_hours": hours, "mobile": _masked(m),
                    "profiles": [_profile(p) for p in profiles]})


def _profile(p):
    unseen = PortalShare.query.filter(PortalShare.patient_id == p.id, PortalShare.revoked_at.is_(None),
                                      PortalShare.seen_at.is_(None)).count()
    return {"patient_id": p.id, "name": p.name, "case_number": p.case_number, "age": p.age,
            "gender": p.gender, "new_items": unseen}


def _patient_login():
    c = _jwt_claims(True)
    if c.get("role") != "patient" or not c.get("mobile"):
        raise PortalError("Please log in to the patient portal.", 401)
    return c["mobile"]


def _my_patient(pid):
    """The profile, if it belongs to the logged-in number and the doctor has the portal on for it."""
    m = _patient_login()
    p = db.session.get(Patient, pid)
    a = _access(pid)
    if p is None or _digits(p.mobile)[-10:] != m or a is None or not a.enabled:
        raise PortalError("This record is not available.", 404)
    return m, p, a


@portal_bp.route("/portal/me", methods=["GET"])
@_guard
def portal_me():
    m = _patient_login()
    return jsonify({"mobile": _masked(m), "clinic": CLINIC_NAME, "profiles": [_profile(p) for p in _enabled_profiles(m)]})


# ═════════════════════════════════════════════════════════════════════════════
#  What exists for a patient (doctor view) / what is shared (patient view)
# ═════════════════════════════════════════════════════════════════════════════
def _active_shares(pid):
    return {(s.item_type, s.item_id): s for s in
            PortalShare.query.filter(PortalShare.patient_id == pid, PortalShare.revoked_at.is_(None)).all()}


def _models():
    out = {}
    try:
        from models import Prescription
        out["Prescription"] = Prescription
    except Exception:
        pass
    try:
        from models import Image
        out["Image"] = Image
    except Exception:
        pass
    try:
        from models import CBCTVolume
        out["CBCTVolume"] = CBCTVolume
    except Exception:
        pass
    try:
        from models import Consultation
        out["Consultation"] = Consultation
    except Exception:
        pass
    br = _module("billing_receipts")
    if br is not None and hasattr(br, "BillingReceipt"):
        out["BillingReceipt"] = br.BillingReceipt
    return out


def _visits_of(pid):
    return (Visit.query.filter(Visit.patient_id == pid)
            .filter(or_(Visit.status.is_(None), Visit.status != "CANCELLED"))
            .order_by(Visit.visit_date.desc().nullslast(), Visit.id.desc()).all())


def _owner_of(item_type, item_id):
    """(patient_id, visit_id) of an item, or (None, None)."""
    M = _models()
    if item_type == "visit_summary":
        v = db.session.get(Visit, item_id)
        return (v.patient_id, v.id) if v else (None, None)
    model = {"prescription": "Prescription", "image": "Image", "cbct": "CBCTVolume"}.get(item_type)
    if model:
        if model not in M:
            return None, None
        row = db.session.get(M[model], item_id)
        v = db.session.get(Visit, row.visit_id) if row is not None and row.visit_id else None
        return (v.patient_id, v.id) if v else (None, None)
    if item_type == "receipt" and "BillingReceipt" in M:
        r = db.session.get(M["BillingReceipt"], item_id)
        return (r.patient_id, getattr(r, "visit_id", None)) if r is not None else (None, None)
    return None, None


def _rx_rows(visit_ids):
    M = _models()
    if "Prescription" not in M or not visit_ids:
        return []
    return M["Prescription"].query.filter(M["Prescription"].visit_id.in_(visit_ids)).order_by(M["Prescription"].id).all()


def _investigations(ids):
    pr = _module("prescription")
    try:
        return pr._investigations_of(ids) if pr is not None and hasattr(pr, "_investigations_of") else {}
    except Exception:
        db.session.rollback()
        return {}


def _medicines(raw):
    try:
        meds = json.loads(raw or "[]")
    except Exception:
        return []
    out = []
    for m in meds if isinstance(meds, list) else []:
        if not isinstance(m, dict):
            continue
        name = m.get("name") or m.get("drug_name") or m.get("medicine") or ""
        if not name:
            continue
        out.append({
            "name": str(name)[:120],
            "dose": str(m.get("dosage") or m.get("dose") or m.get("strength") or "")[:60],
            "when": str(m.get("times") or m.get("frequency") or m.get("timing") or "")[:80],
            "food": str(m.get("when") or m.get("food") or m.get("before_after") or "")[:60],
            "days": str(m.get("days") or m.get("duration") or "")[:30],
            "notes": str(m.get("instructions") or m.get("notes") or "")[:200],
        })
    return out


def _receipts_of(pid):
    M = _models()
    if "BillingReceipt" not in M:
        return []
    R = M["BillingReceipt"]
    return R.query.filter(R.patient_id == pid).order_by(R.receipt_date.desc(), R.receipt_no.desc()).all()


def _receipt_amount(r):
    try:
        return float(r.amount_paid or 0)
    except Exception:
        return 0.0


def _latest_consultation(visit_id):
    M = _models()
    if "Consultation" not in M:
        return None
    C = M["Consultation"]
    return C.query.filter(C.visit_id == visit_id).order_by(C.id.desc()).first()


def _summary_of(v):
    c = _latest_consultation(v.id)
    pick = lambda *vals: next((str(x).strip() for x in vals if x and str(x).strip()), "")
    nxt = getattr(v, "next_appointment", None) or (getattr(c, "follow_up_date", None) if c else None)
    return {
        "chief_complaint": pick(v.chief_complaint),
        "diagnosis":       pick(c.diagnosis if c else None, v.diagnosis),
        "treatment_done":  pick(c.treatment_done_today if c else None, v.treatment_done),
        "treatment_plan":  pick(c.treatment_plan if c else None, v.treatment_plan),
        "advice":          pick(c.advice if c else None, v.advice),
        "next_visit":      _ist(nxt) if nxt else None,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  DOCTOR: choose what the patient sees
# ═════════════════════════════════════════════════════════════════════════════
@portal_bp.route("/portal-admin/patients/<int:pid>", methods=["GET"])
@_guard
def admin_patient(pid):
    _doctor_only()
    p = db.session.get(Patient, pid)
    if p is None:
        raise PortalError("This patient no longer exists.", 404)
    M = _models()
    shares = _active_shares(pid)
    sh = lambda t, i: ({"shared": True, "shared_at": _ist(shares[(t, i)].shared_at, "%d %b %Y, %I:%M %p"),
                        "seen": bool(shares[(t, i)].seen_at)} if (t, i) in shares else {"shared": False})
    visits = _visits_of(pid)
    vids = [v.id for v in visits]
    rx_by_visit, img_by_visit, cbct_by_visit = {}, {}, {}
    for r in _rx_rows(vids):
        rx_by_visit.setdefault(r.visit_id, []).append(r)
    if "Image" in M and vids:
        for im in M["Image"].query.filter(M["Image"].visit_id.in_(vids)).order_by(M["Image"].id).all():
            img_by_visit.setdefault(im.visit_id, []).append(im)
    if "CBCTVolume" in M and vids:
        for cv in M["CBCTVolume"].query.filter(M["CBCTVolume"].visit_id.in_(vids)).order_by(M["CBCTVolume"].id).all():
            cbct_by_visit.setdefault(cv.visit_id, []).append(cv)
    out_visits = []
    for v in visits:
        s = _summary_of(v)
        out_visits.append({
            "visit_id": v.id, "date": _ist(v.visit_date), "status": v.status,
            "treatment": s["treatment_done"] or getattr(v, "followup_treatment", None) or s["chief_complaint"] or "",
            "diagnosis": s["diagnosis"],
            "summary": sh("visit_summary", v.id),
            "prescriptions": [{"id": r.id, "date": r.date or _ist(r.created_at), "medicines": len(_medicines(r.medicines)),
                               **sh("prescription", r.id)} for r in rx_by_visit.get(v.id, [])],
            "images": [{"id": im.id, "type": im.image_type, "date": _ist(getattr(im, "image_date", None)),
                        "description": im.description or "", "url": f"/api/images/{im.id}/data", **sh("image", im.id)}
                       for im in img_by_visit.get(v.id, [])],
            "cbct": [{"id": cv.id, "date": _ist(cv.uploaded_at), "slices": cv.num_slices, **sh("cbct", cv.id)}
                     for cv in cbct_by_visit.get(v.id, [])],
        })
    receipts = [{"id": r.id, "receipt_no": r.receipt_no, "date": _ist(r.receipt_date), "amount": _receipt_amount(r),
                 **sh("receipt", r.id)} for r in _receipts_of(pid)]
    a = _access(pid)
    m = _digits(p.mobile)[-10:]
    family = [{"patient_id": f.id, "name": f.name, "case_number": f.case_number,
               "portal_on": bool(getattr(_access(f.id), "enabled", False))}
              for f in (_patients_on_mobile(m) if len(m) == 10 else []) if f.id != p.id]
    log = (PortalLog.query.filter(PortalLog.patient_id == pid).order_by(PortalLog.id.desc()).limit(15).all())
    return jsonify({
        "patient": {"id": p.id, "name": p.name, "case_number": p.case_number, "mobile": p.mobile,
                    "mobile_ok": len(m) == 10 and m[0] in "6789"},
        "access": {"enabled": bool(a and a.enabled), "show_appointments": bool(a.show_appointments) if a else True,
                   "enabled_at": _ist(a.enabled_at, "%d %b %Y") if a and a.enabled_at else None,
                   "enabled_by": a.enabled_by if a else None},
        "family": family,
        "visits": out_visits,
        "receipts": receipts,
        "shared_count": len(shares),
        "log": [{"at": _ist(l.at, "%d %b %Y, %I:%M %p"), "action": l.action, "detail": l.detail} for l in log],
        "sms": sms_mode(),
    })


@portal_bp.route("/portal-admin/patients/<int:pid>/access", methods=["POST"])
@_guard
def admin_access(pid):
    _doctor_only()
    p = db.session.get(Patient, pid)
    if p is None:
        raise PortalError("This patient no longer exists.", 404)
    data = request.get_json(force=True, silent=True) or {}
    a = _access(pid) or PortalAccess(patient_id=pid, enabled=False, show_appointments=True)
    if "enabled" in data:
        on = bool(data.get("enabled"))
        if on:
            m = _digits(p.mobile)[-10:]
            if len(m) != 10 or m[0] not in "6789":
                raise PortalError("This patient's mobile number is not a valid 10-digit Indian number. Correct it first.")
            if not a.enabled:
                a.enabled_at, a.enabled_by = datetime.utcnow(), _staff_name()
        a.enabled = on
    if "show_appointments" in data:
        a.show_appointments = bool(data.get("show_appointments"))
    db.session.add(a)
    db.session.commit()
    _log("portal_on" if a.enabled else "portal_off", f"by {_staff_name()}", None, pid)
    return admin_patient(pid)


def _items(data):
    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        raise PortalError("Choose at least one item.")
    out = []
    for it in items[:500]:
        t = str((it or {}).get("type") or "")
        try:
            i = int((it or {}).get("id"))
        except (TypeError, ValueError):
            raise PortalError("An item could not be read. Please try again.")
        if t not in ITEM_TYPES:
            raise PortalError(f"Unknown item type: {t}")
        out.append((t, i))
    return out


@portal_bp.route("/portal-admin/patients/<int:pid>/share", methods=["POST"])
@_guard
def admin_share(pid):
    _doctor_only()
    if db.session.get(Patient, pid) is None:
        raise PortalError("This patient no longer exists.", 404)
    data = request.get_json(force=True, silent=True) or {}
    message = (str(data.get("message") or "").strip()[:1000]) or None
    shares = _active_shares(pid)
    who = _staff_name()
    added = 0
    for t, i in _items(data):
        owner, visit_id = _owner_of(t, i)
        if owner != pid:
            raise PortalError("One of the chosen items does not belong to this patient.", 400)
        if (t, i) in shares:
            if message and t == "visit_summary":
                shares[(t, i)].message = message
            continue
        db.session.add(PortalShare(patient_id=pid, visit_id=visit_id, item_type=t, item_id=i,
                                   message=message if t == "visit_summary" else None,
                                   shared_by=who, shared_at=datetime.utcnow()))
        added += 1
    db.session.commit()
    _log("shared", f"{added} item(s) by {who}", None, pid)
    return admin_patient(pid)


@portal_bp.route("/portal-admin/patients/<int:pid>/unshare", methods=["POST"])
@_guard
def admin_unshare(pid):
    _doctor_only()
    data = request.get_json(force=True, silent=True) or {}
    shares = _active_shares(pid)
    who = _staff_name()
    n = 0
    for key in _items(data):
        s = shares.get(key)
        if s is not None:
            s.revoked_at, s.revoked_by = datetime.utcnow(), who
            n += 1
    db.session.commit()
    _log("withdrawn", f"{n} item(s) by {who}", None, pid)
    return admin_patient(pid)


@portal_bp.route("/portal-admin/overview", methods=["GET"])
@_guard
def admin_overview():
    _doctor_only()
    now = datetime.utcnow()
    today = datetime.combine((now + IST).date(), datetime.min.time()) - IST
    return jsonify({
        "patients_on": PortalAccess.query.filter(PortalAccess.enabled.is_(True)).count(),
        "shared_7_days": PortalShare.query.filter(PortalShare.shared_at >= now - timedelta(days=7),
                                                  PortalShare.revoked_at.is_(None)).count(),
        "logins_today": PortalLog.query.filter(PortalLog.action == "login", PortalLog.at >= today).count(),
        "sms": sms_mode(),
    })


# ═════════════════════════════════════════════════════════════════════════════
#  PATIENT: the shared record
# ═════════════════════════════════════════════════════════════════════════════
def _appointments_for(p):
    ap = _module("appointments")
    if ap is None or not getattr(ap, "configured", lambda: False)():
        return None
    try:
        rows = ap.sb_select(patient_id=f"eq.{p.id}")
        today = ap.today_ist().isoformat()
        shaped = []
        for r in rows:
            st = str(r.get("status") or "SCHEDULED").upper()
            if st == "CANCELLED":
                continue
            shaped.append({"date": str(r.get("appointment_date") or "")[:10], "time": str(r.get("appointment_time") or "")[:5],
                           "treatment": r.get("treatment") or "", "doctor": r.get("doctor_name") or "",
                           "status": "Completed" if st == "COMPLETED" else "Booked"})
        upcoming = sorted([a for a in shaped if a["date"] >= today and a["status"] == "Booked"], key=lambda a: (a["date"], a["time"]))
        past = sorted([a for a in shaped if a not in upcoming], key=lambda a: (a["date"], a["time"]), reverse=True)[:30]
        return {"upcoming": upcoming, "past": past}
    except Exception as exc:
        print("[portal] appointments could not be read:", type(exc).__name__, str(exc)[:200])
        return None


@portal_bp.route("/portal/patients/<int:pid>/record", methods=["GET"])
@_guard
def portal_record(pid):
    m, p, a = _my_patient(pid)
    M = _models()
    shares = PortalShare.query.filter(PortalShare.patient_id == pid, PortalShare.revoked_at.is_(None)).all()
    by_type = {}
    for s in shares:
        by_type.setdefault(s.item_type, {})[s.item_id] = s
    new_ids = {(s.item_type, s.item_id) for s in shares if s.seen_at is None}

    visits = {}

    def visit_entry(visit_id):
        if visit_id not in visits:
            v = db.session.get(Visit, visit_id)
            if v is None or v.patient_id != pid:
                return None
            visits[visit_id] = {"visit_id": v.id, "date": _ist(v.visit_date), "sort": v.visit_date or datetime.min,
                                "summary": None, "message": None, "prescriptions": [], "images": [], "cbct": []}
        return visits[visit_id]

    for vid, s in by_type.get("visit_summary", {}).items():
        e = visit_entry(vid)
        if e is not None:
            v = db.session.get(Visit, vid)
            e["summary"] = _summary_of(v)
            e["message"] = s.message
            e["summary_new"] = ("visit_summary", vid) in new_ids
    rx_ids = list(by_type.get("prescription", {}).keys())
    if rx_ids and "Prescription" in M:
        inv = _investigations(rx_ids)
        for r in M["Prescription"].query.filter(M["Prescription"].id.in_(rx_ids)).all():
            e = visit_entry(r.visit_id)
            if e is None:
                continue
            e["prescriptions"].append({
                "id": r.id, "date": r.date or _ist(r.created_at), "doctor": r.doctor or "",
                "diagnosis": r.diagnosis or "", "advice": r.advice or "",
                "medicines": _medicines(r.medicines),
                "investigations": [{"name": i.get("name"), "note": i.get("note") or "", "group": i.get("group") or ""}
                                   for i in (inv.get(r.id) or []) if isinstance(i, dict) and i.get("name")],
                "follow_up": " ".join(x for x in (_ist(r.follow_up_date) if r.follow_up_date else "", r.follow_up_time or "") if x),
                "new": ("prescription", r.id) in new_ids,
            })
    img_ids = list(by_type.get("image", {}).keys())
    if img_ids and "Image" in M:
        for im in M["Image"].query.filter(M["Image"].id.in_(img_ids)).all():
            e = visit_entry(im.visit_id)
            if e is not None:
                e["images"].append({"id": im.id, "type": im.image_type, "date": _ist(getattr(im, "image_date", None)),
                                    "description": im.description or "", "mime_type": getattr(im, "mime_type", None) or "image/jpeg",
                                    "new": ("image", im.id) in new_ids})
    cb_ids = list(by_type.get("cbct", {}).keys())
    if cb_ids and "CBCTVolume" in M:
        for cv in M["CBCTVolume"].query.filter(M["CBCTVolume"].id.in_(cb_ids)).all():
            e = visit_entry(cv.visit_id)
            if e is not None:
                e["cbct"].append({"id": cv.id, "date": _ist(cv.uploaded_at), "slices": cv.num_slices,
                                  "new": ("cbct", cv.id) in new_ids})
    receipts = []
    rc_ids = list(by_type.get("receipt", {}).keys())
    if rc_ids and "BillingReceipt" in M:
        R = M["BillingReceipt"]
        for r in R.query.filter(R.id.in_(rc_ids), R.patient_id == pid).order_by(R.receipt_date.desc()).all():
            try:
                treat = ", ".join(str(t.get("name") or "") for t in json.loads(r.treatments_json or "[]") if isinstance(t, dict))
            except Exception:
                treat = ""
            receipts.append({"id": r.id, "receipt_no": r.receipt_no, "date": _ist(r.receipt_date),
                             "amount": _receipt_amount(r), "treatments": treat[:200], "new": ("receipt", r.id) in new_ids})

    vlist = sorted(visits.values(), key=lambda e: e.pop("sort"), reverse=True)
    for e in vlist:
        e["prescriptions"].sort(key=lambda r: r["id"])
        e["images"].sort(key=lambda i: i["id"])
    result = {
        "clinic": CLINIC_NAME,
        "patient": {"id": p.id, "name": p.name, "case_number": p.case_number, "age": p.age, "gender": p.gender},
        "visits": vlist,
        "receipts": receipts,
        "appointments": _appointments_for(p) if a.show_appointments else None,
        "new_items": len(new_ids),
    }
    # mark as seen (the doctor sees "seen by patient")
    if new_ids:
        now = datetime.utcnow()
        for s in shares:
            if s.seen_at is None:
                s.seen_at = now
        db.session.commit()
    _log("viewed_record", "", m, pid)
    return jsonify(result)


def _shared_item(item_type, item_id):
    """(mobile, patient, share) for a shared item of the logged-in patient, else 404."""
    m = _patient_login()
    owner, _visit = _owner_of(item_type, item_id)
    if owner is None:
        raise PortalError("This file is not available.", 404)
    _m, p, _a = _my_patient(owner)
    s = PortalShare.query.filter(PortalShare.patient_id == owner, PortalShare.item_type == item_type,
                                 PortalShare.item_id == item_id, PortalShare.revoked_at.is_(None)).first()
    if s is None:
        raise PortalError("This file is not available.", 404)
    return m, p, s


@portal_bp.route("/portal/files/image/<int:image_id>", methods=["GET"])
@_guard
def portal_image_link(image_id):
    m, p, _s = _shared_item("image", image_id)
    im_mod = _module("images")
    M = _models()
    img = db.session.get(M["Image"], image_id)
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    url = dl = None
    if im_mod is not None and im_mod.storage_for(img.image_path) is im_mod._S3:
        try:
            name = im_mod._download_name(img, mime)
            url = im_mod._S3.presign(img.image_path, mime, None, 3600)
            dl = im_mod._S3.presign(img.image_path, mime, name, 3600)
        except Exception as exc:
            print("[portal] could not make a link:", type(exc).__name__)
            url = None
    _log("opened_image", str(image_id), m, p.id)
    return jsonify({"url": url, "download_url": dl if url else None, "mime_type": mime})


@portal_bp.route("/portal/files/image/<int:image_id>/data", methods=["GET"])
@_guard
def portal_image_data(image_id):
    m, p, _s = _shared_item("image", image_id)
    im_mod = _module("images")
    M = _models()
    img = db.session.get(M["Image"], image_id)
    mime = getattr(img, "mime_type", None) or "image/jpeg"
    data = None
    if im_mod is not None:
        store = im_mod.storage_for(img.image_path)
        try:
            data = store.read(img.image_path)
        except Exception:
            data = None
        if data is None:
            data = im_mod._decode_base64(im_mod._base64_of(img))
    if not data:
        raise PortalError("This picture's file is missing. Please contact the clinic.", 404)
    return Response(data, mimetype=mime, headers={"Cache-Control": "private, max-age=600"})


@portal_bp.route("/portal/files/receipt/<int:receipt_id>", methods=["GET"])
@_guard
def portal_receipt_pdf(receipt_id):
    m, p, _s = _shared_item("receipt", receipt_id)
    br = _module("billing_receipts")
    r = db.session.get(br.BillingReceipt, receipt_id)
    try:
        pdf = br.build_receipt_pdf(r)
    except Exception as exc:
        print("[portal] receipt PDF failed:", type(exc).__name__, str(exc)[:200])
        raise PortalError("The receipt could not be prepared just now. Please try again.", 500)
    _log("opened_receipt", str(r.receipt_no), m, p.id)
    return send_file(io.BytesIO(pdf), mimetype="application/pdf", as_attachment=False,
                     download_name=f"Receipt-{r.receipt_no}.pdf")


@portal_bp.route("/portal/files/cbct/<int:cbct_id>/preview", methods=["GET"])
@_guard
def portal_cbct_preview(cbct_id):
    m, p, _s = _shared_item("cbct", cbct_id)
    cb = _module("cbct_backend")
    if cb is None:
        raise PortalError("The scan preview is not available.", 404)
    _log("opened_cbct", str(cbct_id), m, p.id)
    return cb.export_png(cbct_id)


@portal_bp.route("/portal/files/cbct/<int:cbct_id>/zip", methods=["GET"])
@_guard
def portal_cbct_zip(cbct_id):
    m, p, _s = _shared_item("cbct", cbct_id)
    cb = _module("cbct_backend")
    im_mod = _module("images")
    M = _models()
    vol = db.session.get(M["CBCTVolume"], cbct_id)
    loc = str(getattr(vol, "slice_data", "") or "")
    if not (cb and im_mod and loc.startswith("s3://")):
        return jsonify({"url": None})
    zloc = loc.rsplit("/", 1)[0] + "/original-dicom.zip"
    try:
        if not im_mod._S3.exists(zloc):
            return jsonify({"url": None})
        url = im_mod._S3.presign(zloc, "application/zip", f"CBCT-scan-{cbct_id}.zip", 3600)
    except Exception:
        return jsonify({"url": None})
    _log("downloaded_cbct", str(cbct_id), m, p.id)
    return jsonify({"url": url})