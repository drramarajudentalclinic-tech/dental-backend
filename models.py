from datetime import datetime, timedelta, timezone
from database import db
from sqlalchemy import Numeric
from werkzeug.security import generate_password_hash, check_password_hash


# ═══════════════════════════════════════════════════════════════
#  CLINIC TIME (Asia/Kolkata) + RECORD STAMPS
#  Timestamps are stored in UTC, like every other table in this file,
#  and converted to clinic time when they are sent to the screen.
#  India has no daylight saving, so a fixed +05:30 offset is exact and
#  needs no timezone database on the server.
# ═══════════════════════════════════════════════════════════════
IST = timezone(timedelta(hours=5, minutes=30), "Asia/Kolkata")


def ist_now():
    return datetime.now(IST)


def ist_today():
    """Today's date at the clinic (not the server's date)."""
    return ist_now().date()


def to_ist(dt):
    """Stored (naive UTC) datetime -> timezone-aware clinic time."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_iso(dt):
    """e.g. 2026-10-07T12:15:00+05:30"""
    local = to_ist(dt)
    return local.isoformat(timespec="seconds") if local else None


def ist_display(dt):
    """e.g. 07-10-2026 12:15 PM"""
    local = to_ist(dt)
    return local.strftime("%d-%m-%Y %I:%M %p") if local else None


ROLE_LABELS = {
    "doctor": "Doctor",
    "reception": "Receptionist",
    "admin": "Admin",
    "legacy": "Earlier patient form",
}


def actor_label(name, role):
    """"Receptionist – Ramesh", "Doctor – Rama Raju", or None."""
    role_label = ROLE_LABELS.get((role or "").lower())
    if role == "legacy":
        return role_label
    if name and role_label:
        return f"{role_label} – {name}"
    return name or role_label


class ActorStampMixin:
    """Who created / last changed a record, plus a change counter.

    `version` goes up by one on every update. The screen sends back the
    version it loaded, so two people editing the same record at the same
    time cannot silently overwrite each other."""

    created_by      = db.Column(db.String(100))
    created_by_role = db.Column(db.String(30))
    updated_by      = db.Column(db.String(100))
    updated_by_role = db.Column(db.String(30))
    version         = db.Column(db.Integer, default=1)

    def was_updated(self):
        created = getattr(self, "created_at", None)
        updated = getattr(self, "updated_at", None)
        if self.updated_by:
            return True
        if not updated:
            return False
        if not created:
            return False
        # Older tables fill updated_at at insert time; ignore that.
        return (updated - created) > timedelta(seconds=2)

    def stamp_dict(self):
        created = getattr(self, "created_at", None)
        updated = getattr(self, "updated_at", None) if self.was_updated() else None
        return {
            "version":            self.version or 1,
            "created_at":         ist_iso(created),
            "created_at_display": ist_display(created),
            "created_by":         self.created_by,
            "created_by_role":    self.created_by_role,
            "created_by_label":   actor_label(self.created_by, self.created_by_role),
            "updated_at":         ist_iso(updated),
            "updated_at_display": ist_display(updated),
            "updated_by":         self.updated_by if updated else None,
            "updated_by_role":    self.updated_by_role if updated else None,
            "updated_by_label":   actor_label(self.updated_by, self.updated_by_role) if updated else None,
        }


class RecordStampMixin(ActorStampMixin):
    """Full stamp set for the new medical-history tables.
    updated_at stays empty until the record is really edited."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=True)


# ═══════════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(
    db.String(20),
    nullable=False,
    default="reception"
)
# reception
# doctor
# admin

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ═══════════════════════════════════════════════════════════════
#  PATIENT
# ═══════════════════════════════════════════════════════════════
class Patient(db.Model):
    __tablename__ = "patients"

    id             = db.Column(db.Integer, primary_key=True)
    case_number    = db.Column(db.String(50), unique=True, nullable=False)
    name           = db.Column(db.String(150), nullable=False)
    date           = db.Column(db.Date, nullable=True)
    age            = db.Column(db.Integer, nullable=False)
    date_of_birth  = db.Column(db.Date, nullable=True)
    gender         = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20))
    mobile         = db.Column(db.String(20), nullable=False)
    email          = db.Column(db.String(150))
    blood_group    = db.Column(db.String(10))
    address        = db.Column(db.Text)
    profession     = db.Column(db.String(100))
    referred_by    = db.Column(db.String(150))
    chief_complaint= db.Column(db.Text)
    no_known_allergies = db.Column(db.Boolean, default=False, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, onupdate=datetime.utcnow)

        # Relationships
    visits = db.relationship(
        "Visit",
        backref="patient",
        lazy=True
    )

    medical = db.relationship(
        "MedicalHistory",
        backref="patient",
        uselist=False
    )

    allergies = db.relationship(
        "AllergyRecord",
        back_populates="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )

    habits = db.relationship(
        "Habit",
        backref="patient",
        lazy=True
    )

    medications = db.relationship(
        "Medication",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )

    women_history = db.relationship(
        "WomanHistory",
        backref="patient",
        uselist=False
    )

    family_doctor = db.relationship(
        "FamilyDoctor",
        backref="patient",
        uselist=False
    )

    consent = db.relationship(
        "Consent",
        backref="patient",
        uselist=False
    )
is_active = db.Column(
    db.Boolean,
    default=True
)

last_visit_date = db.Column(
    db.DateTime
)

total_visits = db.Column(
    db.Integer,
    default=0
)

# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
#  FAMILY DOCTOR
# ═══════════════════════════════════════════════════════════════
class FamilyDoctor(db.Model):
    __tablename__ = "family_doctors"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        unique=True,
        nullable=False
    )

    doctor_name = db.Column(db.String(150))
    doctor_phone = db.Column(db.String(50))
    doctor_address = db.Column(db.Text)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "doctor_name": self.doctor_name or "",
            "doctor_phone": self.doctor_phone or "",
            "doctor_address": self.doctor_address or "",
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            ),
        }
        
        # ═══════════════════════════════════════════════════════════════
#  CONSENT
# ═══════════════════════════════════════════════════════════════
class Consent(db.Model):
    __tablename__ = "consents"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        unique=True,
        nullable=False
    )

    agreed = db.Column(db.Boolean, default=False)
    signature = db.Column(db.String(200))
    relationship = db.Column(db.String(100))
    consent_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "agreed": bool(self.agreed),
            "signature": self.signature or "",
            "relationship": self.relationship or "",
            "consent_date": (
                self.consent_date.isoformat()
                if self.consent_date else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            ),
        }
# ═══════════════════════════════════════════════════════════════
#  MEDICAL HISTORY
# ═══════════════════════════════════════════════════════════════
class MedicalHistory(db.Model):
    __tablename__ = "medical_history"

    id                      = db.Column(db.Integer, primary_key=True)
    patient_id              = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False)

    aids                    = db.Column(db.Boolean, default=False)
    asthma                  = db.Column(db.Boolean, default=False)
    arthritis_rheumatism    = db.Column(db.Boolean, default=False)
    blood_disease           = db.Column(db.Boolean, default=False)
    bp_high                 = db.Column(db.Boolean, default=False)
    bp_low                  = db.Column(db.Boolean, default=False)
    corticosteroid_treatment= db.Column(db.Boolean, default=False)
    cancer                  = db.Column(db.Boolean, default=False)
    diabetes                = db.Column(db.Boolean, default=False)
    epilepsy                = db.Column(db.Boolean, default=False)
    heart_problems          = db.Column(db.Boolean, default=False)
    hepatitis               = db.Column(db.Boolean, default=False)
    herpes                  = db.Column(db.Boolean, default=False)
    jaundice                = db.Column(db.Boolean, default=False)
    liver_disease           = db.Column(db.Boolean, default=False)
    kidney_disease          = db.Column(db.Boolean, default=False)
    psychiatric_treatment   = db.Column(db.Boolean, default=False)
    radiation_treatment     = db.Column(db.Boolean, default=False)
    respiratory_disease     = db.Column(db.Boolean, default=False)
    rheumatic_fever         = db.Column(db.Boolean, default=False)
    tb                      = db.Column(db.Boolean, default=False)
    thyroid_problems        = db.Column(db.Boolean, default=False)
    ulcer                   = db.Column(db.Boolean, default=False)
    venereal_disease        = db.Column(db.Boolean, default=False)
    other                   = db.Column(db.Text)
    no_known_conditions     = db.Column(db.Boolean, default=False, nullable=False)
    recorded_date           = db.Column(db.Date, nullable=True)
    updated_at              = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "aids":                     self.aids,
            "asthma":                   self.asthma,
            "arthritis_rheumatism":     self.arthritis_rheumatism,
            "blood_disease":            self.blood_disease,
            "bp_high":                  self.bp_high,
            "bp_low":                   self.bp_low,
            "corticosteroid_treatment": self.corticosteroid_treatment,
            "cancer":                   self.cancer,
            "diabetes":                 self.diabetes,
            "epilepsy":                 self.epilepsy,
            "heart_problems":           self.heart_problems,
            "hepatitis":                self.hepatitis,
            "herpes":                   self.herpes,
            "jaundice":                 self.jaundice,
            "liver_disease":            self.liver_disease,
            "kidney_disease":           self.kidney_disease,
            "psychiatric_treatment":    self.psychiatric_treatment,
            "radiation_treatment":      self.radiation_treatment,
            "respiratory_disease":      self.respiratory_disease,
            "rheumatic_fever":          self.rheumatic_fever,
            "tb":                       self.tb,
            "thyroid_problems":         self.thyroid_problems,
            "ulcer":                    self.ulcer,
            "venereal_disease":         self.venereal_disease,
            "other":                    self.other,
            "no_known_conditions":      self.no_known_conditions,
            "recorded_date":            self.recorded_date.isoformat() if self.recorded_date else None,
        }


# ═══════════════════════════════════════════════════════════════
#  ALLERGY RECORDS — one row per allergy, many rows per patient.
#  Shared by Doctor and Reception; every row is added / edited /
#  deleted on its own through medical_history.py.
# ═══════════════════════════════════════════════════════════════

class AllergyRecord(ActorStampMixin, db.Model):
    __tablename__ = "allergy_records"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    allergy_type = db.Column(
        db.String(50),
        nullable=False
    )
    # Drug / Food / Environmental / Anesthesia / Latex / Iodine /
    # Insect / Skin / Other

    allergen = db.Column(db.String(255), nullable=False)

    reaction = db.Column(db.String(255))

    severity = db.Column(db.String(50))

    # Active / Resolved  (empty on rows created before this column existed
    # — those are treated as Active)
    status = db.Column(db.String(20))

    notes = db.Column(db.Text)

    recorded_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    patient = db.relationship(
        "Patient",
        backref=db.backref(
            "allergy_records",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "type": self.allergy_type,
            "allergen": self.allergen,
            "reaction": self.reaction,
            "severity": self.severity,
            "status": self.status or "Active",
            "notes": self.notes,
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
            **self.stamp_dict(),
        }
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
#  HABITS
# ═══════════════════════════════════════════════════════════════
class Habit(db.Model):
    __tablename__ = "habits"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        unique=True,
        nullable=False
    )

    # Store habit details (None = No, Text = Yes + Details)
    smoking = db.Column(db.Text)
    alcohol = db.Column(db.Text)
    tobacco = db.Column(db.Text)
    pan_chewing = db.Column(db.Text)
    spicy_foods = db.Column(db.Text)

    # If checked, all other habits should be empty
    no_habits = db.Column(db.Boolean, default=False)

    recorded_date = db.Column(db.Date, nullable=True)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "smoking": bool(self.smoking),
            "smoking_detail": self.smoking or "",

            "alcohol": bool(self.alcohol),
            "alcohol_detail": self.alcohol or "",

            "tobacco": bool(self.tobacco),
            "tobacco_detail": self.tobacco or "",

            "pan_chewing": bool(self.pan_chewing),
            "pan_chewing_detail": self.pan_chewing or "",

            "spicy_foods": bool(self.spicy_foods),
            "spicy_foods_detail": self.spicy_foods or "",

            "no_habits": bool(self.no_habits),

            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }
    # ═══════════════════════════════════════════════════════════════
# MEDICATIONS
# ═══════════════════════════════════════════════════════════════

class Medication(ActorStampMixin, db.Model):
    __tablename__ = "medications"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    medicine_name = db.Column(db.String(200), nullable=False)

    dosage = db.Column(db.String(100))

    frequency = db.Column(db.String(100))

    route = db.Column(db.String(50))

    duration = db.Column(db.String(100))

    # Reason / indication
    purpose = db.Column(db.String(200))

    prescribed_by = db.Column(db.String(200))

    start_date = db.Column(db.Date, nullable=True)

    end_date = db.Column(db.Date, nullable=True)

    notes = db.Column(db.Text)

    # Status: True = currently taking, False = stopped
    active = db.Column(db.Boolean, default=True)

    recorded_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "route": self.route,
            "duration": self.duration,
            "purpose": self.purpose,
            "prescribed_by": self.prescribed_by,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "notes": self.notes,
            "active": self.active is not False,
            "status": "Stopped" if self.active is False else "Active",
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
            **self.stamp_dict(),
        }
    
class WomanHistory(db.Model):
    __tablename__ = "woman_history"

    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False)
    pregnant      = db.Column(db.Boolean, default=False)
    due_date      = db.Column(db.Date, nullable=True)
    nursing_child = db.Column(db.Boolean, default=False)
    recorded_date = db.Column(db.Date, nullable=True)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "pregnant":      self.pregnant,
            "due_date":      self.due_date.isoformat() if self.due_date else None,
            "nursing_child": self.nursing_child,
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
        }


# ═══════════════════════════════════════════════════════════════
#  MEDICAL HISTORY — RECORD-LEVEL TABLES
#
#  One row per medical condition / habit / women's-health entry, so a
#  patient can have any number of each and every row can be added,
#  edited and deleted on its own by Doctor or Reception.
#
#  These three tables are the source of truth. MedicalHistory, Habit
#  and WomanHistory above (one row per patient) are kept as an
#  automatically maintained summary so existing screens, alerts and
#  print-outs that read them keep working — see medical_history.py.
#
#  legacy_ref is set only on rows that were carried over from those
#  older one-row-per-patient tables; the unique constraint guarantees
#  that carrying the same old value over twice can never create a
#  duplicate. Rows people add through the screen leave it empty.
# ═══════════════════════════════════════════════════════════════
class MedicalConditionRecord(RecordStampMixin, db.Model):
    __tablename__ = "medical_condition_records"
    __table_args__ = (
        db.UniqueConstraint("patient_id", "legacy_ref", name="uq_condition_legacy_ref"),
    )

    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    # One of the MedicalHistory column names (diabetes, bp_high, …) or "other"
    condition_key  = db.Column(db.String(50), nullable=False)
    condition_name = db.Column(db.String(255), nullable=False)
    details       = db.Column(db.Text)
    status        = db.Column(db.String(20), default="Current")   # Current / Controlled / Resolved
    since         = db.Column(db.String(100))
    notes         = db.Column(db.Text)
    recorded_date = db.Column(db.Date, nullable=True)
    legacy_ref    = db.Column(db.String(60), nullable=True)

    def to_dict(self):
        return {
            "id":             self.id,
            "patient_id":     self.patient_id,
            "condition_key":  self.condition_key,
            "condition_name": self.condition_name,
            "details":        self.details,
            "status":         self.status or "Current",
            "since":          self.since,
            "notes":          self.notes,
            "recorded_date":  self.recorded_date.isoformat() if self.recorded_date else None,
            **self.stamp_dict(),
        }


class HabitRecord(RecordStampMixin, db.Model):
    __tablename__ = "habit_records"
    __table_args__ = (
        db.UniqueConstraint("patient_id", "legacy_ref", name="uq_habit_legacy_ref"),
    )

    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    # One of the Habit column names (smoking, alcohol, …) or "other"
    habit_key     = db.Column(db.String(50), nullable=False)
    habit_name    = db.Column(db.String(150), nullable=False)
    details       = db.Column(db.Text)
    frequency     = db.Column(db.String(100))
    duration      = db.Column(db.String(100))
    status        = db.Column(db.String(20), default="Current")   # Current / Occasional / Former
    notes         = db.Column(db.Text)
    recorded_date = db.Column(db.Date, nullable=True)
    legacy_ref    = db.Column(db.String(60), nullable=True)

    def to_dict(self):
        return {
            "id":            self.id,
            "patient_id":    self.patient_id,
            "habit_key":     self.habit_key,
            "habit_name":    self.habit_name,
            "details":       self.details,
            "frequency":     self.frequency,
            "duration":      self.duration,
            "status":        self.status or "Current",
            "notes":         self.notes,
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
            **self.stamp_dict(),
        }


class WomenHealthRecord(RecordStampMixin, db.Model):
    __tablename__ = "women_health_records"
    __table_args__ = (
        db.UniqueConstraint("patient_id", "legacy_ref", name="uq_women_legacy_ref"),
    )

    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    # Pregnancy / Nursing / Menstrual history / Menopause / Gynecological / Other
    record_type   = db.Column(db.String(50), nullable=False)
    details       = db.Column(db.Text)
    lmp_date      = db.Column(db.Date, nullable=True)
    due_date      = db.Column(db.Date, nullable=True)
    status        = db.Column(db.String(20), default="Current")   # Current / Past
    notes         = db.Column(db.Text)
    recorded_date = db.Column(db.Date, nullable=True)
    legacy_ref    = db.Column(db.String(60), nullable=True)

    def to_dict(self):
        return {
            "id":            self.id,
            "patient_id":    self.patient_id,
            "record_type":   self.record_type,
            "details":       self.details,
            "lmp_date":      self.lmp_date.isoformat() if self.lmp_date else None,
            "due_date":      self.due_date.isoformat() if self.due_date else None,
            "status":        self.status or "Current",
            "notes":         self.notes,
            "recorded_date": self.recorded_date.isoformat() if self.recorded_date else None,
            **self.stamp_dict(),
        }


# ═══════════════════════════════════════════════════════════════
#  MEDICAL HISTORY CHANGE LOG
#  One row for every add / update / delete of a medical-history record
#  (same idea as VisitAudit). A deleted record's last values stay
#  readable here, so nothing disappears without a trace.
# ═══════════════════════════════════════════════════════════════
class MedicalHistoryAudit(db.Model):
    __tablename__ = "medical_history_audit"

    id                = db.Column(db.Integer, primary_key=True)
    patient_id        = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    section           = db.Column(db.String(30), nullable=False)
    record_id         = db.Column(db.Integer, nullable=True)
    # CREATE / UPDATE / DELETE / IMPORT / NONE_KNOWN
    action            = db.Column(db.String(20), nullable=False)
    summary           = db.Column(db.String(300))
    before_json       = db.Column(db.Text)
    after_json        = db.Column(db.Text)
    performed_by      = db.Column(db.String(100))
    performed_by_role = db.Column(db.String(30))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id":                 self.id,
            "patient_id":         self.patient_id,
            "section":            self.section,
            "record_id":          self.record_id,
            "action":             self.action,
            "summary":            self.summary,
            "performed_by":       self.performed_by,
            "performed_by_role":  self.performed_by_role,
            "performed_by_label": actor_label(self.performed_by, self.performed_by_role),
            "at":                 ist_iso(self.created_at),
            "at_display":         ist_display(self.created_at),
        }


# ═══════════════════════════════════════════════════════════════
#  VISITS
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
#  VISITS
# ═══════════════════════════════════════════════════════════════
class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    # -----------------------------
    # Visit Information
    # -----------------------------
    visit_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    chief_complaint = db.Column(db.Text)

    # -----------------------------
    # Visit Status
    # CREATED
    # IN_PROGRESS
    # READY_FOR_BILLING
    # COMPLETED
    # REOPENED
    # CANCELLED
    # -----------------------------
    status = db.Column(
        db.String(30),
        default="CREATED",
        nullable=False
    )

    # -----------------------------
    # Visit Ownership
    # -----------------------------
    created_by = db.Column(
        db.String(100),
        nullable=True
    )   # Reception or Doctor username

    assigned_doctor = db.Column(
        db.String(100),
        nullable=True
    )

    # -----------------------------
    # Clinical Details
    # -----------------------------
    diagnosis = db.Column(db.Text)

    treatment_plan = db.Column(db.Text)

    treatment_done = db.Column(db.Text)

    advice = db.Column(db.Text)

    followup_treatment = db.Column(db.Text)

    # -----------------------------
    # Billing Instructions
    # -----------------------------
    treatment_type = db.Column(
        db.String(150),
        nullable=True
    )

    estimated_charges = db.Column(
        db.Float,
        default=0.0
    )

    amount_collected_today = db.Column(
        db.Float,
        default=0.0
    )

    billing_note = db.Column(
        db.Text,
        nullable=True
    )

    reception_notes = db.Column(
        db.Text,
        nullable=True
    )

    # -----------------------------
    # Follow-up
    # -----------------------------
    next_appointment = db.Column(
        db.Date,
        nullable=True
    )

    # -----------------------------
    # Visit Closing
    # -----------------------------
    closed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    closed_by = db.Column(
        db.String(100),
        nullable=True
    )

    # -----------------------------
    # Visit Reopening
    # -----------------------------
    reopened_at = db.Column(
        db.DateTime,
        nullable=True
    )

    reopened_by = db.Column(
        db.String(100),
        nullable=True
    )

    reopen_reason = db.Column(
        db.Text,
        nullable=True
    )

    # -----------------------------
    # Billing Queue Visibility
    # Lets reception hide a visit from the active billing queue — whether
    # or not it was ever paid — while still being able to find it again
    # by searching name / mobile / case number. Column added via the
    # migration in payments.py (run_visit_migrations).
    # -----------------------------
    billing_closed = db.Column(
        db.Boolean,
        default=False,
        nullable=True
    )

    billing_closed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    cbct_files = db.relationship(
        "CBCTFile",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    cbct_volumes = db.relationship(
        "CBCTVolume",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    dental_charts = db.relationship(
        "DentalChart",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    other_findings = db.relationship(
        "OtherFinding",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    consultations = db.relationship(
        "Consultation",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    prescriptions = db.relationship(
        "Prescription",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    images = db.relationship(
        "Image",
        backref="visit",
        lazy=True,
        cascade="all, delete-orphan"
    )

    payments = db.relationship(
        "Payment",
        backref="visit",
        lazy=True
    )
    
    audit_logs = db.relationship(
    "VisitAudit",
    backref="visit",
    lazy=True,
    cascade="all, delete-orphan"
)

# ═══════════════════════════════════════════════════════════════
# V# ═══════════════════════════════════════════════════════════════
# VISIT AUDIT
# ═══════════════════════════════════════════════════════════════
class VisitAudit(db.Model):
    __tablename__ = "visit_audit"

    id = db.Column(db.Integer, primary_key=True)

    visit_id = db.Column(
        db.Integer,
        db.ForeignKey("visits.id"),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    old_status = db.Column(
        db.String(30)
    )

    new_status = db.Column(
        db.String(30)
    )

    performed_by = db.Column(
        db.String(100)
    )

    reason = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Do NOT define another relationship here.
    # The relationship is already defined in the Visit model
    # using:
    #
    # audit_logs = db.relationship(
    #     "VisitAudit",
    #     backref="visit",
    #     lazy=True,
    #     cascade="all, delete-orphan"
    # )
# ═══════════════════════════════════════════════════════════════
#  DENTAL CHART
# ═══════════════════════════════════════════════════════════════
class DentalChart(db.Model):
    __tablename__ = "dental_chart"

    id           = db.Column(db.Integer,     primary_key=True)
    visit_id     = db.Column(db.Integer,     db.ForeignKey("visits.id"), nullable=False)
    tooth_number = db.Column(db.String(10),  nullable=False)
    condition    = db.Column(db.String(100), nullable=False)
    severity     = db.Column(db.String(20))
    other_text   = db.Column(db.String(200))
    custom_color = db.Column(db.String(20))
    surface      = db.Column(db.String(50))
    notes        = db.Column(db.Text)
    doctor       = db.Column(db.String(100))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "visit_id":     self.visit_id,
            "tooth_number": self.tooth_number,
            "condition":    self.condition,
            "severity":     self.severity,
            "other_text":   self.other_text,
            "custom_color": self.custom_color,
            "surface":      self.surface,
            "notes":        self.notes,
            "doctor":       self.doctor,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "updated_at":   self.updated_at.isoformat() if self.updated_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  OTHER FINDINGS
# ═══════════════════════════════════════════════════════════════
class OtherFinding(db.Model):
    __tablename__ = "other_findings"

    id           = db.Column(db.Integer, primary_key=True)
    visit_id     = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)
    finding_type = db.Column(db.String(100), nullable=False)
    value        = db.Column(db.Text)
    notes        = db.Column(db.Text)
    doctor       = db.Column(db.String(100))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  CONSULTATION
# ═══════════════════════════════════════════════════════════════
class Consultation(db.Model):
    __tablename__ = "consultations"

    id                   = db.Column(db.Integer, primary_key=True)
    visit_id             = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)
    diagnosis            = db.Column(db.Text)
    advice               = db.Column(db.Text)
    treatment_plan       = db.Column(db.Text)
    treatment_done_today = db.Column(db.Text)
    follow_up_date       = db.Column(db.Date, nullable=True)
    follow_up_time       = db.Column(db.Text, nullable=True)
    doctor               = db.Column(db.String(100))
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  PRESCRIPTION
# ═══════════════════════════════════════════════════════════════
class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id                   = db.Column(db.Integer, primary_key=True)
    visit_id             = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)

    # ── Patient snapshot ──
    patient_name         = db.Column(db.String(150))
    patient_age          = db.Column(db.String(20))
    patient_gender       = db.Column(db.String(10))
    case_number          = db.Column(db.String(50))
    date                 = db.Column(db.String(20))

    # ── Clinical content ──
    diagnosis            = db.Column(db.Text)
    advice               = db.Column(db.Text)
    treatment_done_today = db.Column(db.Text)

    # ── Medicines stored as JSON string ──
    medicines            = db.Column(db.Text, default="[]")

    # ── Follow-up ──
    follow_up_date       = db.Column(db.String(30))
    follow_up_time       = db.Column(db.String(20))

    # ── Status ──
    status               = db.Column(db.String(20), default="confirmed")

    # ── Legacy columns kept for backward compat ──
    drug_name            = db.Column(db.String(150))
    dosage               = db.Column(db.String(50))
    frequency            = db.Column(db.String(50))
    duration             = db.Column(db.String(50))
    instructions         = db.Column(db.Text)
    doctor               = db.Column(db.String(100))

    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":                   self.id,
            "visit_id":             self.visit_id,
            "patient_name":         self.patient_name,
            "patient_age":          self.patient_age,
            "patient_gender":       self.patient_gender,
            "case_number":          self.case_number,
            "date":                 self.date,
            "diagnosis":            self.diagnosis,
            "advice":               self.advice,
            "treatment_done_today": self.treatment_done_today,
            # Alias to match the key name used everywhere on the frontend
            # (Reception edit modal, print template, visit-enrichment
            # fallback). Without this the saved value is invisible to the
            # UI even after the _safe_data() write-side fix.
            "treatment_done":       self.treatment_done_today,
            "medicines":            self.medicines or "[]",
            "follow_up_date":       self.follow_up_date,
            "follow_up_time":       self.follow_up_time,
            "status":               self.status,
            "doctor":               self.doctor,
            "created_at":           self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  IMAGE
# ═══════════════════════════════════════════════════════════════
class Image(db.Model):
    __tablename__ = "images"

    id          = db.Column(db.Integer, primary_key=True)
    visit_id    = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)
    # Widened 255 -> 500: disk-storage paths are now
    # "uploads/images/<visit_id>/<uuid32>_<original-filename>.<ext>",
    # which can exceed 255 chars with a long original filename.
    # Matches CBCTFile.file_path / Payment.receipt_path elsewhere in this file.
    image_path  = db.Column(db.String(500), nullable=False)
    image_type  = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_date  = db.Column(db.Date, nullable=True)
    # NOTE: these two were being set by images.py's upload_image() but were
    # never declared here — since SQLAlchemy only persists mapped columns,
    # every uploaded image's actual bytes were silently discarded on save.
    image_data  = db.Column(db.Text, nullable=True)   # base64-encoded file content
    mime_type   = db.Column(db.String(50), nullable=True)


# ═══════════════════════════════════════════════════════════════
#  CBCT FILES  (raw uploaded DICOM/zip archives)
# ═══════════════════════════════════════════════════════════════
class CBCTFile(db.Model):
    __tablename__ = "cbct_files"

    id            = db.Column(db.Integer, primary_key=True)
    visit_id      = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)
    filename      = db.Column(db.String(255), nullable=False)   # stored filename (uuid-prefixed)
    original_name = db.Column(db.String(255), nullable=False)   # original filename from user
    file_path     = db.Column(db.String(500), nullable=False)   # absolute path on disk
    file_size     = db.Column(db.Integer,     nullable=True)    # bytes
    uploaded_by   = db.Column(db.String(100), nullable=True)
    uploaded_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":            self.id,
            "visit_id":      self.visit_id,
            "filename":      self.filename,
            "original_name": self.original_name,
            "file_path":     self.file_path,
            "file_size":     self.file_size,
            "uploaded_by":   self.uploaded_by,
            "uploaded_at":   self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  CBCT VOLUME  (parsed / processed DICOM volume)
# ═══════════════════════════════════════════════════════════════
class CBCTVolume(db.Model):
    __tablename__ = "cbct_volumes"

    id              = db.Column(db.Integer, primary_key=True)
    visit_id        = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False, index=True)

    # Patient / study metadata (from DICOM headers)
    patient_name    = db.Column(db.String(120))
    patient_id      = db.Column(db.String(64))
    study_date      = db.Column(db.String(20))
    modality        = db.Column(db.String(10),  default="CT")
    institution     = db.Column(db.String(120))

    # Volume dimensions
    num_slices      = db.Column(db.Integer,   default=0)   # axial depth
    coronal_slices  = db.Column(db.Integer,   default=0)
    sagittal_slices = db.Column(db.Integer,   default=0)
    rows            = db.Column(db.Integer,   default=512)
    cols            = db.Column(db.Integer,   default=512)

    # Voxel spacing (mm)
    slice_thickness = db.Column(db.Float,     default=0.3)
    pixel_spacing_x = db.Column(db.Float,     default=0.3)
    pixel_spacing_y = db.Column(db.Float,     default=0.3)

    # Storage: all slice images as base64 JPEG, packed in JSON
    # Format: { "axial": [...], "coronal": [...], "sagittal": [...] }
    # For large volumes consider moving this to object storage (S3/GCS)
    slice_data      = db.Column(db.Text)

    # Housekeeping
    uploaded_by     = db.Column(db.String(80))
    notes           = db.Column(db.Text)
    uploaded_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    annotations     = db.relationship(
        "CBCTAnnotation", backref="volume", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CBCTVolume id={self.id} visit={self.visit_id} slices={self.num_slices}>"


# ═══════════════════════════════════════════════════════════════
#  CBCT ANNOTATION
# ═══════════════════════════════════════════════════════════════
class CBCTAnnotation(db.Model):
    __tablename__ = "cbct_annotations"

    id         = db.Column(db.Integer, primary_key=True)
    cbct_id    = db.Column(db.Integer, db.ForeignKey("cbct_volumes.id"), nullable=False, index=True)
    ann_type   = db.Column(db.String(30))   # distance | angle | hu | implant | ian
    ann_view   = db.Column(db.String(20))   # axial | coronal | sagittal
    data       = db.Column(db.Text)         # Full annotation JSON blob
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CBCTAnnotation id={self.id} type={self.ann_type} view={self.ann_view}>"



# ═══════════════════════════════════════════════════════════════
#  FINAL BILLING LEDGER
#  Charges are separate from payments. PaymentAllocation explains
#  exactly which charge a payment settled.
# ═══════════════════════════════════════════════════════════════
class PatientAccount(db.Model):
    __tablename__ = "patient_accounts"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    credit_balance = db.Column(Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = db.relationship("Patient", backref=db.backref("billing_account", uselist=False))
    charges = db.relationship("BillingCharge", back_populates="account", lazy=True)


class BillingCharge(db.Model):
    __tablename__ = "billing_charges"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("patient_accounts.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=True, index=True)
    description = db.Column(db.Text, nullable=False)
    treatment_code = db.Column(db.String(80), nullable=True)
    gross_amount = db.Column(Numeric(12, 2), nullable=False, default=0)
    discount = db.Column(Numeric(12, 2), nullable=False, default=0)
    net_amount = db.Column(Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    charge_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    account = db.relationship("PatientAccount", back_populates="charges")
    patient = db.relationship("Patient", backref=db.backref("billing_charges", lazy=True))
    visit = db.relationship("Visit", backref=db.backref("billing_charges", lazy=True))
    allocations = db.relationship(
        "PaymentAllocation",
        back_populates="charge",
        lazy=True,
        cascade="all, delete-orphan",
    )


class PaymentAllocation(db.Model):
    __tablename__ = "payment_allocations"

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=False, index=True)
    charge_id = db.Column(db.Integer, db.ForeignKey("billing_charges.id"), nullable=True, index=True)
    allocation_type = db.Column(db.String(20), nullable=False, default="CHARGE")  # CHARGE / CREDIT
    amount = db.Column(Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    payment = db.relationship("Payment", back_populates="ledger_allocations")
    charge = db.relationship("BillingCharge", back_populates="allocations")

# ═══════════════════════════════════════════════════════════════
#  PAYMENT
# ═══════════════════════════════════════════════════════════════
class Payment(db.Model):
    __tablename__ = "payments"

    id                     = db.Column(db.Integer, primary_key=True)
    visit_id               = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=True)
    account_id             = db.Column(db.Integer, db.ForeignKey("patient_accounts.id"), nullable=True, index=True)
    ledger_status          = db.Column(db.String(20), nullable=False, default="ACTIVE")
    patient_name           = db.Column(db.String(150), nullable=False)
    case_number            = db.Column(db.String(50),  nullable=False)
    mobile                 = db.Column(db.String(20))
    treatment_description  = db.Column(db.Text)
    fee                    = db.Column(db.Float, default=0.0)
    discount               = db.Column(db.Float, default=0.0)
    paid_amount            = db.Column(db.Float, nullable=False)
    balance                = db.Column(db.Float, default=0.0)
    payment_method         = db.Column(db.String(50))
    receipt_number         = db.Column(db.Integer, nullable=True)
    receipt_path           = db.Column(db.String(500), nullable=True)
    payment_date           = db.Column(db.Date, nullable=True)
    created_at             = db.Column(db.DateTime, default=datetime.utcnow)

    receipts               = db.relationship("Receipt", backref="payment", lazy=True)
    ledger_allocations     = db.relationship("PaymentAllocation", back_populates="payment", lazy=True, cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════
#  RECEIPT
# ═══════════════════════════════════════════════════════════════
class Receipt(db.Model):
    __tablename__ = "receipts"

    id             = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.Integer, unique=True, nullable=False)
    payment_id     = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=False)
    status         = db.Column(db.String(20), default="ACTIVE")   # ACTIVE / CANCELLED
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  MEDICAL HISTORY — DATABASE UPGRADE
#
#  This file declares new columns on allergy_records / medications and
#  four new tables. They must exist in the database before ANY query
#  touches those models (visits.py, doctor.py, patients.py … all read
#  them), so the upgrade is tied to this file rather than to one route
#  file: the first time a database session is opened after start-up,
#  the missing columns and tables are added. That makes it impossible
#  to run the new models against an un-upgraded database.
#
#  The upgrade only ADDS things (ALTER TABLE … ADD COLUMN, CREATE TABLE).
#  It never drops, renames or rewrites anything, and it is safe to run
#  any number of times.
# ═══════════════════════════════════════════════════════════════
import threading
import traceback

from sqlalchemy import event, inspect as sa_inspect, text
from sqlalchemy.orm import Session as _OrmSession

_MH_NEW_TABLES = [MedicalConditionRecord, HabitRecord, WomenHealthRecord, MedicalHistoryAudit]
_MH_NEW_COLUMNS = {
    AllergyRecord: ["status", "created_by", "created_by_role", "updated_by", "updated_by_role", "version"],
    Medication: ["route", "start_date", "end_date",
                 "created_by", "created_by_role", "updated_by", "updated_by_role", "version"],
}

_mh_schema_ready = False
_mh_schema_lock = threading.Lock()


def ensure_medical_history_schema(engine=None):
    """Create the new tables and add the new columns if they are missing.
    Returns the list of things it added (empty when already up to date)."""
    global _mh_schema_ready
    if _mh_schema_ready:
        return []

    with _mh_schema_lock:
        if _mh_schema_ready:
            return []

        engine = engine or db.engine
        added = []

        def run(ddl):
            with engine.begin() as conn:
                if engine.dialect.name == "postgresql":
                    # Never hang a request behind another connection's lock.
                    conn.execute(text("SET LOCAL lock_timeout = '10s'"))
                conn.execute(text(ddl))

        for model in _MH_NEW_TABLES:
            table = model.__table__
            if not sa_inspect(engine).has_table(table.name):
                table.create(bind=engine, checkfirst=True)
                added.append(f"table {table.name}")

        for model, names in _MH_NEW_COLUMNS.items():
            table = model.__table__
            inspector = sa_inspect(engine)
            if not inspector.has_table(table.name):
                table.create(bind=engine, checkfirst=True)
                added.append(f"table {table.name}")
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for name in names:
                if name in existing:
                    continue
                column_type = table.columns[name].type.compile(dialect=engine.dialect)
                try:
                    run(f"ALTER TABLE {table.name} ADD COLUMN {name} {column_type}")
                    added.append(f"column {table.name}.{name}")
                except Exception:
                    # Another worker may have added it a moment ago.
                    now = {c["name"] for c in sa_inspect(engine).get_columns(table.name)}
                    if name not in now:
                        raise

        for item in added:
            print(f"[medical-history] database upgrade: added {item}")
        if added:
            print("[medical-history] database upgrade completed")
        _mh_schema_ready = True
        return added


@event.listens_for(_OrmSession, "after_begin")
def _mh_schema_guard(session, transaction, connection):
    """Runs the upgrade once, before the first query of the first session."""
    if _mh_schema_ready:
        return
    try:
        ensure_medical_history_schema(connection.engine)
    except Exception:
        # Report loudly, keep the application running, try again next time.
        print("[medical-history] DATABASE UPGRADE FAILED - medical history will not work until this is fixed:")
        traceback.print_exc()