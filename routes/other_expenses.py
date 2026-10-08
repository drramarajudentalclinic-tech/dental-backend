"""
routes/other_expenses.py
────────────────────────
Other Expenses — everything the clinic pays out that is not a patient bill:
doctor fees, lab, materials, salary, rent, electricity, repairs …

Each expense has a date, category, paid to (Doctor / Company / Person) and
the name, amount, how it was paid (Cash, UPI, Card, Cheque, Bank transfer)
and a description.

The month's Excel sheet is saved by itself in the same Financial-year
folders as the receipts (on the server, or in object storage — the same
settings as Billing):
    receipts/Financial year 2026-2027/Oct2026/other expenses/Other Exp Oct2026.xlsx
The month's Excel sheet is made fresh from the saved expenses every time an
expense of that month is added, changed or deleted (so it is always right),
with a TOTAL row and a second sheet "By category".

Deleting an expense needs a reason. A full copy, the reason, who and when are
kept in the deletion log (table other_expense_deletions).

Addresses (all need the login):
  GET    /api/other-expenses                 ?from=YYYY-MM-DD&to=YYYY-MM-DD&q=&category=   (newest first)
  GET    /api/other-expenses/meta            categories, payment methods, names used before
  POST   /api/other-expenses                 add      {date, category, type, party_name, amount, payment_method, description}
  PUT    /api/other-expenses/<id>            change
  DELETE /api/other-expenses/<id>            delete   {reason}   → deletion log
  GET    /api/other-expenses/summary         ?fy=2026-2027   month by month and by category
  GET    /api/other-expenses/excel           ?month=2026-10  the month's Excel sheet (download)
  POST   /api/other-expenses/files/regenerate {fy}  save every month's Excel sheet of that year again
  GET    /api/other-expenses/files/months    financial years and months that have expenses
  GET    /api/other-expenses/files           ?month=2026-10   that month's saved Excel sheet
  GET    /api/other-expenses/files/sheet     ?key=…/Other Exp Oct2026.xlsx   the saved sheet's rows, to show in the app
  GET    /api/other-expenses/files/download  ?key=…  (&inline=1 to show it)
  GET    /api/other-expenses/deleted         ?q=   the deletion log

The file storage is the one in billing_receipts.py (same routes folder);
without that file expenses still work, only the files are not written.
app.py does not change: it still registers other_expenses_bp and calls
run_other_expense_migrations(app).
"""

import io
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import func, or_, text

from database import db

try:
    from auth_utils import require_login
except ImportError:                      # the app keeps it in routes/
    from routes.auth_utils import require_login


other_expenses_bp = Blueprint("other_expenses", __name__, url_prefix="/api")

CATEGORIES = [
    "Doctor fee", "Lab charges", "Dental materials", "Medicines", "Salary", "Rent", "Electricity",
    "Water", "Internet / Phone", "Maintenance / Repairs", "Equipment", "Cleaning / Housekeeping",
    "Stationery / Printing", "Transport", "Tea / Snacks", "Marketing", "Other",
]
PAYMENT_METHODS = ["Cash", "UPI", "Card", "Cheque", "Bank transfer"]
PAID_TO_TYPES = ["Dr", "Company", "Other"]          # Doctor / Company / Person (kept as before)
MAX_AMOUNT = 10000000                                # 1 crore — anything above is a typing mistake
MAX_BILL_BYTES = 15 * 1024 * 1024
BILL_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
    ".pdf": "application/pdf", ".heic": "image/heic",
}
_IST = timedelta(hours=5, minutes=30)
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ─────────────────────────────────────────────────────────────────────────────
# Tables
# ─────────────────────────────────────────────────────────────────────────────
class OtherExpense(db.Model):
    __tablename__ = "other_expenses"

    id             = db.Column(db.Integer, primary_key=True)
    date           = db.Column(db.String(20), nullable=False)    # "YYYY-MM-DD" (as before)
    type           = db.Column(db.String(20), nullable=False)    # "Dr" | "Company" | "Other"
    party_name     = db.Column(db.String(200), nullable=False)
    amount         = db.Column(db.Float, nullable=False)
    description    = db.Column(db.Text, nullable=True, default="")
    excel_file     = db.Column(db.String(200), nullable=True)    # old column, no longer used
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    # added by this version (the table is upgraded by itself)
    category       = db.Column(db.String(60))
    payment_method = db.Column(db.String(30))
    bill_key       = db.Column(db.String(600))
    bill_name      = db.Column(db.String(200))
    bill_type      = db.Column(db.String(80))
    created_by     = db.Column(db.String(100))
    updated_at     = db.Column(db.DateTime)
    updated_by     = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id":             self.id,
            "date":           self.date,
            "type":           self.type,
            "party_name":     self.party_name,
            "amount":         float(self.amount or 0),
            "description":    self.description or "",
            "category":       self.category or _guess_category(self),
            "payment_method": self.payment_method or "",
            "has_bill":       bool(self.bill_key),
            "bill_name":      self.bill_name or "",
            "bill_type":      self.bill_type or "",
            "created_at":     _ist_text(self.created_at),
            "created_by":     self.created_by or "",
            "updated_at":     _ist_text(self.updated_at),
            "updated_by":     self.updated_by or "",
        }


class OtherExpenseDeletion(db.Model):
    """Deletion log: a full copy of every deleted expense, with why, who and when."""
    __tablename__ = "other_expense_deletions"

    id           = db.Column(db.Integer, primary_key=True)
    expense_id   = db.Column(db.Integer, index=True)
    date         = db.Column(db.String(20))
    category     = db.Column(db.String(60))
    party_name   = db.Column(db.String(200))
    amount       = db.Column(db.Float)
    expense_json = db.Column(db.Text)
    bill_key     = db.Column(db.String(600))
    bill_type    = db.Column(db.String(80))
    reason       = db.Column(db.String(500), nullable=False)
    deleted_by   = db.Column(db.String(100))
    deleted_at   = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        try:
            copy = json.loads(self.expense_json or "{}")
        except Exception:
            copy = {}
        return {
            "id": self.id, "expense_id": self.expense_id, "date": self.date, "category": self.category or "",
            "party_name": self.party_name or "", "amount": float(self.amount or 0), "reason": self.reason,
            "deleted_by": self.deleted_by or "", "deleted_display": _ist_text(self.deleted_at, "%d-%m-%Y %I:%M %p"),
            "has_bill": bool(self.bill_key), "expense": copy,
        }


def _ist_text(value, fmt="%Y-%m-%dT%H:%M:%S"):
    return (value + _IST).strftime(fmt) if value else None


def _guess_category(e):
    """Expenses saved before categories existed."""
    return "Doctor fee" if (e.type or "") == "Dr" else "Other"


# ─────────────────────────────────────────────────────────────────────────────
# Upgrading the table (also done by itself on first use)
# ─────────────────────────────────────────────────────────────────────────────
_NEW_COLUMNS = {
    "category": "VARCHAR(60)", "payment_method": "VARCHAR(30)", "bill_key": "VARCHAR(600)",
    "bill_name": "VARCHAR(200)", "bill_type": "VARCHAR(80)", "created_by": "VARCHAR(100)",
    "updated_at": "TIMESTAMP", "updated_by": "VARCHAR(100)",
}
_ready = False


def _upgrade():
    global _ready
    if _ready:
        return
    OtherExpense.__table__.create(bind=db.engine, checkfirst=True)
    OtherExpenseDeletion.__table__.create(bind=db.engine, checkfirst=True)
    from sqlalchemy import inspect as _inspect
    have = {c["name"] for c in _inspect(db.engine).get_columns("other_expenses")}
    with db.engine.begin() as conn:
        for name, kind in _NEW_COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE other_expenses ADD COLUMN {name} {kind}"))
        if "category" not in have:          # earlier expenses get a category
            conn.execute(text("UPDATE other_expenses SET category = 'Doctor fee' WHERE category IS NULL AND type = 'Dr'"))
            conn.execute(text("UPDATE other_expenses SET category = 'Other' WHERE category IS NULL"))
    _ready = True


def run_other_expense_migrations(app):
    """Called from app.py at start-up. Safe to call any number of times."""
    with app.app_context():
        try:
            _upgrade()
        except Exception as exc:
            print(f"[other-expenses] table upgrade failed: {exc!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────────
class _Refuse(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            _upgrade()
            return fn(*args, **kwargs)
        except _Refuse as err:
            db.session.rollback()
            return jsonify({"error": err.message}), err.status
        except Exception as exc:
            db.session.rollback()
            if exc.__class__.__name__ == "_Refuse" and hasattr(exc, "message"):   # from billing_receipts.py
                return jsonify({"error": exc.message}), getattr(exc, "status", 400)
            print(f"[other-expenses] {fn.__name__} failed: {exc!r}")
            return jsonify({"error": "The server could not do this. Nothing was changed — please try again."}), 500
    return wrapper


def _billing():
    """billing_receipts.py, as visits.py loaded it (for the file storage)."""
    for name in ("routes.billing_receipts", "billing_receipts"):
        if name in sys.modules:
            return sys.modules[name]
    for name in ("routes.billing_receipts", "billing_receipts"):
        try:
            __import__(name)
            return sys.modules[name]
        except ImportError:
            continue
    return None


def _who():
    b = _billing()
    if b is not None:
        try:
            return b._who() or ""
        except Exception:
            return ""
    return ""


def _text(value, limit):
    return str(value if value is not None else "").strip()[:limit]


def _day(value, required=True):
    raw = _text(value, 20)
    if not raw:
        if required:
            raise _Refuse("Please enter the date.")
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        raise _Refuse("Please enter the date as YYYY-MM-DD.")


def _today():
    return (datetime.utcnow() + _IST).date()


def month_label(day):
    return f"{_MONTHS[day.month - 1]}{day.year}"


def financial_year(day):
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{start + 1}"


def month_folder(day):
    return f"receipts/Financial year {financial_year(day)}/{month_label(day)}/other expenses"


def month_excel_key(day):
    return f"{month_folder(day)}/Other Exp {month_label(day)}.xlsx"


def _safe_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9 ._-]+", "", str(value or "")).strip()
    return re.sub(r"\s+", " ", cleaned)[:60] or "bill"


def _clean(data, current=None):
    if not isinstance(data, dict):
        raise _Refuse("The expense could not be read. Please try again.")
    pick = lambda key, default="": data.get(key) if key in data else (getattr(current, key) if current is not None else default)

    day = _day(pick("date"))
    if day > _today() + timedelta(days=1):
        raise _Refuse("The date is in the future. Please check it.")
    kind = _text(pick("type", "Other"), 20) or "Other"
    if kind not in PAID_TO_TYPES:
        kind = "Other"
    name = _text(pick("party_name"), 200)
    if not name:
        raise _Refuse("Please enter whom it was paid to.")
    raw_amount = pick("amount")
    try:
        amount = round(float(str(raw_amount).replace(",", "").strip()), 2)
    except (TypeError, ValueError):
        raise _Refuse("Please enter the amount as a number, e.g. 2500 or 2500.50.")
    if amount != amount or amount <= 0:
        raise _Refuse("The amount must be more than ₹0.")
    if amount > MAX_AMOUNT:
        raise _Refuse("The amount is too large. Please check it.")
    category = _text(pick("category"), 60) or ("Doctor fee" if kind == "Dr" else "Other")
    method = _text(pick("payment_method"), 30)
    return {
        "date": day.isoformat(), "type": kind, "party_name": name, "amount": amount,
        "description": _text(pick("description"), 5000), "category": category, "payment_method": method,
    }


def _find(expense_id):
    e = db.session.get(OtherExpense, expense_id)
    if e is None:
        raise _Refuse("This expense was not found. It may have been deleted.", 404)
    return e


# ─────────────────────────────────────────────────────────────────────────────
# Files: the month's Excel sheet
# ─────────────────────────────────────────────────────────────────────────────
def _files():
    """(store, None) or (None, why not)."""
    b = _billing()
    if b is None:
        return None, "billing_receipts.py is not in the routes folder, so expense files are not saved."
    if not b.files_enabled():
        return None, None                                  # switched off on purpose: nothing to report
    return b.files_store(), None


def _problem(key, exc):
    b = _billing()
    if b is not None:
        try:
            text_ = b._file_problem(key, exc)
            return text_.replace("The receipt itself is saved", "The expense itself is saved") \
                        .replace("Billing → 📊 Excel & files", "Other Expenses → 📊 Summary")
        except Exception:
            pass
    return f"{key} could not be saved ({exc.__class__.__name__}). The expense itself is saved."


def build_month_excel(day):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    first = day.replace(day=1)
    nxt = (first.replace(year=first.year + 1, month=1) if first.month == 12 else first.replace(month=first.month + 1))
    rows = (OtherExpense.query.filter(OtherExpense.date >= first.isoformat(), OtherExpense.date < nxt.isoformat())
            .order_by(OtherExpense.date.asc(), OtherExpense.id.asc()).all())

    head_fill = PatternFill("solid", start_color="1B3A5C", end_color="1B3A5C")
    head_font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    total_fill = PatternFill("solid", start_color="FFF3CD", end_color="FFF3CD")
    total_font = Font(name="Arial", bold=True, color="78350F", size=11)
    thin = Side(style="thin", color="D1D5DB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    data_font = Font(name="Arial", size=10)

    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses"
    columns = ["ID", "Date", "Category", "Paid To (Type)", "Name", "Paid by", "Amount (₹)", "Description"]
    widths = [7, 12, 20, 14, 28, 13, 14, 48]
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
    ws["A1"] = f"Other Expenses — {_MONTHS[day.month - 1]} {day.year}"
    ws["A1"].font = Font(name="Arial", bold=True, color="78350F", size=13)
    ws["A1"].fill = PatternFill("solid", start_color="FFF7ED", end_color="FFF7ED")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26
    for i, (title, width) in enumerate(zip(columns, widths), start=1):
        c = ws.cell(row=2, column=i, value=title)
        c.font, c.fill, c.border = head_font, head_fill, border
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A3"
    type_names = {"Dr": "Doctor", "Company": "Company", "Other": "Person"}
    r = 3
    for e in rows:
        values = [e.id, e.date, e.category or _guess_category(e), type_names.get(e.type, e.type), e.party_name,
                  e.payment_method or "", float(e.amount or 0), e.description or ""]
        for i, v in enumerate(values, start=1):
            c = ws.cell(row=r, column=i, value=v)
            c.font, c.border = data_font, border
            c.alignment = Alignment(vertical="top", wrap_text=(i == 8), horizontal="right" if i == 7 else None)
            if i == 7:
                c.number_format = "#,##0.00"
        r += 1
    ws.cell(row=r, column=1, value="TOTAL")
    ws.cell(row=r, column=7, value=f"=SUM(G3:G{r - 1})" if rows else 0)
    for i in range(1, len(columns) + 1):
        c = ws.cell(row=r, column=i)
        c.font, c.fill, c.border = total_font, total_fill, border
    ws.cell(row=r, column=7).number_format = "#,##0.00"
    ws.cell(row=r, column=7).alignment = Alignment(horizontal="right")

    cs = wb.create_sheet("By category")
    cs.append(["Category", "Expenses", "Amount (₹)"])
    for c in cs[1]:
        c.font, c.fill, c.border = head_font, head_fill, border
    totals = {}
    for e in rows:
        key = e.category or _guess_category(e)
        count, amount = totals.get(key, (0, 0.0))
        totals[key] = (count + 1, amount + float(e.amount or 0))
    for name, (count, amount) in sorted(totals.items(), key=lambda kv: -kv[1][1]):
        cs.append([name, count, round(amount, 2)])
    cs.append(["TOTAL", len(rows), round(sum(float(e.amount or 0) for e in rows), 2)])
    for c in cs[cs.max_row]:
        c.font, c.fill = total_font, total_fill
    for row in cs.iter_rows(min_row=2):
        row[2].number_format = "#,##0.00"
    cs.column_dimensions["A"].width = 26
    cs.column_dimensions["B"].width = 11
    cs.column_dimensions["C"].width = 16

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def save_month_files(days):
    """Write the Excel sheet of each month given. Returns {written, problems}."""
    report = {"written": [], "problems": []}
    store, why = _files()
    if store is None:
        if why:
            report["problems"].append(why)
        return report
    seen = set()
    for d in days:
        if d is None:
            continue
        first = d.replace(day=1)
        if first in seen:
            continue
        seen.add(first)
        key = month_excel_key(first)
        try:
            store.put(key, build_month_excel(first),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            report["written"].append(key)
        except ImportError:
            report["problems"].append("The server is missing the Excel tool. In the backend folder run:  pip install openpyxl")
        except Exception as exc:
            report["problems"].append(_problem(key, exc))
    return report


# ─────────────────────────────────────────────────────────────────────────────
# Addresses
# ─────────────────────────────────────────────────────────────────────────────
@other_expenses_bp.route("/other-expenses", methods=["GET"])
@require_login
@_guard
def list_expenses():
    query = OtherExpense.query
    start = _day(request.args.get("from"), required=False)
    end = _day(request.args.get("to"), required=False)
    if start:
        query = query.filter(OtherExpense.date >= start.isoformat())
    if end:
        query = query.filter(OtherExpense.date <= end.isoformat())
    category = _text(request.args.get("category"), 60)
    if category:
        query = query.filter(OtherExpense.category == category)
    q = _text(request.args.get("q"), 100)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(OtherExpense.party_name.ilike(like), OtherExpense.description.ilike(like),
                                 OtherExpense.category.ilike(like), OtherExpense.payment_method.ilike(like)))
    rows = query.order_by(OtherExpense.date.desc(), OtherExpense.id.desc()).all()
    return jsonify([r.to_dict() for r in rows]), 200


@other_expenses_bp.route("/other-expenses/meta", methods=["GET"])
@require_login
@_guard
def expenses_meta():
    used = (db.session.query(OtherExpense.party_name, OtherExpense.type, OtherExpense.category, func.max(OtherExpense.date))
            .group_by(OtherExpense.party_name, OtherExpense.type, OtherExpense.category)
            .order_by(func.max(OtherExpense.date).desc()).limit(300).all())
    parties, seen = [], set()
    for name, kind, category, last in used:
        if name and name.lower() not in seen:
            seen.add(name.lower())
            parties.append({"name": name, "type": kind, "category": category or "", "last": last})
    extra = sorted({c for (c,) in db.session.query(OtherExpense.category).distinct() if c and c not in CATEGORIES})
    store, why = _files()
    return jsonify({
        "categories": CATEGORIES + extra, "payment_methods": PAYMENT_METHODS, "parties": parties,
        "today": _today().isoformat(),
        "files": {"enabled": store is not None, "where": store.where() if store is not None else "", "problem": why or "",
                  "example": month_excel_key(_today())},
    }), 200


@other_expenses_bp.route("/other-expenses", methods=["POST"])
@require_login
@_guard
def create_expense():
    fields = _clean(request.get_json(force=True, silent=True) or {})
    who = _who()
    e = OtherExpense(created_by=who, updated_by=who, created_at=datetime.utcnow(), **fields)
    db.session.add(e)
    db.session.commit()
    files = save_month_files([_day(e.date)])
    return jsonify({**e.to_dict(), "files": files}), 201


@other_expenses_bp.route("/other-expenses/<int:expense_id>", methods=["PUT"])
@require_login
@_guard
def update_expense(expense_id):
    e = _find(expense_id)
    old_day = _day(e.date)
    fields = _clean(request.get_json(force=True, silent=True) or {}, current=e)
    for key, value in fields.items():
        setattr(e, key, value)
    e.updated_at = datetime.utcnow()
    e.updated_by = _who()
    db.session.commit()
    files = save_month_files([old_day, _day(e.date)])
    return jsonify({**e.to_dict(), "files": files}), 200


@other_expenses_bp.route("/other-expenses/<int:expense_id>", methods=["DELETE"])
@require_login
@_guard
def delete_expense(expense_id):
    body = request.get_json(force=True, silent=True) or {}
    reason = _text((body.get("reason") if isinstance(body, dict) else None) or request.args.get("reason"), 500)
    if len(reason) < 3:
        raise _Refuse("Please write why this expense is being deleted. The reason is kept in the deletion log.")
    e = _find(expense_id)
    day = _day(e.date)
    copy = e.to_dict()
    db.session.add(OtherExpenseDeletion(
        expense_id=e.id, date=e.date, category=copy["category"], party_name=e.party_name, amount=e.amount,
        expense_json=json.dumps(copy, ensure_ascii=False, default=str), bill_key=e.bill_key, bill_type=e.bill_type,
        reason=reason, deleted_by=_who(), deleted_at=datetime.utcnow()))
    db.session.delete(e)
    db.session.commit()
    files = save_month_files([day])
    return jsonify({"status": "deleted", "id": expense_id, "reason": reason, "files": files}), 200


# ── summary, Excel, deletion log ─────────────────────────────────────────────
def _fy_range(fy):
    m = re.fullmatch(r"(\d{4})-(\d{4})", fy or "")
    if not m or int(m.group(2)) != int(m.group(1)) + 1:
        raise _Refuse("Please choose the financial year, e.g. 2026-2027.")
    start = int(m.group(1))
    return date(start, 4, 1), date(start + 1, 3, 31)


@other_expenses_bp.route("/other-expenses/summary", methods=["GET"])
@require_login
@_guard
def expenses_summary():
    fy = _text(request.args.get("fy"), 9) or financial_year(_today())
    start, end = _fy_range(fy)
    rows = OtherExpense.query.filter(OtherExpense.date >= start.isoformat(), OtherExpense.date <= end.isoformat()).all()
    months = []
    for i in range(12):
        y, mth = (start.year, 4 + i) if 4 + i <= 12 else (start.year + 1, 4 + i - 12)
        months.append({"value": f"{y}-{mth:02d}", "label": f"{_MONTHS[mth - 1]} {y}", "total": 0.0, "count": 0,
                       "by_category": {}, "excel_key": month_excel_key(date(y, mth, 1))})
    by_value = {m["value"]: m for m in months}
    categories = {}
    for e in rows:
        m = by_value.get(e.date[:7])
        if m is None:
            continue
        cat = e.category or _guess_category(e)
        amount = float(e.amount or 0)
        m["total"] += amount
        m["count"] += 1
        m["by_category"][cat] = round(m["by_category"].get(cat, 0.0) + amount, 2)
        c = categories.setdefault(cat, {"name": cat, "total": 0.0, "count": 0})
        c["total"] += amount
        c["count"] += 1
    for m in months:
        m["total"] = round(m["total"], 2)
    years = {financial_year(_today())}
    for (d,) in db.session.query(OtherExpense.date).distinct():
        try:
            years.add(financial_year(datetime.strptime(str(d)[:10], "%Y-%m-%d").date()))
        except (TypeError, ValueError):
            pass                                  # an odd date saved long ago: left out of the list
    years = sorted(years, reverse=True)
    return jsonify({
        "fy": fy, "years": years, "months": months,
        "categories": sorted(({**c, "total": round(c["total"], 2)} for c in categories.values()), key=lambda c: -c["total"]),
        "total": round(sum(float(e.amount or 0) for e in rows), 2), "count": len(rows),
        "with_bill": sum(1 for e in rows if e.bill_key),
    }), 200


@other_expenses_bp.route("/other-expenses/excel", methods=["GET"])
@require_login
@_guard
def expenses_excel():
    raw = _text(request.args.get("month"), 7)
    try:
        day = datetime.strptime(raw + "-01", "%Y-%m-%d").date()
    except ValueError:
        raise _Refuse("Please choose a month.")
    try:
        data = build_month_excel(day)
    except ImportError:
        raise _Refuse("The server is missing the Excel tool. In the backend folder run:  pip install openpyxl", 500)
    return send_file(io.BytesIO(data), as_attachment=True, download_name=f"Other Exp {month_label(day)}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@other_expenses_bp.route("/other-expenses/files/regenerate", methods=["POST"])
@require_login
@_guard
def expenses_regenerate():
    body = request.get_json(force=True, silent=True) or {}
    start, end = _fy_range(_text(body.get("fy"), 9))
    used = {d[:7] for (d,) in db.session.query(OtherExpense.date).filter(
        OtherExpense.date >= start.isoformat(), OtherExpense.date <= end.isoformat()).distinct() if d}
    days = [datetime.strptime(v + "-01", "%Y-%m-%d").date() for v in sorted(used)]
    report = save_month_files(days)
    return jsonify({**report, "months": len(days)}), 200


@other_expenses_bp.route("/other-expenses/deleted", methods=["GET"])
@require_login
@_guard
def expenses_deleted():
    query = OtherExpenseDeletion.query
    q = _text(request.args.get("q"), 100)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(OtherExpenseDeletion.party_name.ilike(like), OtherExpenseDeletion.reason.ilike(like),
                                 OtherExpenseDeletion.category.ilike(like), OtherExpenseDeletion.deleted_by.ilike(like)))
    rows = query.order_by(OtherExpenseDeletion.deleted_at.desc(), OtherExpenseDeletion.id.desc()).limit(500).all()
    return jsonify({"deleted": [d.to_dict() for d in rows], "count": len(rows),
                    "total_amount": round(sum(float(d.amount or 0) for d in rows), 2)}), 200




# ── the saved files, shown in the app (like Billing → Receipt Files) ────────
_FILE_TYPES = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def _valid_expense_key(key):
    """Only files in a month's "other expenses" folder."""
    key = str(key or "")
    parts = key.split("/")
    return (key.startswith("receipts/Financial year ") and len(parts) >= 5 and parts[3] == "other expenses"
            and "\\" not in key and "\x00" not in key and all(p not in ("", ".", "..") for p in parts) and len(key) < 600)


def _reading_store():
    store, why = _files()
    if store is None:
        b = _billing()
        if b is None:
            raise _Refuse(why or "The expense files cannot be read.")
        store = b.files_store()          # saving switched off, but what is there can still be read
    return store


@other_expenses_bp.route("/other-expenses/files/months", methods=["GET"])
@require_login
@_guard
def expense_files_months():
    months = set()
    for (d,) in db.session.query(OtherExpense.date).distinct():
        try:
            day = datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        months.add((day.year, day.month))
    years = {}
    for y, m in sorted(months, reverse=True):
        years.setdefault(financial_year(date(y, m, 1)), []).append(
            {"month": _MONTHS[m - 1], "label": f"{_MONTHS[m - 1]} {y}", "value": f"{y}-{m:02d}"})
    store, why = _files()
    return jsonify({
        "years": [{"fy": fy, "label": f"Financial year {fy}", "months": items} for fy, items in sorted(years.items(), reverse=True)],
        "where": store.where() if store is not None else "", "problem": why or "",
    }), 200


@other_expenses_bp.route("/other-expenses/files", methods=["GET"])
@require_login
@_guard
def expense_files_list():
    raw = _text(request.args.get("month"), 7)
    try:
        day = datetime.strptime(raw + "-01", "%Y-%m-%d").date()
    except ValueError:
        raise _Refuse("Please choose a month.")
    folder = month_folder(day)
    store = _reading_store()
    try:
        found = store.list(folder)
    except _Refuse:
        raise
    except Exception as exc:
        raise _Refuse(_problem(folder, exc), 502)
    excel = None
    for f in found:
        if f["key"] == month_excel_key(day):
            excel = {**f, "name": f["key"].rsplit("/", 1)[-1]}
    first = day.replace(day=1)
    nxt = (first.replace(year=first.year + 1, month=1) if first.month == 12 else first.replace(month=first.month + 1))
    count = OtherExpense.query.filter(OtherExpense.date >= first.isoformat(), OtherExpense.date < nxt.isoformat()).count()
    return jsonify({"folder": folder, "where": store.where(), "excel": excel, "excel_key": month_excel_key(day),
                    "expected_name": month_excel_key(day).rsplit("/", 1)[-1], "expenses": count}), 200


@other_expenses_bp.route("/other-expenses/files/sheet", methods=["GET"])
@require_login
@_guard
def expense_files_sheet():
    key = request.args.get("key") or ""
    if not _valid_expense_key(key) or not key.lower().endswith(".xlsx"):
        raise _Refuse("This is not one of the Other Expenses Excel sheets.", 400)
    store = _reading_store()
    try:
        data = store.get(key)
    except Exception as exc:
        raise _Refuse(_problem(key, exc), 502)
    if data is None:
        raise _Refuse("This sheet is not there. Press “Save Excel files again” to make it.", 404)
    try:
        from openpyxl import load_workbook
        book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheets = []
        for ws in book.worksheets:
            rows = [list(r) for r in ws.iter_rows(values_only=True)]
            sheets.append({"name": ws.title, "rows": rows})
        book.close()
    except ImportError:
        raise _Refuse("The server is missing the Excel tool. In the backend folder run:  pip install openpyxl", 500)
    except Exception:
        raise _Refuse("This Excel sheet could not be read. Press “Save Excel files again” to make it again.", 422)

    def cell(v):
        if v is None:
            return ""
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, (datetime, date)):
            return v.strftime("%Y-%m-%d")
        return str(v)

    out, total, count = [], 0.0, 0
    for sh in sheets:
        rows = [[cell(v) for v in r] for r in sh["rows"] if r is not None and any(v not in (None, "") for v in r)]
        title = ""
        if rows and len([v for v in rows[0] if v != ""]) == 1 and len(rows) > 1 and str(rows[0][0]).startswith("Other Expenses"):
            title = str(rows[0][0])
            rows = rows[1:]
        header = [str(h) for h in rows[0]] if rows else []
        body = rows[1:]
        footer = None
        if body and str(body[-1][0]).strip().upper() == "TOTAL":
            footer = body[-1]
            body = body[:-1]
        if sh["name"] == "Expenses" and "Amount (₹)" in header:
            i = header.index("Amount (₹)")
            total = round(sum(float(r[i]) for r in body if isinstance(r[i], (int, float))), 2)
            count = len(body)
            if footer is not None:
                footer = list(footer)
                footer[i] = total               # the sheet's =SUM formula, worked out here
        out.append({"name": sh["name"], "title": title, "columns": header, "rows": body, "footer": footer})
    return jsonify({"key": key, "name": key.rsplit("/", 1)[-1], "sheets": out, "count": count, "total_amount": total}), 200


@other_expenses_bp.route("/other-expenses/files/download", methods=["GET"])
@require_login
@_guard
def expense_files_download():
    key = request.args.get("key") or ""
    if not _valid_expense_key(key):
        raise _Refuse("This file is not one of the Other Expenses files.", 400)
    store = _reading_store()
    try:
        data = store.get(key)
    except Exception as exc:
        raise _Refuse(_problem(key, exc), 502)
    if data is None:
        raise _Refuse("This file is not there any more.", 404)
    name = key.rsplit("/", 1)[-1]
    inline = request.args.get("inline") in ("1", "true", "yes")
    return send_file(io.BytesIO(data), mimetype=_FILE_TYPES.get(os.path.splitext(name)[1].lower(), "application/octet-stream"),
                     as_attachment=not inline, download_name=name)