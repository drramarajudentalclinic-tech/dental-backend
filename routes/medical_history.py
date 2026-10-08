"""
MEDICAL HISTORY — shared, record-level Add / Edit / Update / Delete
====================================================================

One module, one set of tables, used by BOTH Doctor and Reception.

    Patient
       └── shared medical-history records  (this module)
              ├── Doctor screens
              └── Reception screens

Five sections, all working the same way:

    allergies       -> AllergyRecord
    medications     -> Medication
    habits          -> HabitRecord
    womens-health   -> WomenHealthRecord
    conditions      -> MedicalConditionRecord

API (all under /api/patients):

    GET    /<patient_id>/medical-history                       everything, all sections
    GET    /<patient_id>/medical-history/<section>             one section
    POST   /<patient_id>/medical-history/<section>             ADD    -> always a NEW row
    GET    /<patient_id>/medical-history/<section>/<id>        one record
    PUT    /<patient_id>/medical-history/<section>/<id>        UPDATE -> only that row
    DELETE /<patient_id>/medical-history/<section>/<id>        DELETE -> only that row
    PUT    /<patient_id>/medical-history/<section>/none-known  "No known …" tick box
    GET    /<patient_id>/medical-history/audit                 change log

Rules this module enforces:

  * POST never looks for an "existing" record to update, merge or replace.
    It inserts a new row every time, even if the same allergen / medicine /
    condition is already on file.
  * PUT and DELETE find the row by its own id (plus the patient id, so a
    record can never be changed through another patient's URL).
  * created_at / created_by are written once and never touched again.
    updated_at / updated_by are written only when something really changed.
  * Every add / update / delete is written to medical_history_audit.
  * Doctor, Reception and Admin have identical rights on every section.

Wiring: patients.py calls register_medical_history_routes(patients_bp) at
the bottom of the file — no change to app.py is required. This file can sit
in the same folder as patients.py or next to models.py; both work.

The database is brought up to date automatically by models.py before the
first query after start-up (new tables are created, new columns are added;
nothing is dropped or rewritten).
"""

import json
import traceback
from datetime import datetime
from functools import wraps

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from database import db
from models import (
    AllergyRecord,
    Habit,
    HabitRecord,
    MedicalConditionRecord,
    MedicalHistory,
    MedicalHistoryAudit,
    Medication,
    Patient,
    User,
    WomanHistory,
    WomenHealthRecord,
    ensure_medical_history_schema,
    ist_today,
)
from auth_utils import require_login, get_current_role

try:  # used only to read the logged-in user's name
    from flask_jwt_extended import get_jwt, get_jwt_identity
except Exception:  # pragma: no cover
    get_jwt = get_jwt_identity = None


# ══════════════════════════════════════════════════════════════
#  OPTION LISTS  (keep in step with MedicalHistoryManager.jsx)
# ══════════════════════════════════════════════════════════════
# Keys are the MedicalHistory column names, so the old one-row summary
# (used by alerts and older screens) can be kept up to date.
CONDITION_OPTIONS = [
    ("aids", "AIDS"),
    ("asthma", "Asthma"),
    ("arthritis_rheumatism", "Arthritis / Rheumatism"),
    ("blood_disease", "Blood Disease"),
    ("bp_high", "High Blood Pressure"),
    ("bp_low", "Low Blood Pressure"),
    ("corticosteroid_treatment", "Corticosteroid Treatment"),
    ("cancer", "Cancer"),
    ("diabetes", "Diabetes"),
    ("epilepsy", "Epilepsy"),
    ("heart_problems", "Heart Problems"),
    ("hepatitis", "Hepatitis"),
    ("herpes", "Herpes"),
    ("jaundice", "Jaundice"),
    ("liver_disease", "Liver Disease"),
    ("kidney_disease", "Kidney Disease"),
    ("psychiatric_treatment", "Psychiatric Treatment"),
    ("radiation_treatment", "Radiation Treatment"),
    ("respiratory_disease", "Respiratory Disease"),
    ("rheumatic_fever", "Rheumatic Fever"),
    ("tb", "Tuberculosis"),
    ("thyroid_problems", "Thyroid Problems"),
    ("ulcer", "Ulcer"),
    ("venereal_disease", "Venereal Disease"),
]
CONDITION_LABELS = dict(CONDITION_OPTIONS)

# Keys are the Habit column names.
HABIT_OPTIONS = [
    ("smoking", "Smoking"),
    ("alcohol", "Alcohol"),
    ("tobacco", "Tobacco / Chewing Tobacco"),
    ("pan_chewing", "Pan / Betel Nut"),
    ("spicy_foods", "Spicy Foods"),
]
HABIT_LABELS = dict(HABIT_OPTIONS)

WOMEN_TYPES = ["Pregnancy", "Nursing", "Menstrual history", "Menopause", "Gynecological", "Other"]

ALLERGY_STATUSES   = ["Active", "Resolved"]
CONDITION_STATUSES = ["Current", "Controlled", "Resolved"]
HABIT_STATUSES     = ["Current", "Occasional", "Former"]
WOMEN_STATUSES     = ["Current", "Past"]

ALLOWED_ROLES = {"doctor", "reception", "admin"}
ROLE_ALIASES = {
    "receptionist": "reception",
    "front_desk": "reception",
    "frontdesk": "reception",
    "dr": "doctor",
    "administrator": "admin",
}

LEGACY_ACTOR = {"name": None, "role": "legacy"}
TEXT_LIMIT = 2000


class HistoryError(Exception):
    """A problem that should be shown to the user as-is."""

    def __init__(self, message, status=400, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra or {}


# ══════════════════════════════════════════════════════════════
#  WHO IS LOGGED IN
# ══════════════════════════════════════════════════════════════
def normalize_role(role):
    role = (str(role or "")).strip().lower()
    return ROLE_ALIASES.get(role, role)


def current_actor():
    """{"name": <user name>, "role": "doctor" | "reception" | "admin"}"""
    role = normalize_role(get_current_role())

    claims, identity = {}, None
    if get_jwt is not None:
        try:
            claims = get_jwt() or {}
        except Exception:
            claims = {}
        try:
            identity = get_jwt_identity()
        except Exception:
            identity = None

    name = None
    for key in ("full_name", "name", "username"):
        if claims.get(key):
            name = str(claims[key]).strip()
            break

    if isinstance(identity, dict):
        name = name or identity.get("full_name") or identity.get("name") or identity.get("username")
        identity = identity.get("id") or identity.get("user_id")

    if not name and identity is not None:
        ident = str(identity).strip()
        user = None
        try:
            user = User.query.filter_by(username=ident).first()
            if user is None and ident.isdigit():
                user = db.session.get(User, int(ident))
        except Exception:
            user = None
        name = user.username if user is not None else ident

    return {"name": (name or "")[:100] or None, "role": role or None}


def history_access(fn):
    """Logged in + role is Doctor, Reception or Admin (all three equal)."""

    @wraps(fn)
    def checked(*args, **kwargs):
        if normalize_role(get_current_role()) not in ALLOWED_ROLES:
            return jsonify({
                "error": "Forbidden",
                "detail": "Only Doctor and Reception can view or change medical history.",
            }), 403
        return fn(*args, **kwargs)

    return require_login(checked)


# ══════════════════════════════════════════════════════════════
#  FIELD CLEANING
# ══════════════════════════════════════════════════════════════
class Field:
    def __init__(self, name, kind="str", attr=None, label=None, required=False,
                 max_len=None, choices=None, default=None, aliases=()):
        self.name = name
        self.kind = kind                  # str | text | date | bool | choice
        self.attr = attr or name          # model attribute
        self.label = label or name.replace("_", " ").capitalize()
        self.required = required
        self.max_len = max_len
        self.choices = choices
        self.default = default
        self.aliases = aliases

    def find(self, data):
        """(present?, raw value) — looks at the field name, then its aliases."""
        for key in (self.name, *self.aliases):
            if key in data:
                return True, data[key]
        return False, None


def _parse_date(value):
    raw = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ("yes", "true", "1", "active", "on")


def _clean_value(field, raw):
    """Returns the cleaned value, or raises HistoryError."""
    if field.kind == "bool":
        return _to_bool(raw)

    text_value = "" if raw is None else str(raw).strip()

    if field.kind == "date":
        if not text_value:
            return None
        parsed = _parse_date(text_value)
        if parsed is None:
            raise HistoryError(f"{field.label} is not a valid date.")
        return parsed

    if field.kind == "choice":
        if not text_value:
            return None
        for choice in field.choices:
            if choice.lower() == text_value.lower():
                return choice
        raise HistoryError(f"{field.label}: \"{text_value}\" is not one of the allowed values.")

    limit = field.max_len or (TEXT_LIMIT if field.kind == "text" else 255)
    if len(text_value) > limit:
        raise HistoryError(f"{field.label} is too long (maximum {limit} characters).")
    return text_value or None


def clean_fields(spec, data, creating):
    """Validated {model attribute: value}.

    Creating: every field is filled (missing -> default).
    Updating: only the fields actually present in the request are returned,
              so an update can never blank out something it did not send.
    """
    values = {}
    for field in spec.fields:
        present, raw = field.find(data)
        if not present:
            if creating:
                default = field.default() if callable(field.default) else field.default
                if field.required and default is None:
                    raise HistoryError(f"{field.label} is required.")
                values[field.attr] = default
            continue

        value = _clean_value(field, raw)
        if value is None:
            if field.required:
                raise HistoryError(f"{field.label} is required.")
            if field.default is not None and field.kind in ("choice", "date", "bool"):
                # e.g. blank status / blank recorded date: keep a sensible value
                if not creating:
                    continue
                value = field.default() if callable(field.default) else field.default
        values[field.attr] = value
    return values


# ══════════════════════════════════════════════════════════════
#  SECTION DEFINITIONS
# ══════════════════════════════════════════════════════════════
class Section:
    def __init__(self, key, slug, model, noun, fields, summary, order_by=None,
                 prepare=None, female_only=False):
        self.key = key              # JSON key        e.g. "womens_health"
        self.slug = slug            # URL segment     e.g. "womens-health"
        self.model = model
        self.noun = noun            # "allergy", "medication", …
        self.fields = fields
        self.summary = summary      # record -> short one-line description
        self.prepare = prepare      # (values, data, record|None) -> None, may raise
        self.female_only = female_only

    def query(self, patient_id):
        return self.model.query.filter_by(patient_id=patient_id).order_by(self.model.id.asc())

    def serialize(self, record):
        out = record.to_dict()
        out["section"] = self.key
        out["label"] = self.summary(record)
        return out


def _join(*parts, sep=" - "):
    # Plain ASCII separator on purpose: these strings are also stored
    # (change log, summary tables), and must be safe in any database encoding.
    return sep.join(str(p).strip() for p in parts if p and str(p).strip())


# ── Allergies ────────────────────────────────────────────────
def _prepare_allergy(values, data, record):
    # Type is not compulsory on the reception form; never leave it empty
    # (the column is NOT NULL) and never throw away what was typed.
    if "allergy_type" in values and not values["allergy_type"]:
        values["allergy_type"] = (record.allergy_type if record is not None else None) or "Other"


# ── Medications ──────────────────────────────────────────────
def _prepare_medication(values, data, record):
    # "status": "Active" / "Stopped" is accepted as another way to send `active`.
    if "active" not in data and "status" in data:
        status = str(data.get("status") or "").strip().lower()
        if status:
            values["active"] = status not in ("stopped", "inactive", "discontinued", "completed")
    start = values.get("start_date", record.start_date if record is not None else None)
    end = values.get("end_date", record.end_date if record is not None else None)
    if start and end and end < start:
        raise HistoryError("End date cannot be before the start date.")


# ── Habits / Conditions: fixed list + "other" ────────────────
def _keyed_prepare(key_attr, name_attr, labels, what):
    def prepare(values, data, record):
        if key_attr in values:
            key = values[key_attr]
            if key != "other":
                values[name_attr] = labels[key]
            else:
                name = values.get(name_attr)
                if not name and record is not None and getattr(record, key_attr) == "other":
                    name = getattr(record, name_attr)   # unchanged "other" record
                if not name:
                    raise HistoryError(f"Please type the name of the {what}.")
                values[name_attr] = name
        elif name_attr in values:
            # Name sent without the key: only meaningful for "other" records.
            if record is not None and getattr(record, key_attr) != "other":
                values.pop(name_attr)
            elif not values[name_attr]:
                raise HistoryError(f"Please type the name of the {what}.")
    return prepare


SECTIONS = {}


def _add_section(section):
    SECTIONS[section.key] = section
    return section


_add_section(Section(
    key="allergies", slug="allergies", model=AllergyRecord, noun="allergy",
    fields=[
        Field("allergen", required=True, max_len=255, label="Allergy / substance", aliases=("allergy",)),
        Field("type", attr="allergy_type", max_len=50, label="Allergy type", default="Other",
              aliases=("allergy_type",)),
        Field("reaction", max_len=255),
        Field("severity", max_len=50),
        Field("status", kind="choice", choices=ALLERGY_STATUSES, default="Active"),
        Field("notes", kind="text"),
        Field("recorded_date", kind="date", default=ist_today, label="Date"),
    ],
    summary=lambda r: _join(r.allergen, r.reaction),
    prepare=_prepare_allergy,
))

_add_section(Section(
    key="medications", slug="medications", model=Medication, noun="medication",
    fields=[
        Field("medicine_name", required=True, max_len=200, label="Medication name",
              aliases=("medication", "name")),
        Field("dosage", max_len=100),
        Field("frequency", max_len=100),
        Field("route", max_len=50),
        Field("duration", max_len=100),
        Field("purpose", max_len=200, label="Reason / indication", aliases=("reason", "indication")),
        Field("prescribed_by", max_len=200),
        Field("start_date", kind="date"),
        Field("end_date", kind="date"),
        Field("active", kind="bool", default=True),
        Field("notes", kind="text"),
        Field("recorded_date", kind="date", default=ist_today, label="Date"),
    ],
    summary=lambda r: _join(r.medicine_name, _join(r.dosage, r.frequency, sep=" ")),
    prepare=_prepare_medication,
))

_add_section(Section(
    key="habits", slug="habits", model=HabitRecord, noun="habit",
    fields=[
        Field("habit_key", kind="choice", choices=[k for k, _ in HABIT_OPTIONS] + ["other"],
              required=True, label="Habit", aliases=("habit",)),
        Field("habit_name", max_len=150, label="Habit name"),
        Field("details", kind="text"),
        Field("frequency", max_len=100),
        Field("duration", max_len=100),
        Field("status", kind="choice", choices=HABIT_STATUSES, default="Current"),
        Field("notes", kind="text"),
        Field("recorded_date", kind="date", default=ist_today, label="Date"),
    ],
    summary=lambda r: _join(r.habit_name, r.details),
    prepare=_keyed_prepare("habit_key", "habit_name", HABIT_LABELS, "habit"),
))

_add_section(Section(
    key="womens_health", slug="womens-health", model=WomenHealthRecord, noun="women's health record",
    fields=[
        Field("record_type", kind="choice", choices=WOMEN_TYPES, required=True, label="Type",
              aliases=("type",)),
        Field("details", kind="text"),
        Field("lmp_date", kind="date", label="LMP date", aliases=("lmp",)),
        Field("due_date", kind="date"),
        Field("status", kind="choice", choices=WOMEN_STATUSES, default="Current"),
        Field("notes", kind="text"),
        Field("recorded_date", kind="date", default=ist_today, label="Date"),
    ],
    summary=lambda r: _join(r.record_type, r.details or (f"Due {r.due_date.strftime('%d-%m-%Y')}" if r.due_date else "")),
    female_only=True,
))

_add_section(Section(
    key="conditions", slug="conditions", model=MedicalConditionRecord, noun="medical condition",
    fields=[
        Field("condition_key", kind="choice", choices=[k for k, _ in CONDITION_OPTIONS] + ["other"],
              required=True, label="Condition", aliases=("condition",)),
        Field("condition_name", max_len=255, label="Condition name"),
        Field("details", kind="text"),
        Field("status", kind="choice", choices=CONDITION_STATUSES, default="Current"),
        Field("since", max_len=100),
        Field("notes", kind="text"),
        Field("recorded_date", kind="date", default=ist_today, label="Date"),
    ],
    summary=lambda r: _join(r.condition_name, r.details),
    prepare=_keyed_prepare("condition_key", "condition_name", CONDITION_LABELS, "condition"),
))

SECTION_ORDER = ["conditions", "allergies", "medications", "habits", "womens_health"]

_SLUGS = {}
for _s in SECTIONS.values():
    _SLUGS[_s.slug] = _s
    _SLUGS[_s.key] = _s
_SLUGS.update({
    "women": SECTIONS["womens_health"],
    "womens": SECTIONS["womens_health"],
    "medical-conditions": SECTIONS["conditions"],
    "medical_conditions": SECTIONS["conditions"],
    "allergy": SECTIONS["allergies"],
})


def get_section(slug):
    section = _SLUGS.get((slug or "").strip().lower())
    if section is None:
        raise HistoryError("Unknown medical-history section.", 404)
    return section


def _is_female(patient):
    return (patient.gender or "").strip().lower() == "female"


# ══════════════════════════════════════════════════════════════
#  DATABASE UPGRADE
#  The upgrade itself lives in models.py (ensure_medical_history_schema)
#  and runs automatically before the first query after start-up. The
#  hook below is a second safety net for the same step.
# ══════════════════════════════════════════════════════════════
def _ensure_schema_before_request():
    try:
        ensure_medical_history_schema()
    except Exception:
        print("[medical-history] DATABASE UPGRADE FAILED - medical history will not work until this is fixed:")
        traceback.print_exc()
        db.session.rollback()
    return None


# ══════════════════════════════════════════════════════════════
#  CARRYING OVER DATA FROM THE OLDER ONE-ROW-PER-PATIENT TABLES
#
#  MedicalHistory (tick boxes), Habit (one text per habit) and
#  WomanHistory (pregnant / nursing) could each hold only one value per
#  patient. Each value found there becomes its own record, once. The
#  old rows are NOT deleted.
#
#  After that the direction is reversed: the records are the truth and
#  the old tables are rewritten from them after every change, so alerts,
#  history screens and print-outs that still read the old tables show
#  the same information.
# ══════════════════════════════════════════════════════════════
def _stamp_from_legacy(legacy_row):
    """(created_at, recorded_date) for a record carried over from an old row."""
    when = getattr(legacy_row, "updated_at", None) or datetime.utcnow()
    recorded = getattr(legacy_row, "recorded_date", None) or when.date()
    return when, recorded


def _audit(patient_id, section_key, record_id, action, summary, actor, before=None, after=None):
    db.session.add(MedicalHistoryAudit(
        patient_id=patient_id,
        section=section_key,
        record_id=record_id,
        action=action,
        summary=(summary or "")[:300],
        before_json=json.dumps(before, default=str) if before is not None else None,
        after_json=json.dumps(after, default=str) if after is not None else None,
        performed_by=actor.get("name"),
        performed_by_role=actor.get("role"),
        created_at=datetime.utcnow(),
    ))


def _import_legacy(patient):
    """Turn values that exist only in the old tables into records."""
    pid = patient.id
    created = []

    # ── Medical conditions ──
    medical = MedicalHistory.query.filter_by(patient_id=pid).first()
    if medical is not None:
        records = MedicalConditionRecord.query.filter_by(patient_id=pid).all()
        live_keys = {r.condition_key for r in records if (r.status or "Current") != "Resolved"}
        refs = {r.legacy_ref for r in records if r.legacy_ref}
        when, recorded = _stamp_from_legacy(medical)

        for key, label in CONDITION_OPTIONS:
            if getattr(medical, key, False) and key not in live_keys and key not in refs:
                created.append(("conditions", MedicalConditionRecord(
                    patient_id=pid, condition_key=key, condition_name=label, status="Current",
                    recorded_date=recorded, created_at=when, legacy_ref=key,
                    created_by=None, created_by_role="legacy", version=1,
                )))

        other = (medical.other or "").strip()
        if other and "other" not in live_keys and "other" not in refs:
            fits = len(other) <= 255
            created.append(("conditions", MedicalConditionRecord(
                patient_id=pid, condition_key="other",
                condition_name=other if fits else "Other condition",
                details=None if fits else other,
                status="Current", recorded_date=recorded, created_at=when, legacy_ref="other",
                created_by=None, created_by_role="legacy", version=1,
            )))

    # ── Habits ──
    habit = Habit.query.filter_by(patient_id=pid).first()
    if habit is not None:
        records = HabitRecord.query.filter_by(patient_id=pid).all()
        live_keys = {r.habit_key for r in records if (r.status or "Current") != "Former"}
        refs = {r.legacy_ref for r in records if r.legacy_ref}
        when, recorded = _stamp_from_legacy(habit)

        for key, label in HABIT_OPTIONS:
            value = (getattr(habit, key, None) or "").strip()
            if value and key not in live_keys and key not in refs:
                created.append(("habits", HabitRecord(
                    patient_id=pid, habit_key=key, habit_name=label,
                    details=None if value.lower() == "yes" else value,
                    status="Current", recorded_date=recorded, created_at=when, legacy_ref=key,
                    created_by=None, created_by_role="legacy", version=1,
                )))

    # ── Women's health ──
    women = WomanHistory.query.filter_by(patient_id=pid).first()
    if women is not None:
        records = WomenHealthRecord.query.filter_by(patient_id=pid).all()
        live_types = {r.record_type for r in records if (r.status or "Current") == "Current"}
        refs = {r.legacy_ref for r in records if r.legacy_ref}
        when, recorded = _stamp_from_legacy(women)

        if women.pregnant and "Pregnancy" not in live_types and "pregnant" not in refs:
            created.append(("womens_health", WomenHealthRecord(
                patient_id=pid, record_type="Pregnancy", due_date=women.due_date,
                status="Current", recorded_date=recorded, created_at=when, legacy_ref="pregnant",
                created_by=None, created_by_role="legacy", version=1,
            )))
        if women.nursing_child and "Nursing" not in live_types and "nursing_child" not in refs:
            created.append(("womens_health", WomenHealthRecord(
                patient_id=pid, record_type="Nursing", details="Nursing a child",
                status="Current", recorded_date=recorded, created_at=when, legacy_ref="nursing_child",
                created_by=None, created_by_role="legacy", version=1,
            )))

    if not created:
        return 0

    for _, record in created:
        db.session.add(record)
    db.session.flush()          # assigns ids; raises IntegrityError on a duplicate carry-over
    for section_key, record in created:
        section = SECTIONS[section_key]
        _audit(pid, section_key, record.id, "IMPORT",
               f"Carried over from the earlier patient form: {section.summary(record)}",
               LEGACY_ACTOR, after=section.serialize(record))
    return len(created)


def _set(obj, attr, value):
    """Assign only when the value really differs (avoids pointless UPDATEs)."""
    current = getattr(obj, attr)
    if isinstance(value, bool):
        current = bool(current)
    if current != value:
        setattr(obj, attr, value)


def _project_conditions(pid):
    records = MedicalConditionRecord.query.filter_by(patient_id=pid).order_by(MedicalConditionRecord.id).all()
    medical = MedicalHistory.query.filter_by(patient_id=pid).first()
    if medical is None:
        if not records:
            return
        medical = MedicalHistory(patient_id=pid, recorded_date=ist_today())
        db.session.add(medical)

    live = [r for r in records if (r.status or "Current") != "Resolved"]
    live_keys = {r.condition_key for r in live}
    for key, _ in CONDITION_OPTIONS:
        _set(medical, key, key in live_keys)
    other = "; ".join(_join(r.condition_name, r.details) for r in live if r.condition_key == "other")
    _set(medical, "other", other or None)
    if records:
        _set(medical, "no_known_conditions", False)


def _habit_text(record):
    return _join(record.details, record.frequency, record.duration, sep=", ") or "Yes"


def _project_habits(pid):
    records = HabitRecord.query.filter_by(patient_id=pid).order_by(HabitRecord.id).all()
    habit = Habit.query.filter_by(patient_id=pid).first()
    if habit is None:
        if not records:
            return
        habit = Habit(patient_id=pid, recorded_date=ist_today())
        db.session.add(habit)

    live = [r for r in records if (r.status or "Current") != "Former"]
    for key, _ in HABIT_OPTIONS:
        texts = [_habit_text(r) for r in live if r.habit_key == key]
        _set(habit, key, "; ".join(texts) or None)
    if records:
        _set(habit, "no_habits", False)


def _project_women(pid):
    records = WomenHealthRecord.query.filter_by(patient_id=pid).order_by(WomenHealthRecord.id).all()
    women = WomanHistory.query.filter_by(patient_id=pid).first()
    if women is None:
        if not records:
            return
        women = WomanHistory(patient_id=pid, recorded_date=ist_today())
        db.session.add(women)

    live = [r for r in records if (r.status or "Current") == "Current"]
    pregnancies = [r for r in live if r.record_type == "Pregnancy"]
    _set(women, "pregnant", bool(pregnancies))
    _set(women, "due_date", pregnancies[-1].due_date if pregnancies else None)
    _set(women, "nursing_child", any(r.record_type == "Nursing" for r in live))


def _project_allergies(patient):
    if patient.no_known_allergies and AllergyRecord.query.filter_by(patient_id=patient.id).count():
        patient.no_known_allergies = False


def _project(patient, section_key=None):
    """Rewrite the old one-row summary tables from the records."""
    if section_key in (None, "conditions"):
        _project_conditions(patient.id)
    if section_key in (None, "habits"):
        _project_habits(patient.id)
    if section_key in (None, "womens_health"):
        _project_women(patient.id)
    if section_key in (None, "allergies"):
        _project_allergies(patient)


def sync_patient_history(patient):
    """Bring one patient fully up to date. Called before every read/write.

    The old tables are only ever rewritten in the same transaction in which
    the carry-over check has just succeeded, so an old value can never be
    cleared unless a record for it exists."""
    pid = patient.id
    for attempt in (1, 2):
        try:
            _import_legacy(patient)
            db.session.flush()
            _project(patient)
            db.session.commit()
            return patient
        except IntegrityError:
            # Two requests carried the same old value over at the same moment;
            # the database kept exactly one copy. Look again: the records are
            # there now, so the second pass has nothing left to insert.
            db.session.rollback()
            patient = db.session.get(Patient, pid)
            if attempt == 2:
                raise
    return patient


def migrate_all_patients():
    """Optional: carry over every patient's old data in one go (for example
    right after deployment) instead of patient-by-patient on first opening.
    Returns the number of patients processed."""
    ensure_medical_history_schema()
    count = 0
    for (pid,) in db.session.query(Patient.id).all():
        patient = db.session.get(Patient, pid)
        if patient is not None:
            sync_patient_history(patient)
            count += 1
    return count


# ══════════════════════════════════════════════════════════════
#  "NO KNOWN …" TICK BOXES
#  A per-patient acknowledgement, not a record. Only meaningful while
#  the section is empty; adding a record clears it automatically.
# ══════════════════════════════════════════════════════════════
NONE_KNOWN_SECTIONS = ("conditions", "allergies", "habits")


def _none_known(patient):
    pid = patient.id
    medical = MedicalHistory.query.filter_by(patient_id=pid).first()
    habit = Habit.query.filter_by(patient_id=pid).first()
    return {
        "conditions": bool(medical and medical.no_known_conditions)
                      and not MedicalConditionRecord.query.filter_by(patient_id=pid).count(),
        "allergies": bool(patient.no_known_allergies)
                     and not AllergyRecord.query.filter_by(patient_id=pid).count(),
        "habits": bool(habit and habit.no_habits)
                  and not HabitRecord.query.filter_by(patient_id=pid).count(),
    }


def _write_none_known(patient, section_key, value):
    pid = patient.id
    if section_key == "allergies":
        patient.no_known_allergies = bool(value)
    elif section_key == "conditions":
        medical = MedicalHistory.query.filter_by(patient_id=pid).first()
        if medical is None:
            if not value:
                return
            medical = MedicalHistory(patient_id=pid, recorded_date=ist_today())
            db.session.add(medical)
        medical.no_known_conditions = bool(value)
    elif section_key == "habits":
        habit = Habit.query.filter_by(patient_id=pid).first()
        if habit is None:
            if not value:
                return
            habit = Habit(patient_id=pid, recorded_date=ist_today())
            db.session.add(habit)
        habit.no_habits = bool(value)


def set_none_known(patient, section, value, actor, commit=True):
    if section.key not in NONE_KNOWN_SECTIONS:
        raise HistoryError("This section has no \"none known\" option.")
    value = bool(value)
    if value and section.query(patient.id).count():
        raise HistoryError(
            "This section already has records. Delete them first if the patient really has none.", 409)
    was = _none_known(patient)[section.key]
    _write_none_known(patient, section.key, value)
    if was != value:
        _audit(patient.id, section.key, None, "NONE_KNOWN",
               f"\"No known {section.noun}\" {'ticked' if value else 'cleared'}", actor)
    if commit:
        db.session.commit()
    return value


# ══════════════════════════════════════════════════════════════
#  CORE OPERATIONS
# ══════════════════════════════════════════════════════════════
def _find(section, patient_id, record_id):
    """The record is looked up by ITS OWN id, scoped to the patient."""
    record = section.model.query.filter_by(id=record_id, patient_id=patient_id).first()
    if record is None:
        raise HistoryError(
            f"This {section.noun} record no longer exists. It may have been deleted by another user.", 404)
    return record


def create_record(patient, section, data, actor, commit=True):
    """ADD — always inserts a brand-new row. Never updates, merges or
    replaces anything that is already there."""
    if section.female_only and not _is_female(patient):
        raise HistoryError("Women's health records apply to female patients only.")

    values = clean_fields(section, data, creating=True)
    if section.prepare:
        section.prepare(values, data, None)

    record = section.model(patient_id=patient.id, **values)
    record.created_at = datetime.utcnow()
    record.created_by = actor.get("name")
    record.created_by_role = actor.get("role")
    record.updated_at = None
    record.updated_by = None
    record.updated_by_role = None
    record.version = 1
    db.session.add(record)
    db.session.flush()

    if section.key in NONE_KNOWN_SECTIONS:
        _write_none_known(patient, section.key, False)

    _audit(patient.id, section.key, record.id, "CREATE",
           f"Added {section.noun}: {section.summary(record)}", actor, after=section.serialize(record))
    _project(patient, section.key)
    if commit:
        db.session.commit()
    return record


def update_record(patient, section, record_id, data, actor):
    """UPDATE — changes exactly one row, the one with this id."""
    record = _find(section, patient.id, record_id)

    sent_version = data.get("version")
    if sent_version not in (None, ""):
        try:
            sent_version = int(sent_version)
        except (TypeError, ValueError):
            raise HistoryError("Invalid record version.")
        if sent_version != (record.version or 1):
            raise HistoryError(
                "This record was changed by someone else while you were editing it. "
                "The latest values are shown now — please check them and make your change again.",
                409, {"conflict": True, "record": section.serialize(record)})

    values = clean_fields(section, data, creating=False)
    if section.prepare:
        section.prepare(values, data, record)

    before = section.serialize(record)
    changed = False
    for attr, value in values.items():
        if getattr(record, attr) != value:
            setattr(record, attr, value)
            changed = True

    if not changed:
        return record, False

    # created_at / created_by are deliberately left alone.
    record.updated_at = datetime.utcnow()
    record.updated_by = actor.get("name")
    record.updated_by_role = actor.get("role")
    record.version = (record.version or 1) + 1
    db.session.flush()

    _audit(patient.id, section.key, record.id, "UPDATE",
           f"Updated {section.noun}: {section.summary(record)}", actor,
           before=before, after=section.serialize(record))
    _project(patient, section.key)
    db.session.commit()
    return record, True


def delete_record(patient, section, record_id, actor):
    """DELETE — removes exactly one row, the one with this id."""
    record = _find(section, patient.id, record_id)
    before = section.serialize(record)

    _audit(patient.id, section.key, record.id, "DELETE",
           f"Deleted {section.noun}: {section.summary(record)}", actor, before=before)
    db.session.delete(record)
    db.session.flush()
    _project(patient, section.key)
    db.session.commit()
    return before


def create_initial_history(patient, payload, actor):
    """Used when a NEW patient is registered: saves the history entered on
    the registration form in the same transaction as the patient, so the
    patient and their history are stored together or not at all.
    Does not commit. Raises HistoryError on bad input."""
    payload = payload or {}
    for key in SECTION_ORDER:
        section = SECTIONS[key]
        rows = payload.get(key) or payload.get(section.slug) or []
        if not isinstance(rows, list):
            raise HistoryError(f"{section.noun.capitalize()} records must be a list.")
        if section.female_only and not _is_female(patient):
            continue
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            try:
                create_record(patient, section, row, actor, commit=False)
            except HistoryError as err:
                raise HistoryError(f"{section.noun.capitalize()} #{index}: {err.message}", err.status)

    none_known = payload.get("none_known") or {}
    for key in NONE_KNOWN_SECTIONS:
        if none_known.get(key) and not SECTIONS[key].query(patient.id).count():
            set_none_known(patient, SECTIONS[key], True, actor, commit=False)


# ══════════════════════════════════════════════════════════════
#  RESPONSES
# ══════════════════════════════════════════════════════════════
def build_history_payload(patient):
    pid = patient.id
    payload = {
        "patient_id": pid,
        "gender": patient.gender,
        "womens_health_applicable": _is_female(patient),
    }
    for key in SECTION_ORDER:
        section = SECTIONS[key]
        payload[key] = [section.serialize(r) for r in section.query(pid).all()]
    payload["none_known"] = _none_known(patient)

    # Same shapes the older endpoints return, for screens that still want them.
    medical = MedicalHistory.query.filter_by(patient_id=pid).first()
    habit = Habit.query.filter_by(patient_id=pid).first()
    women = WomanHistory.query.filter_by(patient_id=pid).first()
    payload["legacy"] = {
        "medical": medical.to_dict() if medical else {},
        "habits": habit.to_dict() if habit else {},
        "women": women.to_dict() if women else {},
        "allergy": {"rows": payload["allergies"]},
        "medications": payload["medications"],
    }
    return payload


def _error_response(err):
    body = {"error": err.message}
    body.update(err.extra)
    return jsonify(body), err.status


def _load(patient_id, slug=None):
    """(patient, section) with the patient's history brought up to date."""
    section = get_section(slug) if slug is not None else None
    patient = db.session.get(Patient, patient_id)
    if patient is None:
        raise HistoryError("Patient not found.", 404)
    patient = sync_patient_history(patient)
    return patient, section


def _body():
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else {}


def _guard(fn):
    """HistoryError -> clean JSON error; anything else -> rollback + 500."""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HistoryError as err:
            db.session.rollback()
            return _error_response(err)
        except Exception as exc:
            db.session.rollback()
            traceback.print_exc()
            return jsonify({"error": "Could not save medical history.", "detail": str(exc)}), 500

    return wrapped


# ══════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════
def register_medical_history_routes(bp):
    """Attach every medical-history route to the patients blueprint
    (url_prefix="/api/patients")."""

    bp.before_app_request(_ensure_schema_before_request)

    # ── Everything for one patient ───────────────────────────
    @bp.route("/<int:patient_id>/medical-history", methods=["GET"], endpoint="mh_get_all")
    @history_access
    @_guard
    def mh_get_all(patient_id):
        patient, _ = _load(patient_id)
        return jsonify(build_history_payload(patient)), 200

    # ── Change log ───────────────────────────────────────────
    @bp.route("/<int:patient_id>/medical-history/audit", methods=["GET"], endpoint="mh_audit")
    @history_access
    @_guard
    def mh_audit(patient_id):
        if db.session.get(Patient, patient_id) is None:
            raise HistoryError("Patient not found.", 404)
        rows = (MedicalHistoryAudit.query
                .filter_by(patient_id=patient_id)
                .order_by(MedicalHistoryAudit.id.desc())
                .limit(300)
                .all())
        return jsonify([r.to_dict() for r in rows]), 200

    # ── One section: list / ADD ──────────────────────────────
    @bp.route("/<int:patient_id>/medical-history/<string:slug>", methods=["GET"], endpoint="mh_list")
    @history_access
    @_guard
    def mh_list(patient_id, slug):
        patient, section = _load(patient_id, slug)
        return jsonify([section.serialize(r) for r in section.query(patient.id).all()]), 200

    @bp.route("/<int:patient_id>/medical-history/<string:slug>", methods=["POST"], endpoint="mh_add")
    @history_access
    @_guard
    def mh_add(patient_id, slug):
        patient, section = _load(patient_id, slug)
        record = create_record(patient, section, _body(), current_actor())
        return jsonify({
            "status": f"{section.noun.capitalize()} added",
            "record": section.serialize(record),
        }), 201

    # ── One record: read / UPDATE / DELETE ───────────────────
    @bp.route("/<int:patient_id>/medical-history/<string:slug>/<int:record_id>",
              methods=["GET"], endpoint="mh_get_one")
    @history_access
    @_guard
    def mh_get_one(patient_id, slug, record_id):
        patient, section = _load(patient_id, slug)
        return jsonify(section.serialize(_find(section, patient.id, record_id))), 200

    @bp.route("/<int:patient_id>/medical-history/<string:slug>/<int:record_id>",
              methods=["PUT", "PATCH"], endpoint="mh_update")
    @history_access
    @_guard
    def mh_update(patient_id, slug, record_id):
        patient, section = _load(patient_id, slug)
        record, changed = update_record(patient, section, record_id, _body(), current_actor())
        return jsonify({
            "status": f"{section.noun.capitalize()} updated" if changed else "No changes",
            "changed": changed,
            "record": section.serialize(record),
        }), 200

    @bp.route("/<int:patient_id>/medical-history/<string:slug>/<int:record_id>",
              methods=["DELETE"], endpoint="mh_delete")
    @history_access
    @_guard
    def mh_delete(patient_id, slug, record_id):
        patient, section = _load(patient_id, slug)
        deleted = delete_record(patient, section, record_id, current_actor())
        return jsonify({
            "status": f"{section.noun.capitalize()} deleted",
            "deleted": deleted,
            "remaining": section.query(patient.id).count(),
        }), 200

    # ── "No known …" tick box ────────────────────────────────
    @bp.route("/<int:patient_id>/medical-history/<string:slug>/none-known",
              methods=["PUT", "POST"], endpoint="mh_none_known")
    @history_access
    @_guard
    def mh_none_known(patient_id, slug):
        patient, section = _load(patient_id, slug)
        data = _body()
        value = set_none_known(patient, section, _to_bool(data.get("none_known", data.get("value", True))),
                               current_actor())
        return jsonify({"section": section.key, "none_known": value}), 200

    # ══════════════════════════════════════════════════════════
    #  EARLIER PER-RECORD URLS (kept so anything still calling them
    #  keeps working). They run through exactly the same code as the
    #  routes above, so they follow the same rules and are logged.
    #
    #    /<id>/medications            GET, POST
    #    /<id>/medications/<med_id>   PUT, DELETE
    #    /<id>/allergies              POST
    #    /<id>/allergies/<allergy_id> PUT, DELETE
    # ══════════════════════════════════════════════════════════
    @bp.route("/<int:patient_id>/medications", methods=["GET"], endpoint="get_medications")
    @history_access
    @_guard
    def get_medications(patient_id):
        patient, section = _load(patient_id, "medications")
        rows = Medication.query.filter_by(patient_id=patient.id).order_by(Medication.medicine_name).all()
        return jsonify([section.serialize(r) for r in rows]), 200

    @bp.route("/<int:patient_id>/medications", methods=["POST"], endpoint="add_medication")
    @history_access
    @_guard
    def add_medication(patient_id):
        patient, section = _load(patient_id, "medications")
        record = create_record(patient, section, _body(), current_actor())
        return jsonify({
            "status": "Medication added successfully",
            "medication_id": record.id,
            "record": section.serialize(record),
        }), 201

    @bp.route("/<int:patient_id>/medications/<int:medication_id>", methods=["PUT"], endpoint="update_medication")
    @history_access
    @_guard
    def update_medication(patient_id, medication_id):
        patient, section = _load(patient_id, "medications")
        record, _ = update_record(patient, section, medication_id, _body(), current_actor())
        return jsonify({"status": "Medication updated", "record": section.serialize(record)}), 200

    @bp.route("/<int:patient_id>/medications/<int:medication_id>", methods=["DELETE"], endpoint="delete_medication")
    @history_access
    @_guard
    def delete_medication(patient_id, medication_id):
        patient, section = _load(patient_id, "medications")
        delete_record(patient, section, medication_id, current_actor())
        return jsonify({"status": "Medication deleted"}), 200

    @bp.route("/<int:patient_id>/allergies", methods=["POST"], endpoint="add_single_allergy")
    @history_access
    @_guard
    def add_single_allergy(patient_id):
        patient, section = _load(patient_id, "allergies")
        record = create_record(patient, section, _body(), current_actor())
        return jsonify({"status": "Allergy added", "allergy": section.serialize(record)}), 201

    @bp.route("/<int:patient_id>/allergies/<int:allergy_id>", methods=["PUT"], endpoint="update_single_allergy")
    @history_access
    @_guard
    def update_single_allergy(patient_id, allergy_id):
        patient, section = _load(patient_id, "allergies")
        record, _ = update_record(patient, section, allergy_id, _body(), current_actor())
        return jsonify({"status": "Allergy updated", "allergy": section.serialize(record)}), 200

    @bp.route("/<int:patient_id>/allergies/<int:allergy_id>", methods=["DELETE"], endpoint="delete_single_allergy")
    @history_access
    @_guard
    def delete_single_allergy(patient_id, allergy_id):
        patient, section = _load(patient_id, "allergies")
        delete_record(patient, section, allergy_id, current_actor())
        return jsonify({
            "status": "Allergy deleted",
            "remaining": section.query(patient.id).count(),
        }), 200