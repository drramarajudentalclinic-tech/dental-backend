"""
Staff login (Doctor / Reception) — safe, real-time accounts.

WHAT THIS FILE DOES
───────────────────
• Login with username + password (same as before) → a pass (JWT) for 14 hours.
• Nobody can create an account from outside any more. Only a logged-in Doctor
  adds staff (👥 Staff screen). /register is Doctor-only, /setup is closed.
• Real time: every request checks the account is still switched on and the pass
  is still current. Switching an account off, resetting its password or
  changing its role logs that person out at their next click.
• 5 wrong passwords → that account is locked for 15 minutes.
• Temporary passwords must be changed at first login.
• Set-password links (invite a new staff member / forgot password), sent by
  e-mail when e-mail is set up, and always shown to the Doctor to copy
  (e.g. to send on WhatsApp). Links work once and expire.
• A login log (who logged in, failed tries, changes) for the Doctor.

SETTINGS (Render → dental-backend → Environment) — all optional
───────────────────
  MAIL_PROVIDER     off (default) | test (links written to the server log) | brevo
  BREVO_API_KEY     the Brevo "API key" (only in Render — never in chat or GitHub)
  MAIL_FROM         sender e-mail verified in Brevo, e.g. drramarajudentalclinic@gmail.com
  MAIL_FROM_NAME    e.g. Sri Satya Sai Dental
  APP_URL           the clinic app address (default https://dental-frontend-zp4w.onrender.com)
  AUTH_SESSION_HOURS  how long a login lasts (default 14)

Render's free plan blocks normal e-mail (SMTP) ports, so e-mail goes through
Brevo's web API instead (free: 300 e-mails a day).

New tables only (staff_accounts, auth_links, auth_log); the existing "user"
table is not changed.
"""
import hashlib
import json
import os
import re
import secrets
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

STAFF_ROLES = ("doctor", "reception", "admin")
CREATABLE_ROLES = ("doctor", "reception")
MAX_TRIES, LOCK_MINUTES = 5, 15
INVITE_HOURS, RESET_HOURS = 48, 2
CLINIC = "Sri Satya Sai Oral Health Center & Dental Clinic"
_DUMMY_HASH = generate_password_hash("not-a-real-password-" + secrets.token_hex(8))
DEFAULT_PASSWORDS = {"doctor1": "doctor123", "reception1": "reception123"}   # the old /setup accounts
# while a temporary password is being changed, only these work
CHANGE_ALLOWED = ("/api/auth/me", "/api/auth/change-password")
# no login needed (an old pass sent along by the browser is ignored here)
PUBLIC_AUTH = ("/api/auth/login", "/api/auth/link", "/api/auth/set-password", "/api/auth/forgot", "/api/auth/setup")


# ═════════════════════════════════════════════════════════════════════════════
#  TABLES (new; the "user" table itself is untouched)
# ═════════════════════════════════════════════════════════════════════════════
class StaffAccount(db.Model):
    __tablename__ = "staff_accounts"
    __table_args__ = {"extend_existing": True}
    user_id        = db.Column(db.Integer, primary_key=True)      # = user.id
    full_name      = db.Column(db.String(120))
    email          = db.Column(db.String(160))
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    active         = db.Column(db.Boolean, default=True, nullable=False)
    must_change    = db.Column(db.Boolean, default=False, nullable=False)
    token_version  = db.Column(db.Integer, default=1, nullable=False)
    failed         = db.Column(db.Integer, default=0, nullable=False)
    locked_until   = db.Column(db.DateTime)
    last_login_at  = db.Column(db.DateTime)
    password_set_at = db.Column(db.DateTime)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    created_by     = db.Column(db.String(80))


class AuthLink(db.Model):
    __tablename__ = "auth_links"
    __table_args__ = {"extend_existing": True}
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, nullable=False, index=True)
    kind       = db.Column(db.String(10), nullable=False)          # invite | reset
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at    = db.Column(db.DateTime)


class AuthLog(db.Model):
    __tablename__ = "auth_log"
    __table_args__ = {"extend_existing": True}
    id       = db.Column(db.Integer, primary_key=True)
    at       = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id  = db.Column(db.Integer, index=True)
    username = db.Column(db.String(80))
    action   = db.Column(db.String(40), nullable=False)
    ip       = db.Column(db.String(64))
    detail   = db.Column(db.String(255))


_ready = {"ok": False}
_lock = threading.Lock()


def run_auth_migrations(app=None):
    """Create the new tables and a staff row for every existing login."""
    def work():
        for m in (StaffAccount, AuthLink, AuthLog):
            m.__table__.create(bind=db.engine, checkfirst=True)
        have = {s.user_id for s in StaffAccount.query.all()}
        made = 0
        for u in User.query.all():
            if u.id in have:
                continue
            default = DEFAULT_PASSWORDS.get((u.username or "").lower())
            weak = bool(default and _safe_check(u.password, default))
            db.session.add(StaffAccount(user_id=u.id, full_name=None, active=True, must_change=weak,
                                        token_version=1, created_by="(existing)"))
            made += 1
        db.session.commit()
        _ready["ok"] = True
        if made:
            print(f"[auth] {made} existing login(s) set up for the new staff security")
    if app is not None:
        with app.app_context():
            work()
    else:
        work()


def _ensure():
    if _ready["ok"]:
        return
    with _lock:
        if not _ready["ok"]:
            run_auth_migrations()


# ═════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════════════
class AuthError(Exception):
    def __init__(self, message, status=400, code=None, **extra):
        super().__init__(message)
        self.message, self.status, self.code, self.extra = message, status, code, extra


@auth_bp.errorhandler(AuthError)
def _auth_error(e):
    body = {"error": e.message}
    if e.code:
        body["code"] = e.code
    body.update(e.extra)
    return jsonify(body), e.status


def _safe_check(hashed, pw):
    try:
        return check_password_hash(hashed or _DUMMY_HASH, pw or "")
    except Exception:
        return False


def _ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else (request.remote_addr or ""))[:64]


def _log(action, user=None, detail="", username=None):
    try:
        db.session.add(AuthLog(user_id=getattr(user, "id", None), username=(getattr(user, "username", None) or username or "")[:80],
                               action=action, ip=_ip(), detail=(detail or "")[:255]))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _now():
    return datetime.utcnow()


def _iso(dt):
    if not dt:
        return None
    ist = dt + timedelta(hours=5, minutes=30)
    return ist.strftime("%d %b %Y, %I:%M %p")


def _sec(user):
    s = db.session.get(StaffAccount, user.id)
    if s is None:
        s = StaffAccount(user_id=user.id, active=True, token_version=1, created_by="(auto)")
        db.session.add(s)
        db.session.flush()
    return s


def _find_user(username):
    name = (username or "").strip()
    if not name:
        return None
    return User.query.filter(func.lower(User.username) == name.lower()).first()


def check_password_rules(pw, username=""):
    pw = pw or ""
    if len(pw) < 8:
        raise AuthError("The password must have at least 8 characters.")
    if len(pw) > 128:
        raise AuthError("The password is too long.")
    low = pw.lower()
    if username and username.lower() in low:
        raise AuthError("The password must not contain the username.")
    if low in ("password", "password1", "12345678", "123456789", "1234567890", "qwerty123", "doctor123",
               "reception123", "abcd1234", "11111111", "00000000", "dental123", "clinic123"):
        raise AuthError("That password is too easy to guess. Please choose another.")
    if not (re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw)):
        raise AuthError("Use letters and at least one number.")


def _token_for(user, sec):
    hours = max(1, min(72, int(float(os.environ.get("AUTH_SESSION_HOURS") or 14))))
    return create_access_token(identity=str(user.id), expires_delta=timedelta(hours=hours),
                               additional_claims={"role": (user.role or "").strip().lower(), "tv": sec.token_version,
                                                  "name": user.username})


def _end_sessions(sec):
    sec.token_version = (sec.token_version or 1) + 1


def _role_of(user):
    return (user.role or "").strip().lower()


def _me():
    """The logged-in staff user (checked against the database), else 401."""
    try:
        verify_jwt_in_request()
    except Exception:
        raise AuthError("Please log in.", 401, "SESSION_ENDED")
    c = get_jwt() or {}
    if c.get("role") not in STAFF_ROLES:
        raise AuthError("Please log in.", 401, "SESSION_ENDED")
    ident = str(get_jwt_identity() or "")
    u = db.session.get(User, int(ident)) if ident.isdigit() else None
    if u is None:
        raise AuthError("Please log in.", 401, "SESSION_ENDED")
    return u, _sec(u)


def doctor_only(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u, s = _me()
        if _role_of(u) not in ("doctor", "admin"):
            raise AuthError("Only the Doctor can manage staff accounts.", 403)
        return fn(u, s, *a, **k)
    return wrapper


# ═════════════════════════════════════════════════════════════════════════════
#  E-MAIL (Brevo web API; Render's free plan blocks SMTP)
# ═════════════════════════════════════════════════════════════════════════════
def mail_mode():
    m = (os.environ.get("MAIL_PROVIDER") or "off").strip().lower()
    return m if m in ("off", "test", "brevo") else "off"


def _app_url():
    return (os.environ.get("APP_URL") or "https://dental-frontend-zp4w.onrender.com").rstrip("/")


def send_mail(to_email, to_name, subject, text, html):
    """True if sent (or written to the log in test mode)."""
    mode = mail_mode()
    if not to_email or mode == "off":
        return False
    if mode == "test":
        print(f"[auth] TEST MODE e-mail to {to_email}: {subject}\n{text}")
        return True
    key = (os.environ.get("BREVO_API_KEY") or "").strip()
    sender = (os.environ.get("MAIL_FROM") or "").strip()
    if not key or not sender:
        print("[auth] e-mail not sent: BREVO_API_KEY or MAIL_FROM is missing")
        return False
    body = json.dumps({
        "sender": {"email": sender, "name": os.environ.get("MAIL_FROM_NAME") or "Sri Satya Sai Dental"},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject, "textContent": text, "htmlContent": html,
    }).encode()
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=body, method="POST",
                                 headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        print("[auth] e-mail failed:", e.code, e.read(300).decode("utf-8", "replace"))
    except Exception as e:
        print("[auth] e-mail failed:", type(e).__name__, str(e)[:200])
    return False


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _link_mail(user, sec, kind, link):
    name = sec.full_name or user.username
    if kind == "invite":
        subject = f"{CLINIC}: set your password"
        lead = (f"You have been added to the clinic app as {_role_of(user).title()}. "
                f"Your username is {user.username}. Click the button to set your password.")
        hours = INVITE_HOURS
    else:
        subject = f"{CLINIC}: reset your password"
        lead = f"A password reset was asked for the username {user.username}. Click the button to choose a new password."
        hours = RESET_HOURS
    text = f"Hello {name},\n\n{lead}\n\n{link}\n\nThe link works once and expires in {hours} hours. If you did not expect this e-mail, ignore it.\n\n{CLINIC}"
    html = (f"<div style=\"font-family:Arial,sans-serif;font-size:15px;color:#1d2b2d;max-width:520px\">"
            f"<p>Hello {_esc(name)},</p><p>{_esc(lead)}</p>"
            f"<p><a href=\"{_esc(link)}\" style=\"display:inline-block;background:#0f3d3e;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold\">"
            f"{'Set my password' if kind == 'invite' else 'Choose a new password'}</a></p>"
            f"<p style=\"color:#667\">The link works once and expires in {hours} hours. If you did not expect this e-mail, ignore it.</p>"
            f"<p style=\"color:#667\">{_esc(CLINIC)}</p></div>")
    return send_mail(sec.email, name, subject, text, html)


def _new_link(user, kind):
    """A fresh single-use link; older unused links of the same person stop working."""
    for old in AuthLink.query.filter(AuthLink.user_id == user.id, AuthLink.used_at.is_(None)).all():
        old.used_at = _now()
    token = secrets.token_urlsafe(32)
    hours = INVITE_HOURS if kind == "invite" else RESET_HOURS
    db.session.add(AuthLink(user_id=user.id, kind=kind, token_hash=_hash(token), expires_at=_now() + timedelta(hours=hours)))
    return f"{_app_url()}/login?{'invite' if kind == 'invite' else 'reset'}={token}"


# ═════════════════════════════════════════════════════════════════════════════
#  REAL-TIME CHECK ON EVERY REQUEST
# ═════════════════════════════════════════════════════════════════════════════
@auth_bp.before_app_request
def _staff_session_still_valid():
    if request.method == "OPTIONS" or request.path in PUBLIC_AUTH:
        return None
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
    except Exception:
        return None            # no / bad / expired pass: the app's own gate answers that
    role = claims.get("role")
    if role not in STAFF_ROLES:
        return None            # patient-portal logins are checked by portal.py
    try:
        _ensure()
        ident = str(get_jwt_identity() or "")
        u = db.session.get(User, int(ident)) if ident.isdigit() else None
        s = db.session.get(StaffAccount, u.id) if u is not None else None
    except Exception as e:
        db.session.rollback()
        print("[auth] session check failed:", type(e).__name__, str(e)[:200])
        return jsonify({"error": "The server is busy. Please try again in a moment."}), 503
    ended = (u is None or s is None or not s.active or claims.get("tv") != s.token_version
             or _role_of(u) != role)
    if ended:
        msg = ("This account has been switched off. Please contact the doctor." if (s is not None and not s.active)
               else "Your login has ended. Please log in again.")
        return jsonify({"error": "Unauthorized", "code": "SESSION_ENDED", "message": msg}), 401
    if s.must_change and request.path not in CHANGE_ALLOWED:
        return jsonify({"error": "Please set a new password first.", "code": "PASSWORD_CHANGE_REQUIRED"}), 403
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ═════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/login", methods=["POST"])
def login():
    _ensure()
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    now = _now()
    if AuthLog.query.filter(AuthLog.ip == _ip(), AuthLog.action == "login_failed",
                            AuthLog.at >= now - timedelta(hours=1)).count() >= 40:
        return jsonify({"error": "Too many wrong tries from this network. Please wait an hour."}), 429
    user = _find_user(username)
    if user is None:
        _safe_check(None, password)                  # same time as a real check
        _log("login_failed", None, "unknown username", username)
        return jsonify({"error": "Invalid credentials"}), 401
    sec = _sec(user)
    if sec.locked_until and sec.locked_until > now:
        mins = max(1, int((sec.locked_until - now).total_seconds() // 60) + 1)
        _log("login_blocked", user, "locked")
        return jsonify({"error": f"Too many wrong passwords. This account is locked for {mins} more minute{'s' if mins != 1 else ''}.",
                        "code": "LOCKED"}), 429
    if not _safe_check(user.password, password):
        sec.failed = (sec.failed or 0) + 1
        detail = f"wrong password ({sec.failed}/{MAX_TRIES})"
        if sec.failed >= MAX_TRIES:
            sec.locked_until, sec.failed = now + timedelta(minutes=LOCK_MINUTES), 0
            detail = f"locked for {LOCK_MINUTES} minutes"
        db.session.commit()
        _log("login_failed", user, detail)
        if sec.locked_until and sec.locked_until > now:
            return jsonify({"error": f"Too many wrong passwords. This account is locked for {LOCK_MINUTES} minutes.", "code": "LOCKED"}), 429
        return jsonify({"error": "Invalid credentials", "tries_left": MAX_TRIES - sec.failed}), 401
    if not sec.active:
        _log("login_blocked", user, "account switched off")
        return jsonify({"error": "This account is switched off. Please contact the doctor.", "code": "DISABLED"}), 403
    sec.failed, sec.locked_until, sec.last_login_at = 0, None, now
    db.session.commit()
    _log("login", user)
    return jsonify({
        "access_token": _token_for(user, sec),
        "user_id": user.id,
        "username": user.username,
        "full_name": sec.full_name or user.username,
        "role": user.role,
        "must_change_password": bool(sec.must_change),
    }), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    u, s = _me()
    return jsonify({"user_id": u.id, "username": u.username, "full_name": s.full_name or u.username, "role": u.role,
                    "email": s.email, "must_change_password": bool(s.must_change)})


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    u, s = _me()
    data = request.get_json(silent=True) or {}
    if not _safe_check(u.password, data.get("current_password") or ""):
        _log("password_change_failed", u, "current password wrong")
        raise AuthError("The current password is not right.", 400)
    new = data.get("new_password") or ""
    check_password_rules(new, u.username)
    if _safe_check(u.password, new):
        raise AuthError("Please choose a password different from the current one.")
    u.password = generate_password_hash(new)
    s.must_change, s.password_set_at = False, _now()
    _end_sessions(s)                                  # other devices are logged out; this tab gets a new pass
    db.session.commit()
    _log("password_changed", u)
    return jsonify({"ok": True, "access_token": _token_for(u, s), "role": u.role, "username": u.username,
                    "full_name": s.full_name or u.username})


# ═════════════════════════════════════════════════════════════════════════════
#  SET-PASSWORD LINKS (invite + forgot password) — no login needed
# ═════════════════════════════════════════════════════════════════════════════
def _link_row(token):
    if not token or len(token) > 100:
        return None
    row = AuthLink.query.filter_by(token_hash=_hash(token)).first()
    if row is None or row.used_at is not None or row.expires_at <= _now():
        return None
    return row


@auth_bp.route("/link", methods=["GET"])
def link_info():
    _ensure()
    row = _link_row(request.args.get("token", ""))
    u = db.session.get(User, row.user_id) if row else None
    s = db.session.get(StaffAccount, row.user_id) if row else None
    if not row or u is None or s is None or not s.active:
        raise AuthError("This link has expired or was already used. Ask the doctor for a new one, or use “Forgot password?”.", 410)
    return jsonify({"kind": row.kind, "username": u.username, "full_name": s.full_name or u.username, "role": u.role})


@auth_bp.route("/set-password", methods=["POST"])
def set_password_from_link():
    _ensure()
    data = request.get_json(silent=True) or {}
    row = _link_row(data.get("token", ""))
    u = db.session.get(User, row.user_id) if row else None
    s = db.session.get(StaffAccount, row.user_id) if row else None
    if not row or u is None or s is None or not s.active:
        raise AuthError("This link has expired or was already used. Ask the doctor for a new one, or use “Forgot password?”.", 410)
    pw = data.get("password") or ""
    check_password_rules(pw, u.username)
    u.password = generate_password_hash(pw)
    s.must_change, s.failed, s.locked_until, s.password_set_at = False, 0, None, _now()
    if s.email:
        s.email_verified = True          # they opened the e-mailed link (or the doctor's copy)
    _end_sessions(s)
    row.used_at = _now()
    db.session.commit()
    _log("password_set_by_link", u, row.kind)
    return jsonify({"ok": True, "username": u.username, "role": u.role})


@auth_bp.route("/forgot", methods=["POST"])
def forgot():
    _ensure()
    data = request.get_json(silent=True) or {}
    who = (data.get("username") or data.get("email") or "").strip()
    generic = {"ok": True, "message": "If this account has an e-mail address, a reset link has been sent. "
                                      "No e-mail? Ask the doctor to reset your password."}
    if not who:
        raise AuthError("Enter your username or e-mail.")
    now = _now()
    if AuthLog.query.filter(AuthLog.ip == _ip(), AuthLog.action == "reset_asked", AuthLog.at >= now - timedelta(hours=1)).count() >= 10:
        return jsonify(generic)
    u = _find_user(who)
    if u is None and "@" in who:
        s = StaffAccount.query.filter(func.lower(StaffAccount.email) == who.lower()).first()
        u = db.session.get(User, s.user_id) if s else None
    _log("reset_asked", u, "", who[:80])
    if u is None:
        return jsonify(generic)
    s = _sec(u)
    recent = AuthLink.query.filter(AuthLink.user_id == u.id, AuthLink.kind == "reset",
                                   AuthLink.created_at >= now - timedelta(minutes=15)).count()
    if not s.active or not s.email or recent >= 3 or mail_mode() == "off":
        return jsonify(generic)
    link = _new_link(u, "reset")
    db.session.commit()
    _link_mail(u, s, "reset", link)
    return jsonify(generic)


# ═════════════════════════════════════════════════════════════════════════════
#  STAFF ACCOUNTS (Doctor only)
# ═════════════════════════════════════════════════════════════════════════════
def _staff_json(u, s):
    now = _now()
    pending = AuthLink.query.filter(AuthLink.user_id == u.id, AuthLink.used_at.is_(None), AuthLink.expires_at > now).first()
    return {
        "user_id": u.id, "username": u.username, "full_name": s.full_name or "", "role": _role_of(u),
        "email": s.email or "", "email_verified": bool(s.email_verified), "active": bool(s.active),
        "must_change_password": bool(s.must_change), "locked": bool(s.locked_until and s.locked_until > now),
        "last_login": _iso(s.last_login_at), "link_pending": pending.kind if pending else None,
        "created_at": _iso(s.created_at), "created_by": s.created_by or "",
    }


def _valid_email(e):
    e = (e or "").strip()
    if not e:
        return ""
    if len(e) > 160 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", e):
        raise AuthError("That e-mail address does not look right.")
    return e


def _active_doctors_except(uid):
    n = 0
    for u in User.query.filter(func.lower(User.role).in_(("doctor", "admin"))).all():
        s = db.session.get(StaffAccount, u.id)
        if u.id != uid and (s is None or s.active):
            n += 1
    return n


@auth_bp.route("/staff", methods=["GET"])
@doctor_only
def staff_list(me, _s):
    rows = [(u, _sec(u)) for u in User.query.order_by(User.id).all()]
    db.session.commit()
    return jsonify({"staff": [_staff_json(u, s) for u, s in rows], "me": me.id, "mail": mail_mode(),
                    "app_url": _app_url()})


def _create(me, data):
    full_name = (data.get("full_name") or "").strip()[:120]
    username = (data.get("username") or "").strip()
    role = (data.get("role") or "reception").strip().lower()
    email = _valid_email(data.get("email"))
    temp = data.get("password") or data.get("temp_password") or ""
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,40}", username or ""):
        raise AuthError("Username: 3–40 letters or numbers (dots, dashes and underscores are fine, no spaces).")
    if role not in CREATABLE_ROLES:
        raise AuthError("Role must be Doctor or Reception.")
    if _find_user(username):
        raise AuthError("That username is already taken.", 409)
    if email and StaffAccount.query.filter(func.lower(StaffAccount.email) == email.lower()).first():
        raise AuthError("Another account already uses that e-mail address.", 409)
    if temp:
        check_password_rules(temp, username)
    u = User(username=username, password=generate_password_hash(temp or secrets.token_urlsafe(24)), role=role)
    db.session.add(u)
    db.session.flush()
    s = StaffAccount(user_id=u.id, full_name=full_name or None, email=email or None, active=True,
                     must_change=bool(temp), token_version=1, created_by=me.username)
    db.session.add(s)
    link = sent = None
    if not temp:
        link = _new_link(u, "invite")
    db.session.commit()
    if link:
        sent = _link_mail(u, s, "invite", link)
    _log("staff_added", u, f"{role} by {me.username}")
    return u, s, link, sent


@auth_bp.route("/staff", methods=["POST"])
@doctor_only
def staff_add(me, _s):
    u, s, link, sent = _create(me, request.get_json(silent=True) or {})
    return jsonify({"staff": _staff_json(u, s), "link": link, "emailed": bool(sent)}), 201


@auth_bp.route("/staff/<int:uid>", methods=["PUT"])
@doctor_only
def staff_edit(me, _s, uid):
    u = db.session.get(User, uid)
    if u is None:
        raise AuthError("This account no longer exists.", 404)
    s = _sec(u)
    data = request.get_json(silent=True) or {}
    if "full_name" in data:
        s.full_name = (data.get("full_name") or "").strip()[:120] or None
    if "email" in data:
        e = _valid_email(data.get("email"))
        if e and StaffAccount.query.filter(func.lower(StaffAccount.email) == e.lower(), StaffAccount.user_id != uid).first():
            raise AuthError("Another account already uses that e-mail address.", 409)
        if (e or None) != s.email:
            s.email, s.email_verified = e or None, False
    if "role" in data:
        role = (data.get("role") or "").strip().lower()
        if role not in CREATABLE_ROLES:
            raise AuthError("Role must be Doctor or Reception.")
        if role != _role_of(u):
            if uid == me.id:
                raise AuthError("You cannot change your own role.")
            if _role_of(u) in ("doctor", "admin") and _active_doctors_except(uid) == 0:
                raise AuthError("There must always be at least one Doctor account.")
            u.role = role
            _end_sessions(s)
    db.session.commit()
    _log("staff_edited", u, f"by {me.username}")
    return jsonify({"staff": _staff_json(u, s)})


@auth_bp.route("/staff/<int:uid>/active", methods=["POST"])
@doctor_only
def staff_active(me, _s, uid):
    u = db.session.get(User, uid)
    if u is None:
        raise AuthError("This account no longer exists.", 404)
    s = _sec(u)
    on = bool((request.get_json(silent=True) or {}).get("active"))
    if not on:
        if uid == me.id:
            raise AuthError("You cannot switch off your own account.")
        if _role_of(u) in ("doctor", "admin") and _active_doctors_except(uid) == 0:
            raise AuthError("There must always be at least one active Doctor account.")
        s.active = False
        _end_sessions(s)                    # logged out at their next click
    else:
        s.active, s.failed, s.locked_until = True, 0, None
    db.session.commit()
    _log("staff_switched_on" if on else "staff_switched_off", u, f"by {me.username}")
    return jsonify({"staff": _staff_json(u, s)})


@auth_bp.route("/staff/<int:uid>/unlock", methods=["POST"])
@doctor_only
def staff_unlock(me, _s, uid):
    u = db.session.get(User, uid)
    if u is None:
        raise AuthError("This account no longer exists.", 404)
    s = _sec(u)
    s.failed, s.locked_until = 0, None
    db.session.commit()
    _log("staff_unlocked", u, f"by {me.username}")
    return jsonify({"staff": _staff_json(u, s)})


@auth_bp.route("/staff/<int:uid>/reset", methods=["POST"])
@doctor_only
def staff_reset(me, _s, uid):
    """Either a set-password link (copied / e-mailed) or a temporary password.
    Both log the person out everywhere."""
    u = db.session.get(User, uid)
    if u is None:
        raise AuthError("This account no longer exists.", 404)
    s = _sec(u)
    data = request.get_json(silent=True) or {}
    temp = data.get("temp_password") or ""
    link = sent = None
    if temp:
        if uid == me.id:
            raise AuthError("Use “Change my password” for your own account.")
        check_password_rules(temp, u.username)
        u.password = generate_password_hash(temp)
        s.must_change = True
        for old in AuthLink.query.filter(AuthLink.user_id == u.id, AuthLink.used_at.is_(None)).all():
            old.used_at = _now()
    else:
        link = _new_link(u, "invite" if not s.last_login_at else "reset")
    s.failed, s.locked_until = 0, None
    if uid != me.id:
        _end_sessions(s)
    db.session.commit()
    if link and data.get("email", True):
        sent = _link_mail(u, s, "invite" if not s.last_login_at else "reset", link)
    _log("staff_password_reset", u, f"by {me.username} ({'temporary password' if temp else 'link'})")
    return jsonify({"staff": _staff_json(u, s), "link": link, "emailed": bool(sent)})


@auth_bp.route("/staff/log", methods=["GET"])
@doctor_only
def staff_log(me, _s):
    try:
        limit = max(10, min(300, int(request.args.get("limit", 80))))
    except ValueError:
        limit = 80
    rows = AuthLog.query.order_by(AuthLog.id.desc()).limit(limit).all()
    return jsonify({"log": [{"at": _iso(r.at), "username": r.username, "action": r.action, "ip": r.ip, "detail": r.detail}
                            for r in rows]})


# ═════════════════════════════════════════════════════════════════════════════
#  OLD ADDRESSES — closed
# ═════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/register", methods=["POST"])
@doctor_only
def register(me, _s):
    """Kept for old callers, but now Doctor-only (the 👥 Staff screen is the normal way)."""
    data = request.get_json(silent=True) or {}
    if not data.get("password"):
        raise AuthError("Username and password required")
    _create(me, data)
    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route("/setup", methods=["GET"])
def setup():
    return jsonify({"error": "This address is closed. The doctor adds staff from the 👥 Staff screen."}), 410