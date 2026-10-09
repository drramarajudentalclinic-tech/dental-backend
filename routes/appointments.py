"""
APPOINTMENTS — kept in Supabase (the same `appointments` table the Appointments
app uses), linked to this clinic's patients.
──────────────────────────────────────────────────────────────────────────────
The old "Appointments Diary" table of this app is no longer used. Every
appointment now lives in ONE place — Supabase `public.appointments` — so the
Appointments app, Reception, the Doctor and (later) the patient portal all see
the same list.

Settings (Render → dental-backend → Environment):
    SUPABASE_URL               https://<project>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY  the secret key (Project Settings → API Keys: "service_role"
                               or a "Secret key" sb_secret_…)
The key stays on the server; the website never sees it.

Columns used in Supabase (existing):  id, name, mobile, appointment_date,
    appointment_time, doctor_name, age, treatment, case_no, status
    (SCHEDULED / COMPLETED / CANCELLED), created_by, created_at, updated_at
Columns added for the link (see the SQL step):  patient_id, visit_id, source, notes

Addresses (all under /api, all need a login):
    GET    /appointments                     list  ?date=YYYY-MM-DD | ?from=&to= | ?patient_id= | ?visit_id= | ?status=
    POST   /appointments                     book  {patient_id | name+mobile+case_number, date, time, treatment, notes, ...}
    PUT    /appointments/<id>                change date / time / treatment / notes / status
    DELETE /appointments/<id>                cancel (status CANCELLED — the row is kept)
    POST   /appointments/<id>/link           {patient_id}  link a booking to a patient of this clinic
    GET    /patients/<pid>/appointments      {upcoming:[...], past:[...]}  (history screen, patient portal)
    GET    /appointments/connection          is Supabase connected?

Automatic updates (no screen has to remember to do it):
    • The doctor enters a next-appointment / follow-up date (consultation,
      prescription, or the visit's next appointment) → the patient is booked
      for that date and time. Saved again with another date → the booking
      MOVES (no second booking). Date removed → the booking is cancelled.
      Already booked that day (by anyone, also in the Appointments app) → the
      same booking is used (time updated), never a duplicate.
    • The visit is closed → the patient's appointment of that day becomes
      COMPLETED.
    • A booking made in the Appointments app is linked to the patient
      automatically by case number (or by mobile number + name).
Answers keep the old shape (appt_id, name, date, time, mobile, case_number,
treatment, notes, status "pending"/"completed"/"cancelled"), so every screen
that read the old diary keeps working.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request

from database import db

try:
    from models import Patient, Visit
except Exception:                                   # pragma: no cover
    from routes.models import Patient, Visit        # type: ignore

try:
    from auth_utils import require_login
except ImportError:
    try:
        from routes.auth_utils import require_login
    except ImportError:                              # pragma: no cover
        def require_login(fn):
            return fn

appointments_bp = Blueprint("appointments", __name__)


class Appointment(db.Model):
    """The OLD diary table of this app — no longer used (appointments are in Supabase).
    Kept only so that any file that still imports it keeps working; nothing reads it."""
    __tablename__ = "appointments"
    __table_args__ = {"extend_existing": True}
    appt_id     = db.Column(db.String(36), primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    date        = db.Column(db.String(20), nullable=False)
    time        = db.Column(db.String(10))
    mobile      = db.Column(db.String(20))
    case_number = db.Column(db.String(50))
    treatment   = db.Column(db.String(200))
    notes       = db.Column(db.Text)
    status      = db.Column(db.String(20), nullable=False, default="pending")

IST = timezone(timedelta(hours=5, minutes=30))
STATUS_IN = {"pending": "SCHEDULED", "scheduled": "SCHEDULED", "booked": "SCHEDULED",
             "completed": "COMPLETED", "done": "COMPLETED",
             "cancelled": "CANCELLED", "canceled": "CANCELLED"}
STATUS_OUT = {"SCHEDULED": "pending", "COMPLETED": "completed", "CANCELLED": "cancelled"}
FOLLOW_UP_SOURCES = ("consultation", "prescription", "visit", "follow-up")
ACTIVE_VISIT = ("CREATED", "IN_PROGRESS", "REOPENED")


class ApptError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


def today_ist():
    return datetime.now(IST).date()


# ═════════════════════════════════════════════════════════════════════
#  Supabase (PostgREST) — tiny client, standard library only
# ═════════════════════════════════════════════════════════════════════
def _settings():
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()
    table = (os.environ.get("SUPABASE_APPOINTMENTS_TABLE") or "appointments").strip()
    return url, key, table


def configured():
    url, key, _ = _settings()
    return bool(url and key)


_columns_cache = {"cols": None}


def _call(method, query="", body=None, prefer=None, timeout=12):
    url, key, table = _settings()
    if not (url and key):
        raise ApptError("Appointments are not connected yet: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                        "must be added in Render (Environment).", 503)
    full = f"{url}/rest/v1/{table}" + (f"?{query}" if query else "")
    headers = {"apikey": key, "Accept": "application/json"}
    if key.startswith("eyJ"):            # the older "service_role" key (a JWT) is also sent as Bearer;
        headers["Authorization"] = f"Bearer {key}"   # the newer "sb_secret_…" keys go in apikey only
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(full, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        print(f"[appointments] Supabase {method} {e.code}: {detail}")
        msg = "The appointment could not be saved in Supabase."
        try:
            j = json.loads(detail)
            text = " ".join(str(j.get(k) or "") for k in ("message", "details", "hint")).strip()
            if "status_check" in text:
                msg = "Supabase refused the status. Allowed: SCHEDULED, COMPLETED, CANCELLED."
            elif "age_check" in text:
                msg = "Supabase refused the age (it must be 0–120)."
            elif "column" in text and ("patient_id" in text or "visit_id" in text or "source" in text or "notes" in text):
                msg = "Supabase is missing the new columns — please run the SQL step (patient_id, visit_id, source, notes)."
            elif text:
                msg = f"Supabase: {text}"
        except ValueError:
            pass
        raise ApptError(msg, 502)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[appointments] Supabase unreachable: {e}")
        raise ApptError("Supabase could not be reached. Please check the internet connection and try again.", 502)


def _q(**filters):
    """PostgREST query string. Values are already 'op.value' strings."""
    parts = []
    for k, v in filters.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            for item in v:
                parts.append((k, item))
        else:
            parts.append((k, v))
    return urllib.parse.urlencode(parts, safe=",.():*")


def sb_select(**filters):
    filters.setdefault("select", "*")
    filters.setdefault("order", "appointment_date.asc,appointment_time.asc")
    return _call("GET", _q(**filters)) or []


def sb_get(appt_id):
    rows = sb_select(id=f"eq.{appt_id}")
    if not rows:
        raise ApptError("This appointment no longer exists.", 404)
    return rows[0]


def sb_insert(row):
    out = _call("POST", "", row, prefer="return=representation")
    return out[0] if isinstance(out, list) and out else out


def sb_update(appt_id, changes):
    out = _call("PATCH", _q(id=f"eq.{appt_id}"), changes, prefer="return=representation")
    if not out:
        raise ApptError("This appointment no longer exists.", 404)
    return out[0]


# ═════════════════════════════════════════════════════════════════════
#  Helpers: clean values, patients, visits
# ═════════════════════════════════════════════════════════════════════
def _date(value, field="date", required=True):
    s = str(value or "").strip()[:10]
    if not s:
        if required:
            raise ApptError(f"Please choose the {field}.")
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ApptError(f"The {field} must look like 2026-10-14.")


def _time(value, required=False):
    s = str(value or "").strip()
    if not s:
        if required:
            raise ApptError("Please choose the time.")
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp][Mm])?$", s)
    if not m:
        raise ApptError("The time must look like 10:30.")
    h, mi = int(m.group(1)), int(m.group(2))
    ap = (m.group(3) or "").lower()
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        raise ApptError("The time must look like 10:30.")
    return f"{h:02d}:{mi:02d}"


def _text(value, n=300):
    s = " ".join(str(value or "").split())
    return s[:n] or None


def _status(value):
    if value in (None, ""):
        return None
    s = STATUS_IN.get(str(value).strip().lower())
    if not s:
        raise ApptError("Status must be Scheduled, Completed or Cancelled.")
    return s


def _digits(mobile):
    d = re.sub(r"\D", "", str(mobile or ""))
    return d[-10:] if len(d) >= 10 else d


def _norm_case(c):
    return re.sub(r"\s+", "", str(c or "")).upper()


def _norm_name(n):
    return " ".join(str(n or "").lower().split())


def _same_person(a, b):
    a, b = _norm_name(a), _norm_name(b)
    if not a or not b:
        return False
    return a == b or a.split()[0] == b.split()[0] or a in b or b in a


def _patient(pid):
    p = db.session.get(Patient, int(pid)) if str(pid or "").isdigit() else None
    if p is None:
        raise ApptError("This patient was not found.", 404)
    return p


def _patient_fields(p):
    age = p.age if isinstance(p.age, int) and 0 <= p.age <= 120 else None
    return {"patient_id": p.id, "name": (p.name or "").strip() or "Patient", "mobile": (p.mobile or "").strip() or None,
            "case_no": (p.case_number or "").strip() or None, "age": age}


def _actor_name():
    try:
        try:
            from medical_history import current_actor
        except ImportError:
            from routes.medical_history import current_actor
        return str((current_actor() or {}).get("name") or "").strip() or None
    except Exception:
        return None


def _match_patients(rows):
    """Links rows booked in the Appointments app (no patient_id yet) to this clinic's
    patients: same case number, or same mobile number and the same (first) name.
    Returns {appt_id: patient}."""
    todo = [r for r in rows if not r.get("patient_id")]
    if not todo:
        return {}
    cases = {_norm_case(r.get("case_no")) for r in todo if r.get("case_no")}
    mobiles = {_digits(r.get("mobile")) for r in todo if len(_digits(r.get("mobile"))) == 10}
    by_case, by_mobile = {}, {}
    if cases:
        for p in Patient.query.filter(db.func.upper(db.func.replace(Patient.case_number, " ", "")).in_(list(cases))).all():
            by_case[_norm_case(p.case_number)] = p
    if mobiles:
        likes = [Patient.mobile.like(f"%{m}") for m in mobiles]
        for p in Patient.query.filter(db.or_(*likes)).all():
            by_mobile.setdefault(_digits(p.mobile), []).append(p)
    found = {}
    for r in todo:
        p = by_case.get(_norm_case(r.get("case_no"))) if r.get("case_no") else None
        if p is None:
            # a mobile is often shared by a family: the name must agree too
            cands = [c for c in by_mobile.get(_digits(r.get("mobile")), []) if _same_person(c.name, r.get("name"))]
            if len(cands) > 1:
                cands = [c for c in cands if _norm_name(c.name) == _norm_name(r.get("name"))]
            p = cands[0] if len(cands) == 1 else None
        if p is not None:
            found[r["id"]] = p
    return found


def _visit_state(patient_ids):
    """{patient_id: {"active": visit_id|None, "closed_today": visit_id|None}} for today (IST)."""
    out = {}
    if not patient_ids:
        return out
    start = datetime.combine(today_ist(), datetime.min.time()) - timedelta(hours=5, minutes=30)   # IST midnight in UTC
    rows = (Visit.query.filter(Visit.patient_id.in_(list(patient_ids)))
            .filter(Visit.visit_date >= start - timedelta(days=1))
            .order_by(Visit.id.desc()).all())
    for v in rows:
        st = (v.status or "").upper()
        d = out.setdefault(v.patient_id, {"active": None, "closed_today": None})
        if st in ACTIVE_VISIT and d["active"] is None:
            d["active"] = v.id
        elif st in ("CLOSED", "COMPLETED", "READY_FOR_BILLING") and v.visit_date and v.visit_date >= start and d["closed_today"] is None:
            d["closed_today"] = v.id
    return out


def _out(r, visit_state=None):
    """Supabase row → the answer shape every screen understands."""
    t = str(r.get("appointment_time") or "")[:5]
    st = str(r.get("status") or "SCHEDULED").upper()
    pid = r.get("patient_id")
    vs = (visit_state or {}).get(pid) or {}
    is_today = str(r.get("appointment_date") or "")[:10] == today_ist().isoformat()
    source = r.get("source") or ("appointments-app" if r.get("created_by") else None)
    return {
        "appt_id": r.get("id"), "id": r.get("id"),
        "name": r.get("name") or "", "date": str(r.get("appointment_date") or "")[:10], "time": t,
        "mobile": r.get("mobile") or "", "case_number": r.get("case_no") or "", "age": r.get("age"),
        "treatment": r.get("treatment") or "", "notes": r.get("notes") or "", "doctor_name": r.get("doctor_name") or "",
        "status": STATUS_OUT.get(st, st.lower()), "state": st,
        "patient_id": pid, "visit_id": r.get("visit_id"), "source": source,
        "linked": bool(pid),
        "in_clinic_visit_id": vs.get("active") if (is_today and st == "SCHEDULED") else None,
        "created_at": r.get("created_at"), "updated_at": r.get("updated_at"),
    }


def _with_links(rows):
    """Link what can be linked (saved back to Supabase once), then shape the answer."""
    found = _match_patients(rows)
    for r in rows:
        p = found.get(r.get("id"))
        if p is None:
            continue
        r["patient_id"] = p.id
        ch = {"patient_id": p.id}
        if not r.get("case_no") and p.case_number:      # the Appointments app then shows the case number too
            ch["case_no"] = r["case_no"] = p.case_number
        try:
            sb_update(r["id"], ch)
        except ApptError as e:
            print("[appointments] could not save the patient link:", e.message)
    state = _visit_state({r["patient_id"] for r in rows if r.get("patient_id")})
    return [_out(r, state) for r in rows]


def _guard(fn):
    from functools import wraps

    @wraps(fn)
    def wrapped(*a, **kw):
        try:
            return fn(*a, **kw)
        except ApptError as e:
            return jsonify({"error": e.message}), e.status
    return wrapped


# ═════════════════════════════════════════════════════════════════════
#  Booking a follow-up — used by the screens AND by the automatic updates
# ═════════════════════════════════════════════════════════════════════
def book_follow_up(patient, new_date, new_time=None, old_date=None, visit_id=None, source="visit",
                   treatment=None, notes=None, doctor=None):
    """One booking per patient per day. Returns (row, "created"|"updated"|"moved"|"kept")."""
    pf = _patient_fields(patient)
    same_day = sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{new_date}", status="eq.SCHEDULED")
    if not same_day:      # booked in the Appointments app but not linked yet
        cand = sb_select(appointment_date=f"eq.{new_date}", status="eq.SCHEDULED", patient_id="is.null")
        found = _match_patients(cand)
        same_day = [r for r in cand if found.get(r["id"]) is not None and found[r["id"]].id == patient.id]
    if same_day:
        row = same_day[0]
        changes = {}
        if not row.get("patient_id"):
            changes["patient_id"] = patient.id
        if new_time and str(row.get("appointment_time") or "")[:5] != new_time:
            changes["appointment_time"] = new_time
        if visit_id and not row.get("visit_id"):
            changes["visit_id"] = visit_id
        if treatment and not row.get("treatment"):
            changes["treatment"] = treatment
        if doctor and not row.get("doctor_name"):
            changes["doctor_name"] = doctor
        if not changes:
            return row, "kept"
        return sb_update(row["id"], changes), "updated"

    if old_date and old_date != new_date:
        old = sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{old_date}", status="eq.SCHEDULED",
                        source=f"in.({','.join(FOLLOW_UP_SOURCES)})")
        if old:
            changes = {"appointment_date": new_date}
            if new_time:
                changes["appointment_time"] = new_time
            if visit_id:
                changes["visit_id"] = visit_id
            return sb_update(old[0]["id"], changes), "moved"

    row = {**pf, "appointment_date": new_date, "appointment_time": new_time or "11:00",
           "treatment": treatment or "Follow-up", "notes": notes, "status": "SCHEDULED",
           "visit_id": visit_id, "source": source, "doctor_name": doctor}
    return sb_insert(row), "created"


def cancel_follow_up(patient, old_date, reason="Follow-up date removed by the doctor"):
    rows = sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{old_date}", status="eq.SCHEDULED",
                     source=f"in.({','.join(FOLLOW_UP_SOURCES)})")
    for r in rows:
        sb_update(r["id"], {"status": "CANCELLED", "notes": _text(f"{r.get('notes') or ''} · {reason}".strip(" ·"))})
    return len(rows)


def complete_today(patient, visit_id=None):
    day = today_ist().isoformat()
    rows = sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{day}", status="eq.SCHEDULED")
    if not rows:
        cand = sb_select(appointment_date=f"eq.{day}", status="eq.SCHEDULED", patient_id="is.null")
        found = _match_patients(cand)
        rows = [r for r in cand if found.get(r["id"]) is not None and found[r["id"]].id == patient.id]
    for r in rows:
        ch = {"status": "COMPLETED", "patient_id": patient.id}
        if visit_id and not r.get("visit_id"):
            ch["visit_id"] = visit_id
        sb_update(r["id"], ch)
    return len(rows)


# ═════════════════════════════════════════════════════════════════════
#  Addresses
# ═════════════════════════════════════════════════════════════════════
@appointments_bp.route("/appointments/connection", methods=["GET"])
@require_login
def connection():
    if not configured():
        return jsonify({"connected": False, "message": "Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Render."}), 200
    try:
        _call("GET", _q(select="id", limit="1"))
        return jsonify({"connected": True}), 200
    except ApptError as e:
        return jsonify({"connected": False, "message": e.message}), 200


@appointments_bp.route("/appointments", methods=["GET"])
@require_login
@_guard
def list_appointments():
    a = request.args
    f = {}
    if a.get("date"):
        f["appointment_date"] = f"eq.{_date(a['date'])}"
    else:
        lo = _date(a.get("from"), required=False)
        hi = _date(a.get("to"), required=False)
        if not lo and not hi and not a.get("patient_id") and not a.get("visit_id"):
            lo = (today_ist() - timedelta(days=400)).isoformat()      # old screens ask for "everything"
        conds = []
        if lo:
            conds.append(f"appointment_date.gte.{lo}")
        if hi:
            conds.append(f"appointment_date.lte.{hi}")
        if len(conds) == 2:
            f["and"] = f"({','.join(conds)})"
        elif conds:
            k, op, v = conds[0].split(".", 2)
            f["appointment_date"] = f"{op}.{v}"
    if a.get("patient_id"):
        f["patient_id"] = f"eq.{int(a['patient_id'])}"
    if a.get("visit_id"):
        f["visit_id"] = f"eq.{int(a['visit_id'])}"
    if a.get("status"):
        f["status"] = f"eq.{_status(a['status'])}"
    order = "appointment_date.desc,appointment_time.desc" if a.get("order") == "desc" else None
    rows = sb_select(**f, **({"order": order} if order else {}))
    return jsonify(_with_links(rows)), 200


@appointments_bp.route("/patients/<int:pid>/appointments", methods=["GET"])
@require_login
@_guard
def patient_appointments(pid):
    p = _patient(pid)
    rows = sb_select(patient_id=f"eq.{p.id}")
    # bookings from the Appointments app not linked yet
    extra = []
    if p.case_number:
        extra += sb_select(patient_id="is.null", case_no=f"eq.{p.case_number}")
    if _digits(p.mobile):
        extra += sb_select(patient_id="is.null", mobile=f"like.*{_digits(p.mobile)}")
    seen = {r["id"] for r in rows}
    extra = [r for r in extra if r["id"] not in seen and not seen.add(r["id"])]
    found = _match_patients(extra)
    rows += [r for r in extra if found.get(r["id"]) is not None and found[r["id"]].id == p.id]
    shaped = _with_links(rows)
    today = today_ist().isoformat()
    upcoming = sorted([r for r in shaped if r["date"] >= today and r["state"] == "SCHEDULED"], key=lambda r: (r["date"], r["time"]))
    past = sorted([r for r in shaped if r not in upcoming], key=lambda r: (r["date"], r["time"]), reverse=True)
    return jsonify({"patient_id": p.id, "upcoming": upcoming, "past": past}), 200


@appointments_bp.route("/appointments", methods=["POST"])
@require_login
@_guard
def create_appointment():
    d = request.get_json(silent=True) or {}
    if not isinstance(d, dict):
        raise ApptError("No data provided")
    day = _date(d.get("date") or d.get("appointment_date"))
    tm = _time(d.get("time") or d.get("appointment_time"), required=True)
    source = _text(d.get("source"), 40)
    visit_id = int(d["visit_id"]) if str(d.get("visit_id") or "").isdigit() else None

    patient = None
    if str(d.get("patient_id") or "").isdigit():
        patient = _patient(d["patient_id"])
    elif visit_id:
        v = db.session.get(Visit, visit_id)
        patient = db.session.get(Patient, v.patient_id) if v else None
    elif d.get("case_number"):
        patient = Patient.query.filter(db.func.upper(Patient.case_number) == _norm_case(d["case_number"])).first()

    doctor = _text(d.get("doctor_name"), 120) or (_actor_name() if source in FOLLOW_UP_SOURCES else None)
    treatment = _text(d.get("treatment"), 200)
    notes = _text(d.get("notes"), 500)

    # follow-ups from the doctor's screens: one booking per patient per day
    if patient is not None and source in FOLLOW_UP_SOURCES:
        if visit_id is None:
            av = _visit_state({patient.id}).get(patient.id) or {}
            visit_id = av.get("active") or av.get("closed_today")
        row, result = book_follow_up(patient, day, tm, visit_id=visit_id, source=source,
                                     treatment=treatment if treatment and treatment != "Follow-up" else (treatment or "Follow-up"),
                                     notes=notes, doctor=doctor)
        out = _with_links([row])[0]
        out["result"] = result
        return jsonify(out), 201 if result == "created" else 200

    if patient is not None:
        if not d.get("allow_second"):
            same = sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{day}", status="eq.SCHEDULED")
            if same:
                raise ApptError(f"{patient.name} already has an appointment on this day at "
                                f"{str(same[0].get('appointment_time') or '')[:5]}. Change that one instead.", 409)
        row = {**_patient_fields(patient)}
    else:
        name = _text(d.get("name"), 200)
        if not name:
            raise ApptError("Please choose the patient (or type the name).")
        age = d.get("age")
        try:
            age = int(age) if str(age or "").strip() else None
        except ValueError:
            age = None
        row = {"name": name, "mobile": _text(d.get("mobile"), 20), "case_no": _text(d.get("case_number"), 50),
               "age": age if age is not None and 0 <= age <= 120 else None}
    row.update({"appointment_date": day, "appointment_time": tm, "treatment": treatment, "notes": notes,
                "status": _status(d.get("status")) or "SCHEDULED", "doctor_name": doctor,
                "visit_id": visit_id, "source": source or "clinic"})
    out = _with_links([sb_insert(row)])[0]
    out["result"] = "created"
    return jsonify(out), 201


@appointments_bp.route("/appointments/<appt_id>", methods=["PUT"])
@require_login
@_guard
def update_appointment(appt_id):
    d = request.get_json(silent=True) or {}
    cur = sb_get(appt_id)
    ch = {}
    if "date" in d or "appointment_date" in d:
        ch["appointment_date"] = _date(d.get("date") or d.get("appointment_date"))
    if "time" in d or "appointment_time" in d:
        t = _time(d.get("time") or d.get("appointment_time"))
        if t:
            ch["appointment_time"] = t
    for key, col, n in (("treatment", "treatment", 200), ("notes", "notes", 500), ("doctor_name", "doctor_name", 120)):
        if key in d:
            ch[col] = _text(d.get(key), n)
    if "status" in d and d.get("status"):
        ch["status"] = _status(d["status"])
    if str(d.get("patient_id") or "").isdigit() and not cur.get("patient_id"):
        ch.update(_patient_fields(_patient(d["patient_id"])))
    elif not cur.get("patient_id"):            # an unlinked booking: its typed details may be corrected
        for key, col, n in (("name", "name", 200), ("mobile", "mobile", 20), ("case_number", "case_no", 50)):
            if key in d and _text(d.get(key), n):
                ch[col] = _text(d.get(key), n)
    if not ch:
        return jsonify(_with_links([cur])[0]), 200
    return jsonify(_with_links([sb_update(appt_id, ch)])[0]), 200


@appointments_bp.route("/appointments/<appt_id>", methods=["DELETE"])
@require_login
@_guard
def cancel_appointment(appt_id):
    cur = sb_get(appt_id)
    reason = _text((request.get_json(silent=True) or {}).get("reason") or request.args.get("reason"), 200)
    ch = {"status": "CANCELLED"}
    if reason:
        ch["notes"] = _text(f"{cur.get('notes') or ''} · Cancelled: {reason}".strip(" ·"), 500)
    row = sb_update(appt_id, ch)
    return jsonify({**_with_links([row])[0], "deleted": appt_id}), 200


@appointments_bp.route("/appointments/<appt_id>/link", methods=["POST"])
@require_login
@_guard
def link_appointment(appt_id):
    d = request.get_json(silent=True) or {}
    p = _patient(d.get("patient_id"))
    sb_get(appt_id)
    ch = _patient_fields(p)
    return jsonify(_with_links([sb_update(appt_id, ch)])[0]), 200


# ═════════════════════════════════════════════════════════════════════
#  Automatic updates — watch the doctor's saves (no other file changes)
# ═════════════════════════════════════════════════════════════════════
_WATCH = [
    ("POST", re.compile(r"/visits/(\d+)/consultations/?$"), "consultation"),
    ("PUT",  re.compile(r"/consultations/(\d+)/?$"), "consultation-edit"),
    ("POST", re.compile(r"/visits/(\d+)/prescriptions/?$"), "prescription"),
    ("PUT",  re.compile(r"/prescriptions/(\d+)/?$"), "prescription-edit"),
    ("PUT",  re.compile(r"/visits/(\d+)/next-appointment/?$"), "visit"),
    ("PUT",  re.compile(r"/visits/(\d+)/close/?$"), "close"),
    ("POST", re.compile(r"/visits/?$"), "new-visit"),          # Reception creates a visit
    ("POST", re.compile(r"/patients/?$"), "new-patient"),      # registration (creates the first visit)
]


def _which():
    for method, rx, kind in _WATCH:
        if request.method == method:
            m = rx.search(request.path)
            if m:
                return kind, (int(m.group(1)) if m.groups() else None)
    return None, None


def _record(kind, rid):
    """(visit_id, old follow-up date) of the record being edited."""
    try:
        if kind == "consultation-edit":
            from models import Consultation
            c = db.session.get(Consultation, rid)
            return (c.visit_id, str(c.follow_up_date or "")[:10] or None) if c else (None, None)
        if kind == "prescription-edit":
            from models import Prescription
            p = db.session.get(Prescription, rid)
            return (p.visit_id, str(p.follow_up_date or "")[:10] or None) if p else (None, None)
        if kind == "visit":
            v = db.session.get(Visit, rid)
            return (rid, str(v.next_appointment or "")[:10] or None) if v else (rid, None)
    except Exception as e:                              # never stop the save
        print("[appointments] could not read the record before the save:", e)
    return (rid if kind in ("consultation", "prescription", "close") else None), None


# ═════════════════════════════════════════════════════════════════════
#  Appointment ⇄ visit, kept in step
#   • appointment day: every linked appointment of today gets its visit
#     (created automatically, at the booked time) → Doctor + Reception see it
#   • a visit created here (Reception, registration) → today's appointment is
#     linked to it, or a new appointment is made for it → the Appointments
#     app shows the walk-in too
#   • an appointment of today cancelled / moved to another day → the visit
#     made for it is withdrawn, as long as nothing was written in it yet
# ═════════════════════════════════════════════════════════════════════
AUTO_BY = "Appointments app"
_sync_state = {"at": None}
SYNC_EVERY = timedelta(seconds=int(os.environ.get("APPOINTMENT_SYNC_SECONDS", "60") or 60))


def _utc_naive(day_iso, hhmm):
    """IST date + time → the naive-UTC value visits.visit_date uses."""
    d = datetime.strptime(day_iso, "%Y-%m-%d")
    h, m = (int(x) for x in (hhmm or "00:00").split(":")[:2])
    return datetime(d.year, d.month, d.day, h, m) - timedelta(hours=5, minutes=30)


def _ist_midnight_utc():
    return datetime.combine(today_ist(), datetime.min.time()) - timedelta(hours=5, minutes=30)


def _untouched(v):
    """An automatic visit nobody has worked on yet (safe to withdraw)."""
    if (v.status or "").upper() != "CREATED":
        return False
    for f in ("diagnosis", "treatment_done", "treatment_plan", "advice", "billing_note"):
        if str(getattr(v, f, "") or "").strip():
            return False
    try:
        from models import Consultation, Prescription
        if Consultation.query.filter_by(visit_id=v.id).first() or Prescription.query.filter_by(visit_id=v.id).first():
            return False
    except Exception:
        pass
    return True


def sync_today(force=False):
    """Make sure every linked appointment of today has its visit; withdraw the
    untouched automatic visits of appointments that were cancelled / moved.
    Returns a small report."""
    now = datetime.utcnow()
    if not force and SYNC_EVERY.total_seconds() <= 0:     # 0 = only when asked (POST /appointments/sync-today)
        return None
    if not force and _sync_state["at"] and now - _sync_state["at"] < SYNC_EVERY:
        return None
    _sync_state["at"] = now
    if not configured():
        return None
    report = {"created": 0, "linked": 0, "withdrawn": 0}
    day = today_ist().isoformat()
    rows = sb_select(appointment_date=f"eq.{day}")
    _with_links(rows)                                    # links bookings from the Appointments app
    start = _ist_midnight_utc()
    for r in rows:
        if (r.get("status") or "").upper() != "SCHEDULED" or not r.get("patient_id"):
            continue
        if r.get("visit_id"):
            v = db.session.get(Visit, int(r["visit_id"]))
            if v is not None:
                continue
        pid = int(r["patient_id"])
        if db.session.get(Patient, pid) is None:
            continue
        active = (Visit.query.filter(Visit.patient_id == pid, Visit.status.in_(list(ACTIVE_VISIT)))
                  .order_by(Visit.id.desc()).first())
        if active is not None:
            sb_update(r["id"], {"visit_id": active.id})
            report["linked"] += 1
            continue
        t = str(r.get("appointment_time") or "")[:5] or "11:00"
        v = Visit(patient_id=pid, visit_date=_utc_naive(day, t), chief_complaint="",
                  followup_treatment=_text(r.get("treatment"), 500) or "Appointment",
                  status="CREATED", created_by=AUTO_BY,
                  assigned_doctor=_text(r.get("doctor_name"), 100))
        db.session.add(v)
        db.session.commit()
        # claim the appointment only if nobody else did meanwhile (several server workers)
        claimed = _call("PATCH", _q(id=f"eq.{r['id']}", visit_id="is.null"), {"visit_id": v.id},
                        prefer="return=representation")
        if not claimed:
            v.status = "CANCELLED"
            db.session.commit()
            continue
        report["created"] += 1
    # automatic visits of today whose appointment was cancelled or moved away
    autos = (Visit.query.filter(Visit.created_by == AUTO_BY, Visit.status == "CREATED")
             .filter(Visit.visit_date >= start - timedelta(hours=12)).all())
    if autos:
        by_visit = {}
        for r in sb_select(visit_id=f"in.({','.join(str(v.id) for v in autos)})"):
            by_visit[int(r["visit_id"])] = r
        for v in autos:
            r = by_visit.get(v.id)
            gone = r is None or (r.get("status") or "").upper() == "CANCELLED" or str(r.get("appointment_date"))[:10] != day
            if gone and _untouched(v):
                v.status = "CANCELLED"
                db.session.commit()
                if r is not None and str(r.get("appointment_date"))[:10] != day:
                    sb_update(r["id"], {"visit_id": None})          # it gets a new visit on its new day
                report["withdrawn"] += 1
    if any(report.values()):
        print("[appointments] today's sync:", report)
    return report


def on_visit_created(visit, body=None):
    """A visit was created in this app: link it to today's appointment, or book one for it."""
    body = body or {}
    patient = db.session.get(Patient, visit.patient_id)
    if patient is None:
        return None
    day = today_ist().isoformat()
    tm = None
    try:
        tm = _time(body.get("visit_time") or body.get("appointment_time"))
    except ApptError:
        tm = None
    if tm and visit.visit_date and visit.created_by != AUTO_BY:
        visit.visit_date = _utc_naive(day, tm)               # the time chosen by Reception
        db.session.commit()
    # today's booking that has no visit yet (or already this one) — an earlier, finished
    # visit's appointment is left alone
    free = lambda r: (r.get("status") or "").upper() == "SCHEDULED" and r.get("visit_id") in (None, visit.id)
    rows = [r for r in sb_select(patient_id=f"eq.{patient.id}", appointment_date=f"eq.{day}") if free(r)]
    if not rows:                                          # booked in the Appointments app, not linked yet
        cand = sb_select(appointment_date=f"eq.{day}", patient_id="is.null", status="eq.SCHEDULED")
        found = _match_patients(cand)
        rows = [r for r in cand if found.get(r["id"]) is not None and found[r["id"]].id == patient.id and free(r)]
    if rows:
        r = sorted(rows, key=lambda x: (x.get("visit_id") != visit.id, str(x.get("appointment_time"))))[0]
        if r.get("visit_id") == visit.id and r.get("patient_id"):
            return r
        return sb_update(r["id"], {**_patient_fields(patient), "visit_id": visit.id})
    now_ist = datetime.now(IST)
    row = {**_patient_fields(patient), "appointment_date": day,
           "appointment_time": tm or f"{now_ist.hour:02d}:{now_ist.minute:02d}",
           "treatment": _text(body.get("followup_treatment") or visit.followup_treatment, 200)
                        or _text(body.get("chief_complaint") or visit.chief_complaint, 200) or "Visit",
           "notes": _text(f"Complaint: {visit.chief_complaint}" if visit.chief_complaint else None, 500),
           "status": "SCHEDULED", "visit_id": visit.id, "source": "clinic-visit",
           "doctor_name": _text(visit.assigned_doctor, 120)}
    return sb_insert(row)


@appointments_bp.route("/appointments/sync-today", methods=["POST"])
@require_login
@_guard
def sync_today_now():
    return jsonify(sync_today(force=True) or {}), 200


@appointments_bp.before_app_request
def _remember_before():
    kind, rid = _which()
    if kind and configured():
        g._appt_watch = (kind, rid, _record(kind, rid) if rid else (None, None))
    # appointment day: create the visits of today's appointments (at most once a minute)
    elif request.method == "GET" and configured() and "/api/" in request.path and not request.path.endswith("/connection"):
        try:
            sync_today()
        except ApptError as e:
            print("[appointments] today's sync skipped:", e.message)
        except Exception as e:
            db.session.rollback()
            print("[appointments] today's sync failed:", type(e).__name__, str(e)[:300])


@appointments_bp.after_app_request
def _sync_after(response):
    watch = getattr(g, "_appt_watch", None)
    if not watch or response.status_code >= 300:
        return response
    kind, rid, (visit_id, old_date) = watch
    if kind in ("new-visit", "new-patient"):
        try:
            data = response.get_json(silent=True) or {}
            vid = data.get("visit_id") or data.get("id") if kind == "new-visit" else data.get("visit_id")
            v = db.session.get(Visit, int(vid)) if str(vid or "").isdigit() else None
            if v is not None:
                on_visit_created(v, request.get_json(silent=True) or {})
        except ApptError as e:
            print("[appointments] visit → appointment skipped:", e.message)
        except Exception as e:
            db.session.rollback()
            print("[appointments] visit → appointment failed:", type(e).__name__, str(e)[:300])
        return response
    try:
        if kind in ("consultation-edit", "prescription-edit"):
            visit_id = visit_id or _record(kind, rid)[0]
        visit = db.session.get(Visit, visit_id) if visit_id else None
        patient = db.session.get(Patient, visit.patient_id) if visit else None
        if patient is None:
            return response
        if kind == "close":
            n = complete_today(patient, visit_id=visit.id)
            if n:
                print(f"[appointments] visit {visit.id} closed → {n} appointment(s) of today completed")
            return response

        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return response
        key = "next_appointment" if kind == "visit" else "follow_up_date"
        if key not in body:
            return response
        new_date = _date(body.get(key), required=False)
        new_time = None
        try:
            new_time = _time(body.get("follow_up_time"))
        except ApptError:
            new_time = None
        source = "visit" if kind == "visit" else kind.replace("-edit", "")
        if new_date:
            if new_date < today_ist().isoformat():
                return response                         # a date in the past is not a booking
            treatment = _text(body.get("treatment_plan"), 200) or _text(body.get("advice"), 200) or "Follow-up"
            done = _text(body.get("treatment_done_today") or body.get("treatment_done"), 200)
            notes = _text(f"Follow-up — previous visit: {done}" if done else (
                f"Follow-up for: {body.get('diagnosis')}" if body.get("diagnosis") else "Follow-up appointment"), 500)
            row, result = book_follow_up(patient, new_date, new_time, old_date=old_date, visit_id=visit.id,
                                         source=source, treatment=treatment, notes=notes,
                                         doctor=_text(body.get("doctor") or visit.assigned_doctor, 120) or _actor_name())
            print(f"[appointments] {kind} {rid}: follow-up {new_date} {new_time or ''} → {result}")
        elif old_date and kind.endswith("-edit") or (old_date and kind == "visit"):
            cancel_follow_up(patient, old_date)
    except ApptError as e:
        print("[appointments] automatic update skipped:", e.message)
    except Exception as e:                              # the doctor's save already succeeded
        print("[appointments] automatic update failed:", type(e).__name__, str(e)[:300])
    return response