r"""
billing_receipts.py — the clinic's billing, inside the web application.

This is the old stand-alone billing software (the .exe: Payment Dashboard,
Add Payment, Edit, View, Delete, PDF receipt, monthly Excel) rebuilt as
part of the clinic system, so no separate program is needed:

  * the same receipt: clinic heading, RECEIPT, date / receipt number,
    name / case id / mobile, treatments with amounts, total, amount in
    words, payment methods, notes, signature, footer line
  * the same Excel columns: date, receipt_no, name, case_no, mobile,
    treatment_summary, amount_paid, payment_methods
  * receipt numbers continue from the old software once its receipts
    are imported (POST /clinic-billing/import-old with its payments.db file)

RECEIPT FILES — FINANCIAL-YEAR FOLDERS (made by themselves)

  Every time a receipt is saved, edited or deleted, its PDF and the
  month's Excel sheet are kept up to date automatically:

      receipts/Financial year 2026-2027/Sep2026/pdf/Anitha_Rao.0004.pdf
      receipts/Financial year 2026-2027/Sep2026/excel/Sep2026.xlsx

  The month folders are exactly like the old billing software's
  (Sep2026\pdf, Sep2026\excel, Sep2026.xlsx), with the financial year on
  top. Financial year = April to March. The folders follow each receipt's own
  date (today's date for a new receipt). The Excel sheet of a month is
  rewritten from the saved receipts each time, so edits and deletes are
  always reflected; a deleted receipt's PDF is removed.

  WHERE THE FILES ARE KEPT
    * In object storage, together with the X-rays and photos, once object
      storage is switched on for the images (IMAGE_STORAGE=s3 and the S3_…
      settings — see images.py). BILLING_STORAGE=s3 / local can choose
      differently for the receipts.
    * Until then, on the server:  <backend folder>\receipts\…
      (BILLING_FILES_FOLDER=D:\Somewhere chooses another folder).
    BILLING_SAVE_FILES=0 switches the files off.
  Billing → "📊 Excel & files" shows where they are, lists them by
  financial year and month for downloading, and has "Save files again".
  If a file cannot be written (the Excel sheet is open in Excel, the
  internet is down …), the receipt is still saved and the screen says
  which file could not be updated.

PATIENT ACCOUNTS — TREATMENTS, DISCOUNTS, PART PAYMENTS, BALANCES

  Each patient has an account:
    * Treatments with their charge (fee) and discount — the amount to be
      paid for each (table billing_treatment_charges).
    * Payments (receipts). A payment says how much is paid now towards each
      chosen treatment — all of it, or part of it (table
      billing_receipt_allocations). A treatment can be paid over several
      visits; a payment can cover several treatments.
    * For every treatment: charge, discount, paid so far, balance, status
      (Not paid / Part paid / Paid). For the patient: total charges, paid,
      balance due.
  A treatment can be added, changed or deleted (deleting only while nothing
  has been paid towards it). A payment can be changed or deleted; the
  balances follow by themselves. The receipt shows, for each treatment, the
  charge, what was paid earlier and the balance left, and the patient's
  total balance after this payment. Simple receipts without a patient
  account (walk-in, and the old software's receipts) still work as before.

DELETING A RECEIPT — WITH A REASON, KEPT IN THE DELETION LOG

  A receipt made by mistake can be deleted, but only with a reason
  (e.g. "Created by mistake", "Duplicate receipt", "Wrong patient").
  Before it goes, a full copy of it — receipt number, date, patient,
  treatments, amount, payment methods, and how it was shared over the
  patient's treatments — is written to the deletion log (table
  billing_receipt_deletions) with the reason, who deleted it and when.
  The log cannot be changed or emptied from the app.
  Numbers: when the LATEST receipt is deleted (the usual "made by mistake"
  case), the next receipt gets its number again, so the numbers stay
  continuous. An older deleted number is not filled in later (that would put
  a new receipt among old ones). The log shows when a deleted receipt's
  number has since been given to a new receipt.

What is different from the old software, on purpose:

  * Receipts are kept in the clinic system's own database (table
    "billing_receipts"); the files above are copies made from it, so a
    lost or damaged file can always be made again ("Save files again").
  * Every receipt can be linked to the patient (patient_id) — the same
    patient record Reception and the Doctor use — so a patient's receipts
    can be listed with GET /clinic-billing/receipts?patient_id=<id>
    (ready for the patient's own access later).
  * A receipt can belong to a clinic visit. Saving the first receipt of
    a visit marks that visit as billed in Billing → "Doctor's
    Instructions"; deleting its last receipt puts it back to Pending.
  * Everything here needs a clinic login.
  * The rupee sign is printed as "Rs." — the old receipts showed a black
    square there, because the PDF's built-in font has no rupee sign.

HOW THIS FILE IS LOADED
  visits.py loads this file and adds its addresses to its own group
  (see the last lines of visits.py), so app.py does not need changing.
  Put this file in the routes folder, next to visits.py.

ADDRESSES (all under /api)
  (They start with /clinic-billing, not /billing, on purpose: the earlier,
   switched-off billing in payments.py still owns addresses beginning with
   /billing and /payments, and the two must never be mixed up.)
  GET    /clinic-billing/receipts            ?q=<search>  ?visit_id=<visit>  ?patient_id=<patient>
  GET    /clinic-billing/receipts/new        next receipt number, today's date, treatment list
  POST   /clinic-billing/receipts            create
  GET    /clinic-billing/receipts/<id>
  PUT    /clinic-billing/receipts/<id>       edit
  DELETE /clinic-billing/receipts/<id>
  GET    /clinic-billing/receipts/<id>/pdf   the receipt (add ?download=1 to save it)
  GET    /clinic-billing/excel               ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
  POST   /clinic-billing/import-old          file = the old software's payments.db
  GET    /clinic-billing/patients            ?q=<name, case number or mobile>   (patient picker)
  GET    /clinic-billing/patients/<id>/account   treatments, balances, payments, visits
  POST   /clinic-billing/patients/<id>/charges   add a treatment {treatment, description, visit_id, date, fee, discount | discount_percent}
  PUT    /clinic-billing/charges/<id>            change it
  DELETE /clinic-billing/charges/<id>            delete it (only while nothing is paid towards it)
  (DELETE /clinic-billing/receipts/<id> needs  {"reason": "..."}  — kept in the deletion log)
  GET    /clinic-billing/deleted             ?q=  the deletion log (newest first)
  (POST / PUT /clinic-billing/receipts also take  allocations: [{charge_id, amount}]  and
   new_charges: [{treatment, description, fee, discount, pay}]  — a payment towards chosen treatments)
  GET    /clinic-billing/files/status        where the receipt files are kept
  GET    /clinic-billing/files/months        financial years and months that have receipts
  GET    /clinic-billing/files               ?month=2026-09   files of one month
  GET    /clinic-billing/files/download      ?key=receipts/Financial year …/Sep2026/pdf/….pdf  (&inline=1 to show it)
  GET    /clinic-billing/files/sheet         ?key=…/Sep2026/excel/Sep2026.xlsx   the sheet's rows, to show in the app
  POST   /clinic-billing/files/regenerate    {date_from, date_to, include_pdfs}

LOGO AND SIGNATURE ON THE RECEIPT
  To use exactly the pictures of the old software, copy its
  static\logo.png and static\signature.png into
      <backend folder>\static\billing\
  If they are not there, the logo and signature already built into this
  clinic system (payments.py) are used.
"""

import base64
import io
import json
import math
import os
import sqlite3
import tempfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import jsonify, request, send_file
from sqlalchemy import func, or_, text
from sqlalchemy.exc import IntegrityError

from database import db
from models import Visit, Patient
from auth_utils import require_login


# ══════════════════════════════════════════════════════════════════
#  Fixed lists (same as the old software)
# ══════════════════════════════════════════════════════════════════
DEFAULT_TREATMENTS = [
    "Scaling",
    "Polishing",
    "Filling (Composite)",
    "Filling (GIC)",
    "Extraction",
    "Surgical Extraction",
    "Root Canal Treatment",
    "Re-RCT",
    "Crown (Metal)",
    "Crown (PFM)",
    "Crown (Zirconia)",
    "Bridge",
    "Implant",
    "Implant + Crown",
    "Complete Denture (Upper)",
    "Complete Denture (Lower)",
    "Partial Denture",
    "Orthodontic Treatment",
    "Tooth Whitening",
    "X-Ray",
    "Consultation",
    "Follow-up Visit",
]

PAYMENT_METHODS = ["UPI", "Cheque", "A/C", "Card", "Cash"]

CLINIC_NAME    = "Sri Satya Sai Oral Health Center & Dental Clinic"
CLINIC_ADDRESS = "Address: G-15, Rajnigandha Apartments, Chaitanyapuri, Hyderabad - 500060"
CLINIC_PHONE   = "Phone: 9908894449, 9949094449"
RECEIPT_FOOTER = "Visit once in 6 months or as advised by the doctor to maintain better oral health"

# (balance_due, added at the end, is the patient's total balance due right after
#  a payment made through the patient account; empty for other receipts)
EXCEL_COLUMNS = ["date", "receipt_no", "name", "case_no", "mobile",
                 "treatment_summary", "amount_paid", "payment_methods", "balance_due"]

MAX_AMOUNT = 100000000          # 10 crore — anything above is a typing mistake
MAX_IMPORT_BYTES = 300 * 1024 * 1024

_IST = timedelta(hours=5, minutes=30)

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_name(day):
    """Oct2026 — the old software's month folder / Excel name."""
    return f"{_MONTHS[day.month - 1]}{day.year}"


def _today_ist():
    return (datetime.utcnow() + _IST).date()


# ══════════════════════════════════════════════════════════════════
#  The receipts table
# ══════════════════════════════════════════════════════════════════
class BillingReceipt(db.Model):
    __tablename__ = "billing_receipts"

    id              = db.Column(db.Integer, primary_key=True)
    receipt_no      = db.Column(db.Integer, nullable=False, unique=True)
    receipt_date    = db.Column(db.Date, nullable=False)
    name            = db.Column(db.String(200), nullable=False)
    case_no         = db.Column(db.String(100))
    mobile          = db.Column(db.String(30))
    # [{"name": ..., "amount": ..., "description": ...}, ...]  (same shape as the old software)
    treatments_json = db.Column(db.Text)
    amount_paid     = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_methods = db.Column(db.String(200))        # "UPI,Cash"
    notes           = db.Column(db.Text)

    # The clinic visit this receipt was made for (empty for walk-in receipts
    # and for receipts brought over from the old software).
    visit_id        = db.Column(db.Integer, index=True)
    # The patient (patients.id) — set from the visit, chosen in the form, or
    # matched by case number when old receipts are brought over.
    patient_id      = db.Column(db.Integer, index=True)
    # False = its PDF could not be saved yet (storage was not reachable); it is
    # saved by itself with a later receipt. Empty for receipts brought over.
    files_saved     = db.Column(db.Boolean)
    # "old-software" for receipts brought over from payments.db
    source          = db.Column(db.String(20))
    # The patient's total balance due right after this payment (receipts paid
    # through the patient account); printed on the receipt.
    balance_after   = db.Column(db.Numeric(12, 2))

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    created_by      = db.Column(db.String(100))
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by      = db.Column(db.String(100))

    def treatments(self):
        if not self.treatments_json:
            return []
        try:
            rows = json.loads(self.treatments_json)
        except Exception:
            return []
        return [t for t in rows if isinstance(t, dict)] if isinstance(rows, list) else []


class TreatmentCharge(db.Model):
    """One treatment in a patient's account: what it costs (fee) and any discount."""
    __tablename__ = "billing_treatment_charges"

    id           = db.Column(db.Integer, primary_key=True)
    patient_id   = db.Column(db.Integer, nullable=False, index=True)
    visit_id     = db.Column(db.Integer, index=True)            # the visit it was done in (optional)
    treatment    = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.String(500))                     # tooth number, notes
    charge_date  = db.Column(db.Date, nullable=False)
    fee          = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount     = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    created_by   = db.Column(db.String(100))
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by   = db.Column(db.String(100))


class ReceiptAllocation(db.Model):
    """How much of one payment (receipt) went to one treatment."""
    __tablename__ = "billing_receipt_allocations"

    id          = db.Column(db.Integer, primary_key=True)
    receipt_id  = db.Column(db.Integer, db.ForeignKey("billing_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    charge_id   = db.Column(db.Integer, db.ForeignKey("billing_treatment_charges.id"), nullable=False, index=True)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)


class ReceiptDeletion(db.Model):
    """Deletion log: a full copy of every deleted receipt, with why, who and when."""
    __tablename__ = "billing_receipt_deletions"

    id            = db.Column(db.Integer, primary_key=True)
    receipt_id    = db.Column(db.Integer)
    receipt_no    = db.Column(db.Integer, nullable=False, index=True)
    receipt_date  = db.Column(db.Date)
    name          = db.Column(db.String(200))
    case_no       = db.Column(db.String(100))
    mobile        = db.Column(db.String(30))
    patient_id    = db.Column(db.Integer, index=True)
    visit_id      = db.Column(db.Integer)
    amount_paid   = db.Column(db.Numeric(12, 2))
    receipt_json  = db.Column(db.Text)                      # everything the receipt held
    reason        = db.Column(db.String(500), nullable=False)
    deleted_by    = db.Column(db.String(100))
    deleted_at    = db.Column(db.DateTime, default=datetime.utcnow, index=True)


_table_ready = False


def _ensure_table():
    """Creates the billing_receipts table the first time it is needed.
    Never touches any other table."""
    global _table_ready
    if _table_ready:
        return
    BillingReceipt.__table__.create(bind=db.engine, checkfirst=True)
    TreatmentCharge.__table__.create(bind=db.engine, checkfirst=True)
    ReceiptAllocation.__table__.create(bind=db.engine, checkfirst=True)
    ReceiptDeletion.__table__.create(bind=db.engine, checkfirst=True)
    # Tables made by the first version of this file have no patient column yet.
    from sqlalchemy import inspect as _inspect
    columns = {c["name"] for c in _inspect(db.engine).get_columns("billing_receipts")}
    with db.engine.begin() as conn:
        if "patient_id" not in columns:
            conn.execute(text("ALTER TABLE billing_receipts ADD COLUMN patient_id INTEGER"))
        if "files_saved" not in columns:
            conn.execute(text("ALTER TABLE billing_receipts ADD COLUMN files_saved BOOLEAN"))
        if "balance_after" not in columns:
            conn.execute(text("ALTER TABLE billing_receipts ADD COLUMN balance_after NUMERIC(12, 2)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_billing_receipts_patient_id ON billing_receipts (patient_id)"))
        # receipts made for a visit belong to that visit's patient
        conn.execute(text(
            "UPDATE billing_receipts SET patient_id = "
            "(SELECT visits.patient_id FROM visits WHERE visits.id = billing_receipts.visit_id) "
            "WHERE patient_id IS NULL AND visit_id IS NOT NULL"))
    _table_ready = True


# ══════════════════════════════════════════════════════════════════
#  Small helpers
# ══════════════════════════════════════════════════════════════════
class _Refuse(Exception):
    """Something in the request is not acceptable; the message is shown to the user."""
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _guard(fn):
    """Makes sure the table exists, and turns any failure into a plain
    message with nothing half-saved."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            _ensure_table()
            return fn(*args, **kwargs)
        except _Refuse as err:
            db.session.rollback()
            return jsonify({"error": err.message}), err.status
        except Exception as exc:
            db.session.rollback()
            print(f"[billing] {fn.__name__} failed: {exc!r}")
            return jsonify({"error": "The server could not do this. Nothing was changed — please try again."}), 500
    return wrapper


def _who():
    """Name of the signed-in person, when the login system can tell us."""
    try:
        try:
            from medical_history import current_actor
        except ImportError:
            from routes.medical_history import current_actor
        name = (current_actor() or {}).get("name")
        return str(name).strip()[:100] if name else None
    except Exception:
        return None


def _text(value, limit):
    return str(value if value is not None else "").strip()[:limit]


def _number(value, what):
    """A money amount: a real number, not negative, not absurd."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return 0.0
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise _Refuse(f"{what} is not a number.")
    if math.isnan(number) or math.isinf(number):
        raise _Refuse(f"{what} is not a number.")
    if number < 0:
        raise _Refuse(f"{what} cannot be less than zero.")
    if number > MAX_AMOUNT:
        raise _Refuse(f"{what} is too large. Please check it.")
    return round(number, 2)


def _parse_date(value, required_message="Please enter the date as YYYY-MM-DD."):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        raise _Refuse(required_message)


def _clean_treatments(raw):
    """Rows without a treatment name are dropped, exactly like the old software."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "[]")
        except Exception:
            raise _Refuse("The treatments could not be read. Please enter them again.")
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise _Refuse("The treatments could not be read. Please enter them again.")
    if len(raw) > 100:
        raise _Refuse("Too many treatment lines on one receipt.")
    cleaned = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"), 200)
        if not name:
            continue
        cleaned.append({
            "name": name,
            "amount": _number(row.get("amount"), f"The amount for “{name}”"),
            "description": _text(row.get("description"), 500),
        })
    return cleaned


def _clean_methods(raw):
    if isinstance(raw, str):
        raw = raw.split(",")
    if not isinstance(raw, (list, tuple)):
        return []
    chosen = {str(m).strip() for m in raw}
    return [m for m in PAYMENT_METHODS if m in chosen]       # fixed order, known names only


def _read_receipt_form(data):
    if not isinstance(data, dict):
        raise _Refuse("The receipt could not be read. Please try again.")
    name = _text(data.get("name"), 200)
    if not name and data.get("patient_id") not in (None, "", 0, "0"):
        patient = db.session.get(Patient, int(data["patient_id"])) if str(data["patient_id"]).isdigit() else None
        name = _text(patient.name, 200) if patient else ""
    if not name:
        raise _Refuse("Please enter the patient's name.")

    treatments = _clean_treatments(data.get("treatments"))
    total = round(sum(t["amount"] for t in treatments), 2)
    given = data.get("amount_paid")
    if given is None or (isinstance(given, str) and not given.strip()):
        amount = total
    else:
        amount = _number(given, "The total amount")

    return {
        "receipt_date": _parse_date(data.get("date")) or _today_ist(),
        "name": name,
        "case_no": _text(data.get("case_no"), 100),
        "mobile": _text(data.get("mobile"), 30),
        "treatments": treatments,
        "amount_paid": amount,
        "payment_methods": _clean_methods(data.get("payment_methods")),
        "notes": _text(data.get("notes"), 5000),
    }


def _apply(receipt, form):
    receipt.receipt_date    = form["receipt_date"]
    receipt.name            = form["name"]
    receipt.case_no         = form["case_no"]
    receipt.mobile          = form["mobile"]
    receipt.treatments_json = json.dumps(form["treatments"], ensure_ascii=False)
    receipt.amount_paid     = Decimal(str(form["amount_paid"]))
    receipt.payment_methods = ",".join(form["payment_methods"])
    receipt.notes           = form["notes"]


def _amount(receipt):
    return float(receipt.amount_paid or 0)


def _patient_card(patient):
    if patient is None:
        return None
    return {"patient_id": patient.id, "name": patient.name or "", "case_number": patient.case_number or "",
            "mobile": patient.mobile or ""}


def _serialize(r, patients=None):
    methods = [m for m in (r.payment_methods or "").split(",") if m]
    if r.patient_id:
        patient = patients.get(r.patient_id) if patients is not None else db.session.get(Patient, r.patient_id)
    else:
        patient = None
    return {
        "id":              r.id,
        "receipt_no":      r.receipt_no,
        "date":            r.receipt_date.isoformat() if r.receipt_date else None,
        "name":            r.name or "",
        "case_no":         r.case_no or "",
        "mobile":          r.mobile or "",
        "treatments":      [_line_out(t) for t in r.treatments()],
        "has_allocations": any(t.get("charge_id") for t in r.treatments()),
        "balance_after":   None if r.balance_after is None else float(r.balance_after),
        "amount_paid":     _amount(r),
        "payment_methods": methods,
        "notes":           r.notes or "",
        "visit_id":        r.visit_id,
        "patient_id":      r.patient_id,
        "patient":         _patient_card(patient),
        "from_old_software": r.source == "old-software",
        "created_by":      r.created_by or "",
        "pdf_name":        _pdf_name(r),
    }


def _line_out(t):
    line = {"name": str(t.get("name") or ""), "amount": _safe_float(t.get("amount")),
            "description": str(t.get("description") or "")}
    if t.get("charge_id"):
        line.update({k: (_safe_float(t.get(k)) if k != "charge_id" else int(t["charge_id"]))
                     for k in ("charge_id", "charge_fee", "charge_discount", "charge_net", "paid_before", "balance_after")})
    return line


def _safe_float(value):
    try:
        number = float(value or 0)
        return 0.0 if math.isnan(number) or math.isinf(number) else number
    except (TypeError, ValueError):
        return 0.0


def _next_receipt_no():
    # One more than the highest receipt there is. So if the latest receipt was
    # deleted, its number is given again; older deleted numbers are not refilled.
    return int(db.session.query(func.max(BillingReceipt.receipt_no)).scalar() or 0) + 1


def _deletion_out(d, reused=None):
    try:
        copy = json.loads(d.receipt_json or "{}")
    except Exception:
        copy = {}
    when = (d.deleted_at + _IST) if d.deleted_at else None
    return {
        "id": d.id,
        "receipt_id": d.receipt_id,
        "receipt_no": d.receipt_no,
        "date": d.receipt_date.isoformat() if d.receipt_date else None,
        "name": d.name or "",
        "case_no": d.case_no or "",
        "mobile": d.mobile or "",
        "patient_id": d.patient_id,
        "visit_id": d.visit_id,
        "amount_paid": float(d.amount_paid or 0),
        "reason": d.reason,
        "deleted_by": d.deleted_by or "",
        "deleted_at": when.isoformat(timespec="seconds") if when else None,
        "deleted_display": when.strftime("%d-%m-%Y %I:%M %p") if when else "",
        "receipt": copy,
        # the receipt that now carries this number, if it was given again
        "number_now_used_by": reused,
    }


def _one_at_a_time():
    """While a receipt is being saved, anyone else saving a receipt waits a
    moment for their turn, so two receipts can never be given the same
    number. (PostgreSQL holds the turn until this save is finished; on other
    databases the unique receipt number plus the retry below does the job.)"""
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT pg_advisory_xact_lock(74209113)"))


def _visit_is_closed(visit):
    return (visit.status or "").strip().lower() in ("closed", "completed")


def _set_visit_billed(visit_id, billed):
    """The same switch Reception's "Mark as Billed" button uses."""
    if not visit_id:
        return
    visit = db.session.get(Visit, visit_id)
    if not visit:
        return
    if billed:
        if _visit_is_closed(visit) and not visit.billing_closed:
            visit.billing_closed = True
            visit.billing_closed_at = datetime.utcnow()
    else:
        visit.billing_closed = False
        visit.billing_closed_at = None


# ══════════════════════════════════════════════════════════════════
#  Patient accounts: treatments, payments towards them, balances
# ══════════════════════════════════════════════════════════════════
def _money(value):
    return round(float(value or 0), 2)


def _net(charge):
    return round(_money(charge.fee) - _money(charge.discount), 2)


def _paid_by_charge(charge_ids):
    """{charge_id: amount paid so far} from all payments."""
    if not charge_ids:
        return {}
    rows = (db.session.query(ReceiptAllocation.charge_id, func.sum(ReceiptAllocation.amount))
            .filter(ReceiptAllocation.charge_id.in_(list(charge_ids)))
            .group_by(ReceiptAllocation.charge_id).all())
    return {cid: _money(total) for cid, total in rows}


def _status(net, paid):
    if net <= 0.004:
        return "No charge"
    if paid <= 0.004:
        return "Not paid"
    if paid + 0.004 >= net:
        return "Paid"
    return "Part paid"


def _patient_balance(patient_id):
    charges = TreatmentCharge.query.filter_by(patient_id=patient_id).all()
    paid = _paid_by_charge([c.id for c in charges])
    return round(sum(max(_net(c) - paid.get(c.id, 0.0), 0.0) for c in charges), 2)


def _clean_charge(data, current=None):
    """A treatment from the form. Discount as an amount (discount) or as a
    percentage of the fee (discount_percent)."""
    if not isinstance(data, dict):
        raise _Refuse("The treatment could not be read. Please try again.")
    treatment = _text(data.get("treatment") if "treatment" in data else (current.treatment if current else ""), 200)
    if not treatment:
        raise _Refuse("Please choose or type the treatment.")
    fee = _number(data.get("fee") if "fee" in data else (current.fee if current else 0), f"The charge for “{treatment}”")
    if data.get("discount_percent") not in (None, ""):
        percent = _number(data.get("discount_percent"), "The discount %")
        if percent > 100:
            raise _Refuse("The discount cannot be more than 100%.")
        discount = round(fee * percent / 100.0, 2)
    else:
        discount = _number(data.get("discount") if "discount" in data else (current.discount if current else 0),
                           f"The discount for “{treatment}”")
    if discount > fee + 0.004:
        raise _Refuse(f"The discount for “{treatment}” (₹{discount:.2f}) is more than its charge (₹{fee:.2f}).")
    when = _parse_date(data.get("date")) if data.get("date") else (current.charge_date if current else None)
    return {
        "treatment": treatment,
        "description": _text(data.get("description") if "description" in data else (current.description if current else ""), 500),
        "fee": fee,
        "discount": discount,
        "charge_date": when or _today_ist(),
    }


def _charge_visit(patient_id, raw):
    """visit_id for a treatment: must be one of this patient's visits."""
    if raw in (None, "", 0, "0"):
        return None
    try:
        visit = db.session.get(Visit, int(raw))
    except (TypeError, ValueError):
        visit = None
    if visit is None or visit.patient_id != patient_id:
        raise _Refuse("That visit is not one of this patient's visits.")
    return visit.id


def _charge_out(c, paid, payments=None):
    net = _net(c)
    paid_here = paid.get(c.id, 0.0)
    return {
        "charge_id": c.id,
        "patient_id": c.patient_id,
        "visit_id": c.visit_id,
        "treatment": c.treatment,
        "description": c.description or "",
        "date": c.charge_date.isoformat() if c.charge_date else None,
        "fee": _money(c.fee),
        "discount": _money(c.discount),
        "net": net,
        "paid": paid_here,
        "balance": round(max(net - paid_here, 0.0), 2),
        "status": _status(net, paid_here),
        "payments": payments or [],
    }


def _allocate(receipt, patient_id, data, who):
    """The payment's lines from the treatments chosen in the patient account.

    data["allocations"] = [{charge_id, amount}]  — paying (part of) existing treatments
    data["new_charges"] = [{treatment, description, fee, discount | discount_percent, pay, visit_id}]
                           — treatments added and paid (fully or partly) in the same go
    Returns the receipt lines. The receipt's own earlier allocations are replaced."""
    if not patient_id:
        raise _Refuse("Please choose the patient first — payments towards treatments belong to a patient's account.")
    ReceiptAllocation.query.filter_by(receipt_id=receipt.id).delete()
    db.session.flush()

    wanted = []
    for item in data.get("allocations") or []:
        if not isinstance(item, dict):
            continue
        try:
            cid = int(item.get("charge_id"))
        except (TypeError, ValueError):
            raise _Refuse("A chosen treatment could not be read. Please choose it again.")
        wanted.append((cid, _number(item.get("amount"), "The amount paid now")))
    new_list = data.get("new_charges") or []
    if len(new_list) > 50 or len(wanted) > 200:
        raise _Refuse("Too many treatments in one payment.")
    for item in new_list:
        fields = _clean_charge(item)
        charge = TreatmentCharge(patient_id=patient_id, visit_id=_charge_visit(patient_id, item.get("visit_id")) if isinstance(item, dict) else None,
                                 created_by=who, updated_by=who, **fields)
        if charge.visit_id is None and receipt.visit_id:
            charge.visit_id = receipt.visit_id
        db.session.add(charge)
        db.session.flush()
        wanted.append((charge.id, _number(item.get("pay"), f"The amount paid now for “{fields['treatment']}”")))

    merged = {}
    for cid, amount in wanted:
        if amount > 0:
            merged[cid] = round(merged.get(cid, 0.0) + amount, 2)
    charges = {c.id: c for c in TreatmentCharge.query.filter(TreatmentCharge.id.in_(list(merged) or [0])).all()}
    paid = _paid_by_charge(list(merged))
    lines = []
    for cid, amount in merged.items():
        c = charges.get(cid)
        if c is None or c.patient_id != patient_id:
            raise _Refuse("A chosen treatment was not found in this patient's account. Please open the account again.")
        net = _net(c)
        before = paid.get(cid, 0.0)
        left = round(net - before, 2)
        if amount > left + 0.004:
            raise _Refuse(f"“{c.treatment}” has only ₹{max(left, 0):.2f} left to pay, but ₹{amount:.2f} was entered.")
        db.session.add(ReceiptAllocation(receipt_id=receipt.id, charge_id=cid, amount=Decimal(str(amount))))
        lines.append({"name": c.treatment, "amount": amount, "description": c.description or "",
                      "charge_id": cid, "charge_fee": _money(c.fee), "charge_discount": _money(c.discount),
                      "charge_net": net, "paid_before": before, "balance_after": round(left - amount, 2)})
    return lines


def _wants_allocation(data):
    return isinstance(data, dict) and ("allocations" in data or "new_charges" in data)


def _finish_account_receipt(receipt, lines, extra_lines):
    """Lines, total and the patient's balance after this payment."""
    every = lines + extra_lines
    if not every or round(sum(l["amount"] for l in every), 2) <= 0:
        raise _Refuse("Enter how much is being paid now for at least one treatment.")
    receipt.treatments_json = json.dumps(every, ensure_ascii=False)
    receipt.amount_paid = Decimal(str(round(sum(l["amount"] for l in every), 2)))
    db.session.flush()
    receipt.balance_after = Decimal(str(_patient_balance(receipt.patient_id)))


# ══════════════════════════════════════════════════════════════════
#  Amount in words (Indian system: thousand, lakh, crore)
#  Same wording the old receipts had: "Three Thousand Two Hundred and Fifty"
# ══════════════════════════════════════════════════════════════════
_ONES = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
         "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _below_hundred(n):
    if n < 20:
        return _ONES[n]
    return _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")


def amount_in_words(amount):
    n = int(round(float(amount or 0)))
    if n <= 0:
        return "Zero"
    parts = []
    crore, n = divmod(n, 10000000)
    lakh, n = divmod(n, 100000)
    thousand, n = divmod(n, 1000)
    hundred, rest = divmod(n, 100)
    if crore:
        parts.append(amount_in_words(crore) + " Crore")
    if lakh:
        parts.append(_below_hundred(lakh) + " Lakh")
    if thousand:
        parts.append(_below_hundred(thousand) + " Thousand")
    if hundred:
        parts.append(_ONES[hundred] + " Hundred")
    if rest:
        parts.append(("and " if parts else "") + _below_hundred(rest))
    return " ".join(parts)


# ══════════════════════════════════════════════════════════════════
#  Logo and signature for the receipt
# ══════════════════════════════════════════════════════════════════
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_picture_cache = {}


def _receipt_picture(kind):
    """kind = "logo" or "signature". The clinic's own file if it was copied
    into static/billing, otherwise the picture built into payments.py.
    Returns something ReportLab can draw, or None."""
    if kind in _picture_cache:
        return _picture_cache[kind]
    from reportlab.lib.utils import ImageReader

    picture = None
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (os.path.join(_BACKEND_ROOT, "static", "billing"),
                   os.path.join(_BACKEND_ROOT, "static"),
                   os.path.join(here, "static", "billing"),
                   os.path.join(here, "static")):
        path = os.path.join(folder, f"{kind}.png")
        if os.path.isfile(path):
            try:
                picture = ImageReader(path)
                picture.getSize()
                break
            except Exception:
                picture = None

    if picture is None:
        try:
            try:
                from routes import payments as _old_billing
            except ImportError:
                import payments as _old_billing
            encoded = getattr(_old_billing, "_LOGO_B64" if kind == "logo" else "_SIG_B64", None)
            if encoded:
                picture = ImageReader(io.BytesIO(base64.b64decode(encoded)))
                picture.getSize()
        except Exception:
            picture = None

    picture = _reasonable_size(picture)
    _picture_cache[kind] = picture
    return picture


def _reasonable_size(picture, longest=360):
    """The logo built into the clinic system is a very large picture (about
    900 x 900, half a megabyte), which would make every saved PDF about
    0.5 MB. Printed 22 mm wide it never needs more than ~360 pixels (over 400 dots per inch), so a
    smaller copy is used: same look on paper, PDFs about 10 times smaller."""
    if picture is None:
        return None
    try:
        from PIL import Image
        from reportlab.lib.utils import ImageReader
        width, height = picture.getSize()
        if max(width, height) <= longest:
            return picture
        image = picture._image if getattr(picture, "_image", None) is not None else None
        if image is None:
            return picture
        image = image.copy()
        image.thumbnail((longest, longest), Image.LANCZOS)
        smaller = ImageReader(image)
        smaller.getSize()
        return smaller
    except Exception:
        return picture


# ══════════════════════════════════════════════════════════════════
#  The PDF receipt — same layout as the old software
# ══════════════════════════════════════════════════════════════════
def _split_text_to_lines(text, max_chars=80):
    """Split long text into lines roughly at word boundaries."""
    if not text:
        return []
    lines, cur = [], ""
    for word in str(text).split():
        if len(cur) + len(word) + 1 <= max_chars:
            cur = (cur + " " + word).strip()
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _pdf_name(receipt):
    safe = "".join(c for c in (receipt.name or "") if c.isalnum() or c in (" ", ".", "_")).strip().replace(" ", "_")
    return f"{safe or 'Receipt'}.{int(receipt.receipt_no):04d}.pdf"


def build_receipt_pdf(receipt):
    """Returns the receipt as PDF bytes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, black

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Receipt {receipt.receipt_no} - {receipt.name}")
    width, height = A4
    margin = 20 * mm
    amount_paid = _amount(receipt)

    # Border
    c.setStrokeColor(black)
    c.setLineWidth(1)
    c.rect(margin / 2, margin / 2, width - margin, height - margin)

    # Logo
    logo_w = 0
    logo = _receipt_picture("logo")
    if logo is not None:
        try:
            c.drawImage(logo, margin, height - margin - 20 * mm, 22 * mm, 22 * mm,
                        preserveAspectRatio=True, mask="auto")
            logo_w = 22 * mm
        except Exception:
            logo_w = 0

    # Header
    header_y = height - margin - 5 * mm
    c.setFillColor(HexColor("#C00000"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(logo_w + margin + 5 * mm, header_y, CLINIC_NAME)

    c.setFillColor(black)
    c.setFont("Helvetica", 10)
    header_y -= 6 * mm
    c.drawString(logo_w + margin + 5 * mm, header_y, CLINIC_ADDRESS)
    header_y -= 5 * mm
    c.drawString(logo_w + margin + 5 * mm, header_y, CLINIC_PHONE)

    y = header_y - 12 * mm

    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "RECEIPT")
    y -= 8 * mm

    # Date + Receipt No
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Date: {receipt.receipt_date.strftime('%d-%b-%Y')}")
    c.drawRightString(width - margin, y, f"Receipt No: {receipt.receipt_no}")
    y -= 12 * mm

    # Patient Info
    for label, value in (("Name:", receipt.name or ""),
                         ("Case Id:", receipt.case_no or ""),
                         ("Mobile:", receipt.mobile or "")):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(margin + 40 * mm, y, value)
        y -= 7 * mm

    # Treatments title
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Treatments")
    y -= 6 * mm
    c.line(margin, y + 3 * mm, width - margin, y + 3 * mm)

    # Table header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "No")
    c.drawString(margin + 18 * mm, y, "Treatment & Description")
    c.drawRightString(width - margin - 20 * mm, y, "Amount (Rs.)")
    y -= 5 * mm
    c.setFont("Helvetica", 10)

    # Treatment rows
    for idx, t in enumerate(receipt.treatments(), start=1):
        if y < 60 * mm:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 10)

        name = str(t.get("name") or "")
        amount = _safe_float(t.get("amount"))
        desc = str(t.get("description") or "").strip()

        c.drawString(margin, y, str(idx))
        c.drawString(margin + 18 * mm, y, name)
        c.drawRightString(width - margin - 20 * mm, y, f"{amount:.2f}")
        y -= 5 * mm

        if desc:
            c.setFont("Helvetica-Oblique", 8)
            for line in _split_text_to_lines(desc, 85):
                c.drawString(margin + 22 * mm, y, line)
                y -= 4 * mm
            y -= 2 * mm
            c.setFont("Helvetica", 10)

        if t.get("charge_id"):
            fee, disc = _safe_float(t.get("charge_fee")), _safe_float(t.get("charge_discount"))
            parts = [f"Charge Rs. {fee:.2f}" + (f" - discount Rs. {disc:.2f} = Rs. {_safe_float(t.get('charge_net')):.2f}" if disc > 0 else "")]
            if _safe_float(t.get("paid_before")) > 0:
                parts.append(f"paid earlier Rs. {_safe_float(t.get('paid_before')):.2f}")
            left = _safe_float(t.get("balance_after"))
            parts.append(f"paid now Rs. {amount:.2f}")
            parts.append("fully paid" if left <= 0.004 else f"balance Rs. {left:.2f}")
            # kept inside the page: wrapped onto a second line when long
            c.setFont("Helvetica", 8)
            room = width - 2 * margin - 24 * mm
            line = ""
            for part in parts:
                trial = part if not line else f"{line}  |  {part}"
                if line and c.stringWidth(trial, "Helvetica", 8) > room:
                    c.drawString(margin + 22 * mm, y + 1 * mm, line)
                    y -= 4 * mm
                    line = part
                else:
                    line = trial
            c.drawString(margin + 22 * mm, y + 1 * mm, line)
            y -= 4 * mm
            c.setFont("Helvetica", 10)

    # Total amount
    c.line(margin, y + 3 * mm, width - margin, y + 3 * mm)
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - margin - 20 * mm, y, f"Total: Rs. {amount_paid:.2f}")
    y -= 10 * mm

    # Balances (payments made through the patient account)
    account_lines = [t for t in receipt.treatments() if t.get("charge_id")]
    if account_lines:
        left_here = sum(max(_safe_float(t.get("balance_after")), 0.0) for t in account_lines)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(width - margin - 20 * mm, y + 3 * mm,
                          "Balance on these treatments: " + ("nil (fully paid)" if left_here <= 0.004 else f"Rs. {left_here:.2f}"))
        y -= 2 * mm
        if receipt.balance_after is not None:
            c.drawRightString(width - margin - 20 * mm, y,
                              f"Total balance due (all treatments): Rs. {float(receipt.balance_after):.2f}")
            y -= 8 * mm

    # Amount in words
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin, y, f"Amount in Words: Rupees {amount_in_words(amount_paid)} Only")
    y -= 12 * mm

    # Payment methods
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Payment Method(s): {receipt.payment_methods or ''}")
    y -= 10 * mm

    # Notes
    for paragraph in str(receipt.notes or "").splitlines() or [""]:
        for line in _split_text_to_lines(paragraph, 90):
            if y < margin + 20 * mm:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 10)
            c.drawString(margin, y, line)
            y -= 4.5 * mm

    # Signature block
    sig_width = 60 * mm
    sig_height = 25 * mm
    sig_x = width - margin - sig_width
    sig_y = y - 15 * mm

    # If not enough space → new page
    if sig_y < margin + 40 * mm:
        c.showPage()
        sig_x = width - margin - sig_width
        sig_y = height - margin - 60 * mm

    # The signature sits centred above the words "Authorized Signatory".
    label = "Authorized Signatory"
    label_width = c.stringWidth(label, "Helvetica-Bold", 10)
    label_centre = width - margin - label_width / 2
    signature = _receipt_picture("signature")
    if signature is not None:
        try:
            img_w, img_h = signature.getSize()
            scale = min(sig_width / float(img_w), sig_height / float(img_h))
            draw_w, draw_h = img_w * scale, img_h * scale
            draw_x = min(label_centre - draw_w / 2, width - margin - draw_w)   # never past the right margin
            c.drawImage(signature, draw_x, sig_y, width=draw_w, height=draw_h, mask="auto")
        except Exception as exc:
            print("[billing] signature could not be drawn:", exc)

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - margin, sig_y - 3 * mm, label)

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, margin, RECEIPT_FOOTER)

    c.save()
    return buffer.getvalue()


# ══════════════════════════════════════════════════════════════════
#  Excel — same columns as the old monthly sheet
# ══════════════════════════════════════════════════════════════════
def _treatment_summary(receipt):
    lines = []
    for t in receipt.treatments():
        amount = _safe_float(t.get("amount"))
        shown = int(amount) if amount.is_integer() else amount
        desc = str(t.get("description") or "")
        lines.append(f"{t.get('name', '')}" + (f" {desc}" if desc else "") + f" ({shown})")
    return "\n".join(lines)


def build_excel(receipts):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(EXCEL_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for r in receipts:
        amount = _amount(r)
        ws.append([
            r.receipt_date.strftime("%Y-%m-%d"),
            r.receipt_no,
            r.name,
            r.case_no or "",
            r.mobile or "",
            _treatment_summary(r),
            int(amount) if float(amount).is_integer() else amount,
            r.payment_methods or "",
            "" if r.balance_after is None else (int(r.balance_after) if float(r.balance_after).is_integer() else float(r.balance_after)),
        ])

    summary_col = ws.cell(row=1, column=EXCEL_COLUMNS.index("treatment_summary") + 1).column_letter
    for cell in ws[summary_col]:
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions[summary_col].width = 40
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["C"].width = 26

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# ══════════════════════════════════════════════════════════════════
#  Receipt files — financial-year folders, on this computer or in
#  object storage (the same object storage the X-rays and photos use)
#
#    receipts/Financial year 2026-2027/Sep2026/pdf/Anitha_Rao.0004.pdf
#    receipts/Financial year 2026-2027/Sep2026/excel/Sep2026.xlsx
#
#  The month folders are exactly like the old billing software's
#  (receipts\Sep2026\excel, receipts\Sep2026\pdf, Sep2026.xlsx), with the
#  financial year on top. The financial year runs April to March:
#  a receipt dated 15-Jan-2027 goes to "Financial year 2026-2027/Jan2027".
#  The folders follow each receipt's own date and are made by themselves.
#
#  Where the files go:
#    * BILLING_STORAGE=s3  (or, if BILLING_STORAGE is not set, the same
#      choice as the images: IMAGE_STORAGE=s3) → the object-storage bucket
#      set up for the images (S3_BUCKET, S3_ACCESS_KEY_ID,
#      S3_SECRET_ACCESS_KEY, S3_REGION, S3_ENDPOINT_URL, S3_PREFIX).
#    * otherwise → a folder on the server:
#      <backend folder>\receipts\…   (BILLING_FILES_FOLDER=D:\Somewhere puts
#      the receipts folder inside that folder instead)
# ══════════════════════════════════════════════════════════════════
FILES_TOP = "receipts"

_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def files_enabled():
    return (os.environ.get("BILLING_SAVE_FILES") or "1").strip().lower() not in ("0", "false", "no", "off")


def storage_kind():
    chosen = (os.environ.get("BILLING_STORAGE") or os.environ.get("IMAGE_STORAGE") or "local").strip().lower()
    return "s3" if chosen == "s3" else "local"


def local_root():
    custom = (os.environ.get("BILLING_FILES_FOLDER") or "").strip().strip('"')
    return os.path.abspath(custom) if custom else _BACKEND_ROOT          # → <backend>\receipts\…


def financial_year(day):
    """2026-2027 for any day from 1-Apr-2026 to 31-Mar-2027."""
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{start + 1}"


def month_folder_key(day):
    return f"{FILES_TOP}/Financial year {financial_year(day)}/{month_name(day)}"      # …/Sep2026


def receipt_pdf_key(receipt):
    return f"{month_folder_key(receipt.receipt_date)}/pdf/{_pdf_name(receipt)}"


def month_excel_key(day):
    return f"{month_folder_key(day)}/excel/{month_name(day)}.xlsx"                     # Sep2026.xlsx


def _valid_key(key):
    """Only files inside receipts/…, never anything outside it."""
    key = str(key or "")
    parts = key.split("/")
    return (key.startswith(FILES_TOP + "/") and "\\" not in key and "\x00" not in key
            and all(p not in ("", ".", "..") for p in parts) and len(key) < 600)


class _LocalFiles:
    kind = "local"

    def where(self):
        return local_root()

    def _path(self, key):
        root = os.path.abspath(local_root())
        path = os.path.abspath(os.path.join(root, *key.split("/")))
        if not (path == root or path.startswith(root + os.sep)):
            raise _Refuse("This file is not in the receipts folder.", 400)
        return path

    def put(self, key, data, content_type=None):
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temp = f"{path}.{os.getpid()}.{id(data)}.tmp"
        with open(temp, "wb") as handle:          # the whole file at once: nobody opens a half-written one
            handle.write(data)
        try:
            os.replace(temp, path)
        except OSError:
            try:
                os.remove(temp)
            except OSError:
                pass
            raise

    def get(self, key):
        path = self._path(key)
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as handle:
            return handle.read()

    def exists(self, key):
        return os.path.exists(self._path(key))

    def delete(self, key):
        path = self._path(key)
        if os.path.isfile(path):
            os.remove(path)

    def list(self, prefix):
        folder = self._path(prefix.rstrip("/"))
        found = []
        for base, _, names in os.walk(folder):
            for name in names:
                if name.endswith(".tmp"):
                    continue
                full = os.path.join(base, name)
                rel = os.path.relpath(full, os.path.abspath(local_root())).replace(os.sep, "/")
                stat = os.stat(full)
                found.append({"key": rel, "size": stat.st_size,
                              "modified": (datetime.utcfromtimestamp(stat.st_mtime) + _IST).strftime("%d-%m-%Y %I:%M %p")})
        return found

    def check_writable(self):
        probe = f"{FILES_TOP}/.write-check-{os.getpid()}"
        self.put(probe, b"ok")
        self.delete(probe)


class _ObjectStorageFiles:
    """S3-compatible object storage (AWS S3, Cloudflare R2, DigitalOcean
    Spaces, Backblaze B2, MinIO …) — the same settings as the images."""
    kind = "s3"
    _client = None
    _client_settings = None

    def _settings(self):
        return tuple(os.environ.get(k, "").strip() for k in
                     ("S3_BUCKET", "S3_ENDPOINT_URL", "S3_REGION", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY", "S3_PREFIX"))

    def bucket(self):
        bucket = os.environ.get("S3_BUCKET", "").strip()
        if not bucket:
            raise _Refuse("Object storage is switched on but S3_BUCKET is not set in the backend's settings.", 500)
        return bucket

    def _full(self, key):
        prefix = os.environ.get("S3_PREFIX", "").strip().strip("/")
        return f"{prefix}/{key}" if prefix else key

    def _short(self, full):
        prefix = os.environ.get("S3_PREFIX", "").strip().strip("/")
        return full[len(prefix) + 1:] if prefix and full.startswith(prefix + "/") else full

    def client(self):
        settings = self._settings()
        if _ObjectStorageFiles._client is None or _ObjectStorageFiles._client_settings != settings:
            import boto3
            from botocore.config import Config
            # Short waits: if the storage cannot be reached, saving a receipt
            # must not hang — it is reported and done later instead.
            kwargs = {"config": Config(connect_timeout=5, read_timeout=30, retries={"max_attempts": 2})}
            _, endpoint, region, key_id, secret, _ = settings
            if endpoint:
                kwargs["endpoint_url"] = endpoint
            if region:
                kwargs["region_name"] = region
            if key_id and secret:
                kwargs["aws_access_key_id"] = key_id
                kwargs["aws_secret_access_key"] = secret
            _ObjectStorageFiles._client = boto3.client("s3", **kwargs)
            _ObjectStorageFiles._client_settings = settings
        return _ObjectStorageFiles._client

    def where(self):
        prefix = os.environ.get("S3_PREFIX", "").strip().strip("/")
        bucket = os.environ.get("S3_BUCKET", "").strip() or "(no bucket set)"
        return f"object storage: {bucket}" + (f"/{prefix}" if prefix else "")

    def put(self, key, data, content_type=None):
        extra = {"ContentType": content_type} if content_type else {}
        self.client().put_object(Bucket=self.bucket(), Key=self._full(key), Body=data, **extra)

    def get(self, key):
        try:
            answer = self.client().get_object(Bucket=self.bucket(), Key=self._full(key))
        except Exception as exc:
            if _missing_object(exc):
                return None
            raise
        return answer["Body"].read()

    def exists(self, key):
        try:
            self.client().head_object(Bucket=self.bucket(), Key=self._full(key))
            return True
        except Exception as exc:
            if _missing_object(exc):
                return False
            raise

    def delete(self, key):
        self.client().delete_object(Bucket=self.bucket(), Key=self._full(key))

    def list(self, prefix):
        found = []
        pages = self.client().get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket(), Prefix=self._full(prefix.rstrip("/") + "/"))
        for page in pages:
            for item in page.get("Contents", []):
                modified = item.get("LastModified")
                if modified is not None:
                    modified = (modified.replace(tzinfo=None) + _IST).strftime("%d-%m-%Y %I:%M %p")
                found.append({"key": self._short(item["Key"]), "size": int(item.get("Size") or 0),
                              "modified": modified or ""})
        return found

    def check_writable(self):
        probe = f"{FILES_TOP}/.write-check-{os.getpid()}"
        self.put(probe, b"ok", "text/plain")
        self.delete(probe)


def _missing_object(exc):
    code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", "")) if hasattr(exc, "response") else ""
    return code in ("404", "NoSuchKey", "NotFound")


_LOCAL_FILES = _LocalFiles()
_OBJECT_FILES = _ObjectStorageFiles()


def files_store():
    return _OBJECT_FILES if storage_kind() == "s3" else _LOCAL_FILES


def _file_problem(key, exc):
    store = files_store()
    if isinstance(exc, _Refuse):
        return exc.message
    if isinstance(exc, ImportError):
        missing = getattr(exc, "name", "") or ""
        if missing.startswith("boto"):
            return "The server is missing the object-storage tool. In the backend folder run:  pip install boto3"
        return "The server is missing the PDF or Excel tool. In the backend folder run:  pip install reportlab openpyxl"
    if store.kind == "local" and isinstance(exc, PermissionError):
        return (f"{key} could not be updated — it is probably open in another program (Excel or a PDF reader). "
                "Close it; it is brought up to date with the next receipt of that month, or with “Save files again”.")
    if store.kind == "s3":
        code = ""
        if hasattr(exc, "response"):
            code = str(exc.response.get("Error", {}).get("Code", ""))
        reason = f" ({code})" if code else f" ({exc.__class__.__name__})"
        return (f"{key} could not be saved in object storage{reason}. Check the storage settings and the internet "
                "connection. The receipt itself is saved — press “Save files again” (Billing → 📊 Excel & files) later.")
    return (f"{key} could not be written ({exc.__class__.__name__}). The receipt itself is saved — "
            "press “Save files again” (Billing → 📊 Excel & files) once the problem is fixed.")


def save_month_excel(day, problems, written):
    first = day.replace(day=1)
    following = (first.replace(year=first.year + 1, month=1) if first.month == 12
                 else first.replace(month=first.month + 1))
    receipts = (BillingReceipt.query
                .filter(BillingReceipt.receipt_date >= first, BillingReceipt.receipt_date < following)
                .order_by(BillingReceipt.receipt_date.asc(), BillingReceipt.receipt_no.asc()).all())
    key = month_excel_key(day)
    try:
        if not receipts and not files_store().exists(key):
            return                      # nothing to show and no sheet yet: no empty folders
        files_store().put(key, build_excel(receipts), _CONTENT_TYPES[".xlsx"])
        written.append(key)
    except Exception as exc:
        problems.append(_file_problem(key, exc))


def save_receipt_pdf(receipt, problems, written):
    key = receipt_pdf_key(receipt)
    try:
        files_store().put(key, build_receipt_pdf(receipt), _CONTENT_TYPES[".pdf"])
        written.append(key)
        receipt.files_saved = True
        return True
    except Exception as exc:
        problems.append(_file_problem(key, exc))
        receipt.files_saved = False          # tried again by itself with a later receipt
        return False


def _catch_up(report, limit=10):
    """Receipts whose PDF could not be saved earlier (storage or internet was
    down) are saved now, together with their month's Excel sheet."""
    waiting = (BillingReceipt.query.filter(BillingReceipt.files_saved.is_(False))
               .order_by(BillingReceipt.id.asc()).limit(limit).all())
    months = set()
    for receipt in waiting:
        if not save_receipt_pdf(receipt, report["problems"], report["written"]):
            return
        months.add(receipt.receipt_date.replace(day=1))
    for month in sorted(months):
        save_month_excel(month, report["problems"], report["written"])


def remove_key(key, problems):
    try:
        files_store().delete(key)
    except Exception as exc:
        problems.append(_file_problem(key, exc))


def update_folders(pdf_for=None, old_key=None, months=()):
    """Brings the receipt files up to date after a change. Never raises:
    the receipt is already saved in the database whatever happens here."""
    report = {"enabled": files_enabled(), "storage": storage_kind(), "folder": "", "written": [], "problems": []}
    if not report["enabled"]:
        return report
    try:
        report["folder"] = files_store().where()
        if old_key and (pdf_for is None or old_key != receipt_pdf_key(pdf_for)):
            remove_key(old_key, report["problems"])
        if pdf_for is not None:
            save_receipt_pdf(pdf_for, report["problems"], report["written"])
        for key in sorted({(d.year, d.month) for d in months if d}):
            save_month_excel(date(key[0], key[1], 1), report["problems"], report["written"])
        if not report["problems"]:
            _catch_up(report)
    except Exception as exc:                           # e.g. the drive or the bucket is missing
        report["problems"].append(_file_problem(FILES_TOP, exc))
    try:
        db.session.commit()                            # remembers which receipts' PDFs are saved
    except Exception:
        db.session.rollback()
    for problem in report["problems"]:
        print("[billing] files:", problem)
    return report


# ══════════════════════════════════════════════════════════════════
#  Bringing over the receipts of the old billing software
# ══════════════════════════════════════════════════════════════════
def _read_old_database(path):
    """Reads the old software's payments.db (SQLite). Returns a list of rows.
    The file is opened read-only and is never changed."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
    try:
        columns = [row[1] for row in con.execute("PRAGMA table_info(receipt)")]
        needed = {"receipt_no", "date", "name", "amount_paid"}
        if not needed <= set(columns):
            raise _Refuse("This file is not the old billing software's database. "
                          "Please choose the payments.db file from the old billing software's folder.")
        wanted = ["receipt_no", "date", "name", "case_no", "mobile", "treatments_json",
                  "amount_paid", "payment_methods", "notes", "visit_id"]
        have = [c for c in wanted if c in columns]
        rows = con.execute(f"SELECT {', '.join(have)} FROM receipt ORDER BY receipt_no").fetchall()
        return [dict(zip(have, row)) for row in rows]
    except sqlite3.DatabaseError:
        raise _Refuse("This file could not be read as the old billing software's database. "
                      "Please choose the payments.db file from the old billing software's folder.")
    finally:
        con.close()


def _old_row_to_values(row):
    """One old receipt, tidied. Returns None when it cannot be used."""
    try:
        receipt_no = int(row.get("receipt_no"))
    except (TypeError, ValueError):
        return None
    if receipt_no <= 0:
        return None
    try:
        when = datetime.strptime(str(row.get("date") or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    name = _text(row.get("name"), 200)
    if not name:
        return None

    try:
        treatments = json.loads(row.get("treatments_json") or "[]")
    except Exception:
        treatments = []
    cleaned = []
    for t in treatments if isinstance(treatments, list) else []:
        if isinstance(t, dict) and _text(t.get("name"), 200):
            cleaned.append({"name": _text(t.get("name"), 200),
                            "amount": round(_safe_float(t.get("amount")), 2),
                            "description": _text(t.get("description"), 500)})
    try:
        visit_id = int(row.get("visit_id")) if row.get("visit_id") else None
    except (TypeError, ValueError):
        visit_id = None
    return {
        "receipt_no": receipt_no,
        "receipt_date": when,
        "name": name,
        "case_no": _text(row.get("case_no"), 100),
        "mobile": _text(row.get("mobile"), 30),
        "treatments": cleaned,
        "amount_paid": round(_safe_float(row.get("amount_paid")), 2),
        "payment_methods": _text(row.get("payment_methods"), 200),
        "notes": _text(row.get("notes"), 5000),
        "visit_id": visit_id,
    }


# ══════════════════════════════════════════════════════════════════
#  ADDRESSES
# ══════════════════════════════════════════════════════════════════
def register_billing_routes(bp):
    """Adds the billing addresses to an existing group of addresses
    (visits.py calls this with its own group)."""

    # ── list / search ──────────────────────────────────────────────
    @bp.route("/clinic-billing/receipts", methods=["GET"], endpoint="billing_list")
    @require_login
    @_guard
    def billing_list():
        q = (request.args.get("q") or "").strip()
        visit_id = request.args.get("visit_id", type=int)
        patient_id = request.args.get("patient_id", type=int)
        query = BillingReceipt.query

        if visit_id:
            query = query.filter(BillingReceipt.visit_id == visit_id)
        if patient_id:
            query = query.filter(BillingReceipt.patient_id == patient_id)
        if q:
            like = f"%{q}%"
            wanted = [BillingReceipt.case_no.ilike(like),
                      BillingReceipt.name.ilike(like),
                      BillingReceipt.mobile.ilike(like)]
            if q.isdigit() and len(q) <= 9:
                wanted.append(BillingReceipt.receipt_no == int(q))
            query = query.filter(or_(*wanted))

        total = query.count()
        # Like the old software: the latest 200 when not searching, every match when searching.
        narrowed = bool(q or visit_id or patient_id)
        limit = 1000 if narrowed else 200
        rows = (query.order_by(BillingReceipt.receipt_date.desc(), BillingReceipt.receipt_no.desc())
                .limit(limit).all())
        ids = {r.patient_id for r in rows if r.patient_id}
        patients = {p.id: p for p in Patient.query.filter(Patient.id.in_(ids)).all()} if ids else {}
        return jsonify({
            "receipts": [_serialize(r, patients) for r in rows],
            "total": total,
            "all_receipts": BillingReceipt.query.count() if narrowed else total,
        }), 200

    # ── patient account ────────────────────────────────────────────
    def _patient_or_404(patient_id):
        patient = db.session.get(Patient, patient_id)
        if patient is None:
            raise _Refuse("This patient was not found.", 404)
        return patient

    @bp.route("/clinic-billing/patients/<int:patient_id>/account", methods=["GET"], endpoint="billing_account")
    @require_login
    @_guard
    def billing_account(patient_id):
        patient = _patient_or_404(patient_id)
        charges = (TreatmentCharge.query.filter_by(patient_id=patient_id)
                   .order_by(TreatmentCharge.charge_date.asc(), TreatmentCharge.id.asc()).all())
        ids = [c.id for c in charges]
        paid = _paid_by_charge(ids)
        receipts = (BillingReceipt.query.filter_by(patient_id=patient_id)
                    .order_by(BillingReceipt.receipt_date.desc(), BillingReceipt.receipt_no.desc()).all())
        by_receipt = {r.id: r for r in receipts}
        payments = {}
        if ids:
            for a in ReceiptAllocation.query.filter(ReceiptAllocation.charge_id.in_(ids)).all():
                r = by_receipt.get(a.receipt_id) or db.session.get(BillingReceipt, a.receipt_id)
                if r is None:
                    continue
                payments.setdefault(a.charge_id, []).append({
                    "receipt_id": r.id, "receipt_no": r.receipt_no,
                    "date": r.receipt_date.isoformat() if r.receipt_date else None, "amount": _money(a.amount)})
        rows = [_charge_out(c, paid, sorted(payments.get(c.id, []), key=lambda p: (p["date"] or "", p["receipt_no"])))
                for c in charges]
        visits = (Visit.query.filter_by(patient_id=patient_id).order_by(Visit.visit_date.desc()).all())
        visit_rows = []
        for v in visits:
            when = (v.visit_date + _IST) if v.visit_date else None
            visit_rows.append({
                "visit_id": v.id,
                "date": when.strftime("%Y-%m-%d") if when else None,
                "status": v.status or "",
                "closed": (v.status or "").strip().lower() in ("closed", "completed"),
                "billed": bool(getattr(v, "billing_closed", False)),
                "diagnosis": (getattr(v, "diagnosis", "") or "").strip(),
                "treatment_done": (getattr(v, "treatment_done", "") or "").strip(),
                "treatment_plan": (getattr(v, "treatment_plan", "") or "").strip(),
                "advice": (getattr(v, "advice", "") or "").strip(),
                "billing_note": (getattr(v, "billing_note", "") or "").strip(),
            })
        totals = {
            "fee": round(sum(r["fee"] for r in rows), 2),
            "discount": round(sum(r["discount"] for r in rows), 2),
            "net": round(sum(r["net"] for r in rows), 2),
            "paid": round(sum(r["paid"] for r in rows), 2),
            "balance": round(sum(r["balance"] for r in rows), 2),
            "open": sum(1 for r in rows if r["balance"] > 0.004),
            "received": round(sum(_amount(r) for r in receipts), 2),
        }
        return jsonify({
            "patient": {**_patient_card(patient), "age": patient.age, "gender": patient.gender or ""},
            "totals": totals,
            "charges": rows,
            "receipts": [_serialize(r, {patient.id: patient}) for r in receipts],
            "visits": visit_rows,
        }), 200

    @bp.route("/clinic-billing/patients/<int:patient_id>/charges", methods=["POST"], endpoint="billing_charge_add")
    @require_login
    @_guard
    def billing_charge_add(patient_id):
        _patient_or_404(patient_id)
        data = request.get_json(force=True, silent=True) or {}
        fields = _clean_charge(data)
        who = _who()
        charge = TreatmentCharge(patient_id=patient_id, visit_id=_charge_visit(patient_id, data.get("visit_id")),
                                 created_by=who, updated_by=who, **fields)
        db.session.add(charge)
        db.session.commit()
        return jsonify(_charge_out(charge, {})), 201

    def _charge_or_404(charge_id):
        charge = db.session.get(TreatmentCharge, charge_id)
        if charge is None:
            raise _Refuse("This treatment was not found. It may have been deleted.", 404)
        return charge

    @bp.route("/clinic-billing/charges/<int:charge_id>", methods=["PUT"], endpoint="billing_charge_update")
    @require_login
    @_guard
    def billing_charge_update(charge_id):
        _one_at_a_time()
        charge = _charge_or_404(charge_id)
        data = request.get_json(force=True, silent=True) or {}
        fields = _clean_charge(data, current=charge)
        paid = _paid_by_charge([charge.id]).get(charge.id, 0.0)
        if round(fields["fee"] - fields["discount"], 2) + 0.004 < paid:
            raise _Refuse(f"₹{paid:.2f} has already been paid towards “{charge.treatment}”, so its charge after "
                          f"discount cannot be less than that. Change or delete those payments first.")
        for key, value in fields.items():
            setattr(charge, key, value)
        if "visit_id" in data:
            charge.visit_id = _charge_visit(charge.patient_id, data.get("visit_id"))
        charge.updated_by = _who()
        charge.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(_charge_out(charge, {charge.id: paid})), 200

    @bp.route("/clinic-billing/charges/<int:charge_id>", methods=["DELETE"], endpoint="billing_charge_delete")
    @require_login
    @_guard
    def billing_charge_delete(charge_id):
        _one_at_a_time()
        charge = _charge_or_404(charge_id)
        used = ReceiptAllocation.query.filter_by(charge_id=charge.id).all()
        if used:
            numbers = sorted({db.session.get(BillingReceipt, a.receipt_id).receipt_no for a in used
                              if db.session.get(BillingReceipt, a.receipt_id)})
            raise _Refuse(f"Payments have been made towards “{charge.treatment}” (receipt #{', #'.join(map(str, numbers))}). "
                          "Change or delete those payments first, then delete the treatment.", 409)
        name = charge.treatment
        db.session.delete(charge)
        db.session.commit()
        return jsonify({"status": "deleted", "treatment": name}), 200

    # ── patient picker ─────────────────────────────────────────────
    @bp.route("/clinic-billing/patients", methods=["GET"], endpoint="billing_patients")
    @require_login
    @_guard
    def billing_patients():
        q = (request.args.get("q") or "").strip()
        if len(q) < 2:
            return jsonify([]), 200
        like = f"%{q}%"
        rows = (Patient.query
                .filter(or_(Patient.name.ilike(like), Patient.case_number.ilike(like), Patient.mobile.ilike(like)))
                .order_by(Patient.name.asc()).limit(20).all())
        return jsonify([{**_patient_card(p), "age": p.age, "gender": p.gender or ""} for p in rows]), 200

    # ── what the Add Payment form needs ────────────────────────────
    @bp.route("/clinic-billing/receipts/new", methods=["GET"], endpoint="billing_new")
    @require_login
    @_guard
    def billing_new():
        return jsonify({
            "receipt_no": _next_receipt_no(),
            "date": _today_ist().isoformat(),
            "treatments": DEFAULT_TREATMENTS,
            "payment_methods": PAYMENT_METHODS,
        }), 200

    # ── create ─────────────────────────────────────────────────────
    @bp.route("/clinic-billing/receipts", methods=["POST"], endpoint="billing_create")
    @require_login
    @_guard
    def billing_create():
        data = request.get_json(force=True, silent=True) or {}
        form = _read_receipt_form(data)

        visit_id = None
        try:
            raw_visit = data.get("visit_id")
            if raw_visit not in (None, "", 0, "0"):
                visit_id = int(raw_visit)
        except (TypeError, ValueError):
            visit_id = None
        visit = db.session.get(Visit, visit_id) if visit_id is not None else None
        if visit is None:
            visit_id = None            # the visit no longer exists: keep the receipt, drop the link
        # The patient: always the visit's patient for a visit; otherwise the one chosen in the form.
        patient_id = visit.patient_id if visit is not None else _chosen_patient(data)

        who = _who()
        receipt = None
        # Two people saving at the same moment must never get the same number
        # (and never both pay the last rupee of the same treatment).
        for _ in range(8):
            _one_at_a_time()
            receipt = BillingReceipt(receipt_no=_next_receipt_no(), visit_id=visit_id, patient_id=patient_id,
                                     created_by=who, updated_by=who)
            _apply(receipt, form)
            db.session.add(receipt)
            try:
                db.session.flush()
                break
            except IntegrityError:
                db.session.rollback()
                receipt = None
        if receipt is None:
            raise _Refuse("The receipt number was taken by another receipt at the same moment. "
                          "Nothing was saved — please press Save again.", 409)

        if _wants_allocation(data):
            lines = _allocate(receipt, patient_id, data, who)
            _finish_account_receipt(receipt, lines, form["treatments"])

        _set_visit_billed(visit_id, True)
        db.session.commit()
        files = update_folders(pdf_for=receipt, months=[receipt.receipt_date])
        return jsonify({**_serialize(receipt), "files": files}), 201

    def _chosen_patient(data):
        """patient_id sent by the form: None to leave unlinked; refused if it does not exist."""
        raw = data.get("patient_id")
        if raw in (None, "", 0, "0"):
            return None
        try:
            patient = db.session.get(Patient, int(raw))
        except (TypeError, ValueError):
            patient = None
        if patient is None:
            raise _Refuse("The chosen patient was not found. Please choose the patient again.")
        return patient.id

    # ── one receipt ────────────────────────────────────────────────
    def _find(receipt_id):
        receipt = db.session.get(BillingReceipt, receipt_id)
        if receipt is None:
            raise _Refuse("This receipt was not found. It may have been deleted.", 404)
        return receipt

    @bp.route("/clinic-billing/receipts/<int:receipt_id>", methods=["GET"], endpoint="billing_get")
    @require_login
    @_guard
    def billing_get(receipt_id):
        return jsonify(_serialize(_find(receipt_id))), 200

    @bp.route("/clinic-billing/receipts/<int:receipt_id>", methods=["PUT"], endpoint="billing_update")
    @require_login
    @_guard
    def billing_update(receipt_id):
        receipt = _find(receipt_id)
        data = request.get_json(force=True, silent=True) or {}
        _one_at_a_time()                      # balances are checked with nobody else paying at the same moment
        has_allocations = ReceiptAllocation.query.filter_by(receipt_id=receipt.id).first() is not None
        if "name" not in data and receipt.name:   # the account screen does not send the name
            data = {**data, "name": receipt.name}
        form = _read_receipt_form(data)
        if isinstance(data, dict) and "patient_id" in data:
            chosen = _chosen_patient(data)
            if (receipt.visit_id or has_allocations) and chosen != receipt.patient_id:
                raise _Refuse("This payment is in a patient's account (or was made for a clinic visit), "
                              "so it stays with that patient.")
            receipt.patient_id = chosen
        old_key, old_day = receipt_pdf_key(receipt), receipt.receipt_date
        kept_lines, kept_amount = receipt.treatments_json, receipt.amount_paid
        _apply(receipt, form)                 # receipt number and visit never change
        if _wants_allocation(data):
            lines = _allocate(receipt, receipt.patient_id, data, _who())
            _finish_account_receipt(receipt, lines, form["treatments"])
        elif has_allocations:
            # changed from the simple form: the treatments paid stay as they were
            receipt.treatments_json, receipt.amount_paid = kept_lines, kept_amount
        receipt.updated_by = _who()
        receipt.updated_at = datetime.utcnow()
        db.session.commit()
        # a new date or name moves the PDF; both months' sheets are rewritten
        files = update_folders(pdf_for=receipt, old_key=old_key, months=[old_day, receipt.receipt_date])
        return jsonify({**_serialize(receipt), "files": files}), 200

    @bp.route("/clinic-billing/receipts/<int:receipt_id>", methods=["DELETE"], endpoint="billing_delete")
    @require_login
    @_guard
    def billing_delete(receipt_id):
        body = request.get_json(force=True, silent=True) or {}
        reason = _text((body.get("reason") if isinstance(body, dict) else None) or request.args.get("reason"), 500)
        if len(reason) < 3:
            raise _Refuse("Please write why this receipt is being deleted. The reason is kept in the deletion log.")
        receipt = _find(receipt_id)
        # The deletion log: a full copy first, so nothing is lost.
        copy = _serialize(receipt)
        copy["allocations"] = [{"charge_id": a.charge_id, "amount": _money(a.amount)}
                               for a in ReceiptAllocation.query.filter_by(receipt_id=receipt.id).all()]
        copy.pop("files", None)
        db.session.add(ReceiptDeletion(
            receipt_id=receipt.id, receipt_no=receipt.receipt_no, receipt_date=receipt.receipt_date,
            name=receipt.name, case_no=receipt.case_no, mobile=receipt.mobile, patient_id=receipt.patient_id,
            visit_id=receipt.visit_id, amount_paid=receipt.amount_paid,
            receipt_json=json.dumps(copy, ensure_ascii=False, default=str),
            reason=reason, deleted_by=_who() or "", deleted_at=datetime.utcnow()))
        visit_id = receipt.visit_id
        number = receipt.receipt_no
        old_key, old_day = receipt_pdf_key(receipt), receipt.receipt_date
        ReceiptAllocation.query.filter_by(receipt_id=receipt.id).delete()      # the balances go back up
        db.session.delete(receipt)
        db.session.flush()
        visit_reopened = False
        # If that was the only receipt of a visit, the visit is unbilled again.
        if visit_id and not BillingReceipt.query.filter_by(visit_id=visit_id).first():
            _set_visit_billed(visit_id, False)
            visit_reopened = True
        db.session.commit()
        files = update_folders(old_key=old_key, months=[old_day])
        return jsonify({"status": "deleted", "receipt_no": number, "reason": reason,
                        "visit_back_to_pending": visit_reopened, "files": files}), 200

    # ── the deletion log ───────────────────────────────────────────
    @bp.route("/clinic-billing/deleted", methods=["GET"], endpoint="billing_deleted")
    @require_login
    @_guard
    def billing_deleted():
        query = ReceiptDeletion.query
        q = _text(request.args.get("q"), 100)
        if q:
            like = f"%{q}%"
            conditions = [ReceiptDeletion.name.ilike(like), ReceiptDeletion.case_no.ilike(like),
                          ReceiptDeletion.mobile.ilike(like), ReceiptDeletion.reason.ilike(like),
                          ReceiptDeletion.deleted_by.ilike(like)]
            if q.isdigit():
                conditions.append(ReceiptDeletion.receipt_no == int(q))
            query = query.filter(or_(*conditions))
        if request.args.get("patient_id", "").isdigit():
            query = query.filter(ReceiptDeletion.patient_id == int(request.args["patient_id"]))
        rows = query.order_by(ReceiptDeletion.deleted_at.desc(), ReceiptDeletion.id.desc()).limit(500).all()
        numbers = {d.receipt_no for d in rows}
        now_used = {}
        if numbers:
            for r in BillingReceipt.query.filter(BillingReceipt.receipt_no.in_(list(numbers))).all():
                now_used[r.receipt_no] = {"id": r.id, "name": r.name, "date": r.receipt_date.isoformat() if r.receipt_date else None,
                                          "amount_paid": _amount(r)}
        return jsonify({"deleted": [_deletion_out(d, now_used.get(d.receipt_no)) for d in rows], "count": len(rows),
                        "total_amount": round(sum(float(d.amount_paid or 0) for d in rows), 2)}), 200

    # ── the PDF receipt ────────────────────────────────────────────
    @bp.route("/clinic-billing/receipts/<int:receipt_id>/pdf", methods=["GET"], endpoint="billing_pdf")
    @require_login
    @_guard
    def billing_pdf(receipt_id):
        receipt = _find(receipt_id)
        try:
            pdf = build_receipt_pdf(receipt)
        except ImportError:
            raise _Refuse("The server is missing the PDF tool. In the backend folder run:  pip install reportlab", 500)
        download = request.args.get("download") in ("1", "true", "yes")
        return send_file(io.BytesIO(pdf), mimetype="application/pdf",
                         as_attachment=download, download_name=_pdf_name(receipt))

    # ── Excel ──────────────────────────────────────────────────────
    @bp.route("/clinic-billing/excel", methods=["GET"], endpoint="billing_excel")
    @require_login
    @_guard
    def billing_excel():
        today = _today_ist()
        day_from = _parse_date(request.args.get("date_from"), "Please choose the From date.") or today.replace(day=1)
        day_to = _parse_date(request.args.get("date_to"), "Please choose the To date.") or today
        if day_to < day_from:
            raise _Refuse("The To date is before the From date.")

        receipts = (BillingReceipt.query
                    .filter(BillingReceipt.receipt_date >= day_from, BillingReceipt.receipt_date <= day_to)
                    .order_by(BillingReceipt.receipt_date.asc(), BillingReceipt.receipt_no.asc()).all())
        try:
            workbook = build_excel(receipts)
        except ImportError:
            raise _Refuse("The server is missing the Excel tool. In the backend folder run:  pip install openpyxl", 500)

        # A whole (or part of one) calendar month is named like the monthly sheet: Sep2026.xlsx
        same_month = (day_from.year, day_from.month) == (day_to.year, day_to.month)
        name = (month_name(day_from) + ".xlsx") if same_month \
            else f"Receipts_{day_from.isoformat()}_to_{day_to.isoformat()}.xlsx"
        response = send_file(io.BytesIO(workbook), as_attachment=True, download_name=name,
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response.headers["X-Receipt-Count"] = str(len(receipts))
        return response

    # ── receipt files ──────────────────────────────────────────────
    @bp.route("/clinic-billing/files/status", methods=["GET"], endpoint="billing_files_status")
    @require_login
    @_guard
    def billing_files_status():
        answer = {"enabled": files_enabled(), "storage": storage_kind(), "folder": "", "writable": False,
                  "example": f"{month_folder_key(_today_ist())}/pdf/  ·  {month_excel_key(_today_ist())}",
                  "problem": ""}
        if files_enabled():
            store = files_store()
            try:
                answer["folder"] = store.where()
                store.check_writable()
                answer["writable"] = True
            except Exception as exc:
                answer["problem"] = _file_problem(FILES_TOP, exc)
        return jsonify(answer), 200

    @bp.route("/clinic-billing/files/months", methods=["GET"], endpoint="billing_files_months")
    @require_login
    @_guard
    def billing_files_months():
        """Financial years and months that have receipts (newest first)."""
        days = [row[0] for row in db.session.query(BillingReceipt.receipt_date).distinct().all() if row[0]]
        months = sorted({(d.year, d.month) for d in days}, reverse=True)
        years = {}
        for year, month in months:
            fy = financial_year(date(year, month, 1))
            years.setdefault(fy, []).append({"month": _MONTHS[month - 1], "label": f"{_MONTHS[month - 1]} {year}",
                                             "value": f"{year}-{month:02d}"})
        return jsonify([{"fy": fy, "label": f"Financial year {fy}", "months": items}
                        for fy, items in sorted(years.items(), reverse=True)]), 200

    @bp.route("/clinic-billing/files", methods=["GET"], endpoint="billing_files_list")
    @require_login
    @_guard
    def billing_files_list():
        if not files_enabled():
            raise _Refuse("Receipt files are switched off on the server (BILLING_SAVE_FILES=0).")
        value = (request.args.get("month") or "").strip()          # "2026-09"
        try:
            day = datetime.strptime(value + "-01", "%Y-%m-%d").date()
        except ValueError:
            raise _Refuse("Please choose a month.")
        folder = month_folder_key(day)
        try:
            found = files_store().list(folder)
        except _Refuse:
            raise
        except Exception as exc:
            raise _Refuse(_file_problem(folder, exc), 502)
        items = []
        for f in sorted(found, key=lambda x: x["key"]):
            rest = f["key"][len(folder) + 1:]
            sub = rest.split("/", 1)[0] if "/" in rest else ""
            kind = {"pdf": "Pdf", "excel": "Excel"}.get(sub)
            if kind is None:
                continue
            items.append({**f, "name": f["key"].rsplit("/", 1)[-1], "kind": kind})
        items.sort(key=lambda x: (x["kind"] != "Excel", x["name"].lower()))
        return jsonify({"folder": folder, "where": files_store().where(), "files": items}), 200

    @bp.route("/clinic-billing/files/download", methods=["GET"], endpoint="billing_files_download")
    @require_login
    @_guard
    def billing_files_download():
        key = request.args.get("key") or ""
        if not _valid_key(key):
            raise _Refuse("This file is not one of the receipt files.", 400)
        try:
            data = files_store().get(key)
        except _Refuse:
            raise
        except Exception as exc:
            raise _Refuse(_file_problem(key, exc), 502)
        if data is None:
            raise _Refuse("This file is not there any more. “Save files again” makes it again.", 404)
        name = key.rsplit("/", 1)[-1]
        ext = os.path.splitext(name)[1].lower()
        inline = request.args.get("inline") in ("1", "true", "yes")       # ?inline=1 → shown in the app
        return send_file(io.BytesIO(data), mimetype=_CONTENT_TYPES.get(ext, "application/octet-stream"),
                         as_attachment=not inline, download_name=name)

    @bp.route("/clinic-billing/files/sheet", methods=["GET"], endpoint="billing_files_sheet")
    @require_login
    @_guard
    def billing_files_sheet():
        """A month's Excel sheet as it is saved in the folder, for showing in the app."""
        key = request.args.get("key") or ""
        if not _valid_key(key) or not key.lower().endswith(".xlsx"):
            raise _Refuse("This is not one of the monthly Excel sheets.", 400)
        try:
            data = files_store().get(key)
        except _Refuse:
            raise
        except Exception as exc:
            raise _Refuse(_file_problem(key, exc), 502)
        if data is None:
            raise _Refuse("This sheet is not there any more. “Save files again” makes it again.", 404)
        try:
            from openpyxl import load_workbook
            book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            sheet = book.worksheets[0]
            rows = [list(r) for r in sheet.iter_rows(values_only=True)]
            book.close()
        except ImportError:
            raise _Refuse("The server is missing the Excel tool. In the backend folder run:  pip install openpyxl", 500)
        except Exception:
            raise _Refuse("This Excel sheet could not be read. “Save files again” makes it again.", 422)

        def cell(v):
            if v is None:
                return ""
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return v
            if isinstance(v, (datetime, date)):
                return v.strftime("%Y-%m-%d")
            return str(v)

        rows = [[cell(v) for v in r] for r in rows if r is not None and any(v not in (None, "") for v in r)]
        header = [str(h) for h in rows[0]] if rows else []
        body = rows[1:] if rows else []
        total = 0.0
        if "amount_paid" in header:
            at = header.index("amount_paid")
            for r in body:
                try:
                    total += float(r[at] or 0)
                except (TypeError, ValueError, IndexError):
                    pass
        return jsonify({"key": key, "name": key.rsplit("/", 1)[-1], "columns": header, "rows": body[:5000],
                        "count": len(body), "total_amount": round(total, 2)}), 200

    @bp.route("/clinic-billing/files/regenerate", methods=["POST"], endpoint="billing_files_regenerate")
    @require_login
    @_guard
    def billing_files_regenerate():
        """Like the old "Regenerate Excel" page: rewrites the monthly sheets of
        the chosen dates — and, if asked, every receipt's PDF in them."""
        if not files_enabled():
            raise _Refuse("Saving receipt files in folders is switched off on the server (BILLING_SAVE_FILES=0).")
        data = request.get_json(force=True, silent=True) or {}
        today = _today_ist()
        day_from = _parse_date(data.get("date_from"), "Please choose the From date.") or today.replace(day=1)
        day_to = _parse_date(data.get("date_to"), "Please choose the To date.") or today
        if day_to < day_from:
            raise _Refuse("The To date is before the From date.")
        if (day_to - day_from).days > 3700:
            raise _Refuse("Please choose at most ten years at a time.")

        report = {"enabled": True, "storage": storage_kind(), "folder": files_store().where(), "written": [], "problems": []}
        months, cursor = [], day_from.replace(day=1)
        while cursor <= day_to:
            months.append(cursor)
            cursor = cursor.replace(year=cursor.year + 1, month=1) if cursor.month == 12 else cursor.replace(month=cursor.month + 1)
        pdfs = 0
        if data.get("include_pdfs"):
            for receipt in (BillingReceipt.query
                            .filter(BillingReceipt.receipt_date >= day_from, BillingReceipt.receipt_date <= day_to)
                            .order_by(BillingReceipt.receipt_no.asc()).all()):
                before = len(report["written"])
                save_receipt_pdf(receipt, report["problems"], report["written"])
                pdfs += len(report["written"]) - before
                if len(report["problems"]) > 20:
                    break
        sheets_before = len(report["written"])
        for month in months:
            save_month_excel(month, report["problems"], report["written"])
        report["pdf_count"] = pdfs
        report["excel_count"] = len(report["written"]) - sheets_before
        report["written"] = report["written"][-30:]
        return jsonify(report), 200

    # ── bring over the old software's receipts ─────────────────────
    @bp.route("/clinic-billing/import-old", methods=["POST"], endpoint="billing_import_old")
    @require_login
    @_guard
    def billing_import_old():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            raise _Refuse("Please choose the payments.db file from the old billing software's folder.")

        blob = upload.read(MAX_IMPORT_BYTES + 1)
        if len(blob) > MAX_IMPORT_BYTES:
            raise _Refuse("This file is too large to be the old billing software's database.")
        if not blob.startswith(b"SQLite format 3\x00"):
            raise _Refuse("This file is not the old billing software's database. "
                          "Please choose the payments.db file from the old billing software's folder.")

        handle, path = tempfile.mkstemp(suffix=".db")
        try:
            with os.fdopen(handle, "wb") as tmp:
                tmp.write(blob)
            old_rows = _read_old_database(path)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        existing = {r.receipt_no: r for r in BillingReceipt.query.all()}
        # Old receipts are linked to the patient whose case number is exactly the same
        # (only when exactly one patient has that case number).
        by_case = {}
        for pid, case in db.session.query(Patient.id, Patient.case_number).all():
            if case and case.strip():
                by_case.setdefault(case.strip().lower(), []).append(pid)
        linked = 0
        who = _who()
        imported, already, unreadable, clashes = 0, 0, 0, []
        months_touched = set()

        for row in old_rows:
            values = _old_row_to_values(row)
            if values is None:
                unreadable += 1
                continue
            here = existing.get(values["receipt_no"])
            if here is not None:
                same = (here.name == values["name"] and here.receipt_date == values["receipt_date"]
                        and abs(_amount(here) - values["amount_paid"]) < 0.005)
                if same:
                    already += 1
                else:
                    clashes.append(values["receipt_no"])
                continue

            receipt = BillingReceipt(
                receipt_no=values["receipt_no"], receipt_date=values["receipt_date"],
                name=values["name"], case_no=values["case_no"], mobile=values["mobile"],
                treatments_json=json.dumps(values["treatments"], ensure_ascii=False),
                amount_paid=Decimal(str(values["amount_paid"])),
                payment_methods=values["payment_methods"], notes=values["notes"],
                visit_id=values["visit_id"], source="old-software",
                created_by=who, updated_by=who,
            )
            matches = by_case.get((values["case_no"] or "").strip().lower(), [])
            if values["visit_id"]:
                visit = db.session.get(Visit, values["visit_id"])
                receipt.patient_id = visit.patient_id if visit else None
            if receipt.patient_id is None and len(matches) == 1:
                receipt.patient_id = matches[0]
            if receipt.patient_id:
                linked += 1
            db.session.add(receipt)
            existing[values["receipt_no"]] = receipt
            imported += 1
            months_touched.add(values["receipt_date"].replace(day=1))

        db.session.commit()
        # The old software already has the PDFs of these receipts in its own
        # folder, so only the monthly Excel sheets are written here.
        # ("Save files again" can also make their PDFs.)
        files = update_folders(months=months_touched)
        return jsonify({
            "files": files,
            "linked_to_patients": linked,
            "in_file": len(old_rows),
            "imported": imported,
            "already_here": already,
            "unreadable": unreadable,
            "number_clashes": clashes[:50],
            "number_clash_count": len(clashes),
            "next_receipt_no": _next_receipt_no(),
        }), 200