from datetime import datetime
from database import db

from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

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
    age            = db.Column(db.Integer, nullable=True)
    date_of_birth  = db.Column(db.Date, nullable=True)
    gender         = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))
    mobile         = db.Column(db.String(20))
    email          = db.Column(db.String(150))
    blood_group    = db.Column(db.String(10))
    address        = db.Column(db.Text)
    profession     = db.Column(db.String(100))
    referred_by    = db.Column(db.String(150))
    chief_complaint= db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    visits         = db.relationship("Visit",         backref="patient", lazy=True)
    medical        = db.relationship("MedicalHistory",backref="patient", uselist=False)
    allergies      = db.relationship("AllergyRecord", backref="patient", lazy=True)
    habits         = db.relationship("Habit",         backref="patient", lazy=True)
    women_history  = db.relationship("WomanHistory",  backref="patient", uselist=False)
    family_doctor  = db.relationship("FamilyDoctor",  backref="patient", uselist=False)
    consent        = db.relationship("Consent",       backref="patient", uselist=False)


# ═══════════════════════════════════════════════════════════════
#  FAMILY DOCTOR
# ═══════════════════════════════════════════════════════════════
class FamilyDoctor(db.Model):
    __tablename__ = "family_doctors"

    id             = db.Column(db.Integer, primary_key=True)
    patient_id     = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False)
    doctor_name    = db.Column(db.String(150))
    doctor_phone   = db.Column(db.String(50))
    doctor_address = db.Column(db.Text)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  CONSENT
# ═══════════════════════════════════════════════════════════════
class Consent(db.Model):
    __tablename__ = "consents"

    id             = db.Column(db.Integer, primary_key=True)
    patient_id     = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False)
    agreed         = db.Column(db.Boolean, default=False)
    signature      = db.Column(db.String(200))
    relationship   = db.Column(db.String(100))
    consent_date   = db.Column(db.Date, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, onupdate=datetime.utcnow)


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
        }


# ═══════════════════════════════════════════════════════════════
#  ALLERGY RECORDS
# ═══════════════════════════════════════════════════════════════
class AllergyRecord(db.Model):
    __tablename__ = "allergy_records"

    id           = db.Column(db.Integer, primary_key=True)
    patient_id   = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    type         = db.Column(db.String(50))
    allergen     = db.Column(db.String(200))
    reaction     = db.Column(db.String(100))
    severity     = db.Column(db.String(50))
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":        self.id,
            "type":      self.type,
            "allergen":  self.allergen,
            "reaction":  self.reaction,
            "severity":  self.severity,
            "notes":     self.notes,
        }


# Backwards-compatible alias
Allergy = AllergyRecord


# ═══════════════════════════════════════════════════════════════
#  HABITS
# ═══════════════════════════════════════════════════════════════
class Habit(db.Model):
    __tablename__ = "habits"

    id             = db.Column(db.Integer, primary_key=True)
    patient_id     = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    habit_type     = db.Column(db.String(50))
    has_habit      = db.Column(db.Boolean, default=False)
    frequency      = db.Column(db.String(50))
    duration_years = db.Column(db.Integer)
    remarks        = db.Column(db.Text)
    consent        = db.Column(db.Boolean, default=False)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  WOMAN HISTORY
# ═══════════════════════════════════════════════════════════════
class WomanHistory(db.Model):
    __tablename__ = "woman_history"

    id            = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False)
    pregnant      = db.Column(db.Boolean, default=False)
    due_date      = db.Column(db.Date, nullable=True)
    nursing_child = db.Column(db.Boolean, default=False)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "pregnant":      self.pregnant,
            "due_date":      self.due_date.isoformat() if self.due_date else None,
            "nursing_child": self.nursing_child,
        }


# ═══════════════════════════════════════════════════════════════
#  VISITS
# ═══════════════════════════════════════════════════════════════
class Visit(db.Model):
    __tablename__ = "visits"

    id                 = db.Column(db.Integer, primary_key=True)
    patient_id         = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    visit_date         = db.Column(db.DateTime, default=datetime.utcnow)
    chief_complaint    = db.Column(db.Text)
    followup_treatment = db.Column(db.Text)
    status             = db.Column(db.String(10), default="OPEN")   # OPEN / CLOSED
    closed_at          = db.Column(db.DateTime, nullable=True)

    # ── Billing / clinical snapshot written at visit-close time ──
    # billing_note: doctor's free-text instructions for reception (optional)
    # treatment_done, advice, treatment_plan, diagnosis: denormalised from
    # the latest Consultation row so billing page can display them without
    # an extra join, and so they survive if the consultation is later edited.
    billing_note   = db.Column(db.Text, nullable=True)
    treatment_done = db.Column(db.Text, nullable=True)
    advice         = db.Column(db.Text, nullable=True)
    treatment_plan = db.Column(db.Text, nullable=True)
    diagnosis      = db.Column(db.Text, nullable=True)

    # Relationships
    dental_charts   = db.relationship("DentalChart",   backref="visit", lazy=True, cascade="all, delete-orphan")
    other_findings  = db.relationship("OtherFinding",  backref="visit", lazy=True, cascade="all, delete-orphan")
    consultations   = db.relationship("Consultation",  backref="visit", lazy=True, cascade="all, delete-orphan")
    prescriptions   = db.relationship("Prescription",  backref="visit", lazy=True, cascade="all, delete-orphan")
    images          = db.relationship("Image",         backref="visit", lazy=True, cascade="all, delete-orphan")
    payments        = db.relationship("Payment",       backref="visit", lazy=True)


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
    doctor               = db.Column(db.String(100))
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
#  PRESCRIPTION  ← UPDATED to match frontend payload
#
#  Old columns (drug_name, dosage, frequency, duration,
#  instructions) are KEPT for backward compatibility but the
#  new columns are what the Prescription.jsx frontend sends.
# ═══════════════════════════════════════════════════════════════
class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id                   = db.Column(db.Integer, primary_key=True)
    visit_id             = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=False)

    # ── Patient snapshot (denormalised for easy receipt printing) ──
    patient_name         = db.Column(db.String(150))
    patient_age          = db.Column(db.String(20))   # stored as string e.g. "40 yrs"
    patient_gender       = db.Column(db.String(10))   # Male / Female / Other
    case_number          = db.Column(db.String(50))
    date                 = db.Column(db.String(20))   # ISO date string "2026-03-09"

    # ── Clinical content ──
    diagnosis            = db.Column(db.Text)
    advice               = db.Column(db.Text)
    treatment_done_today = db.Column(db.Text)

    # ── Medicines — stored as JSON string ──
    # e.g. '[{"name":"Amoxicillin 500mg","dose":"1","freq":"TID","days":"5","instructions":"After food"}]'
    medicines            = db.Column(db.Text, default="[]")

    # ── Follow-up ──
    follow_up_date       = db.Column(db.String(30))   # "2026-03-16" or null

    # ── Status ──
    status               = db.Column(db.String(20), default="confirmed")  # confirmed / draft

    # ── Legacy columns kept for backward compat (nullable) ──
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
            "medicines":            self.medicines or "[]",
            "follow_up_date":       self.follow_up_date,
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
    image_path  = db.Column(db.String(255), nullable=False)
    image_type  = db.Column(db.String(30), nullable=False)   # IOPA, OPG, CBCT, INTRAORAL
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_date  = db.Column(db.Date, nullable=True)


# ═══════════════════════════════════════════════════════════════
#  PAYMENT
# ═══════════════════════════════════════════════════════════════
class Payment(db.Model):
    __tablename__ = "payments"

    id                     = db.Column(db.Integer, primary_key=True)
    visit_id               = db.Column(db.Integer, db.ForeignKey("visits.id"), nullable=True)
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