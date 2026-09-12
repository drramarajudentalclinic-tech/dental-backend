"""
Final patient billing ledger.

Design:
    PatientAccount -> BillingCharge -> PaymentAllocation -> Payment

This module does NOT replace the legacy /api/payments endpoints. It adds the
new account/charge/allocation layer so existing receipts and payment history
remain available while the frontend moves to the new workflow.
"""

import json
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request
from sqlalchemy import inspect

from database import db
from models import Patient, Visit, Payment, PatientAccount, BillingCharge, PaymentAllocation

billing_ledger_bp = Blueprint("billing_ledger", __name__)

MONEY = Decimal("0.01")


def money(value):
    try:
        return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception:
        raise ValueError("Invalid monetary amount")


def dec(value):
    return float(money(value))


def get_or_create_account(patient_id):
    account = PatientAccount.query.filter_by(patient_id=patient_id).first()
    if not account:
        account = PatientAccount(patient_id=patient_id)
        db.session.add(account)
        db.session.flush()
    return account


def allocated_for_charge(charge_id):
    total = db.session.query(db.func.coalesce(db.func.sum(PaymentAllocation.amount), 0)).filter(
        PaymentAllocation.charge_id == charge_id,
        PaymentAllocation.allocation_type == "CHARGE",
        PaymentAllocation.payment.has(Payment.id.isnot(None)),
    ).scalar()
    return money(total)


def charge_balance(charge):
    paid = db.session.query(db.func.coalesce(db.func.sum(PaymentAllocation.amount), 0)).filter(
        PaymentAllocation.charge_id == charge.id,
        PaymentAllocation.allocation_type == "CHARGE",
        PaymentAllocation.payment.has(Payment.ledger_status == "ACTIVE"),
    ).scalar()
    return max(money(charge.net_amount) - money(paid), Decimal("0.00"))


def charge_outstanding(charge_or_id):
    """Backward-compatible outstanding-balance helper used by payments.py.

    Accepts either a BillingCharge object or a charge ID. Always returns a
    Decimal amount so callers can safely perform monetary calculations.
    """
    if isinstance(charge_or_id, BillingCharge):
        charge = charge_or_id
    else:
        charge = BillingCharge.query.get(int(charge_or_id))
        if not charge:
            return Decimal("0.00")
    return charge_balance(charge)


def account_summary(account):
    charges = []
    total_charged = Decimal("0.00")
    total_paid = Decimal("0.00")

    active_charges = BillingCharge.query.filter_by(account_id=account.id, status="ACTIVE").order_by(
        BillingCharge.charge_date.asc(), BillingCharge.id.asc()
    ).all()

    for charge in active_charges:
        paid = money(db.session.query(db.func.coalesce(db.func.sum(PaymentAllocation.amount), 0)).filter(
            PaymentAllocation.charge_id == charge.id,
            PaymentAllocation.allocation_type == "CHARGE",
            PaymentAllocation.payment.has(Payment.ledger_status == "ACTIVE"),
        ).scalar())
        due = max(money(charge.net_amount) - paid, Decimal("0.00"))
        total_charged += money(charge.net_amount)
        total_paid += min(paid, money(charge.net_amount))
        charges.append({
            "id": charge.id,
            "visit_id": charge.visit_id,
            "description": charge.description,
            "treatment_code": charge.treatment_code,
            "gross_amount": dec(charge.gross_amount),
            "discount": dec(charge.discount),
            "net_amount": dec(charge.net_amount),
            "paid_amount": dec(paid),
            "balance_due": dec(due),
            "status": charge.status,
            "charge_date": charge.charge_date.isoformat() if charge.charge_date else None,
            "notes": charge.notes or "",
        })

    payments = Payment.query.filter_by(account_id=account.id, ledger_status="ACTIVE").order_by(Payment.payment_date.desc(), Payment.id.desc()).all()
    payment_rows = []
    for p in payments:
        allocations = PaymentAllocation.query.filter_by(payment_id=p.id).order_by(PaymentAllocation.id.asc()).all()
        allocated = sum((money(a.amount) for a in allocations), Decimal("0.00"))
        payment_rows.append({
            "id": p.id,
            "receipt_number": p.receipt_number,
            "visit_id": p.visit_id,
            "paid_amount": dec(p.paid_amount),
            "payment_method": p.payment_method or "",
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "treatment_description": p.treatment_description or "",
            "allocated_amount": dec(allocated),
            "credit_amount": dec(max(money(p.paid_amount) - allocated, Decimal("0.00"))),
            "allocations": [
                {"charge_id": a.charge_id, "amount": dec(a.amount), "allocation_type": a.allocation_type}
                for a in allocations
            ],
        })

    outstanding = max(total_charged - total_paid, Decimal("0.00"))
    credit = money(account.credit_balance)
    net_due = max(outstanding - credit, Decimal("0.00"))

    return {
        "account_id": account.id,
        "patient_id": account.patient_id,
        "status": account.status,
        "total_charged": dec(total_charged),
        "total_paid": dec(total_paid),
        "outstanding": dec(outstanding),
        "credit_balance": dec(credit),
        "net_due": dec(net_due),
        "charges": charges,
        "payments": payment_rows,
    }


def validate_patient_visit(patient_id, visit_id):
    if visit_id is None:
        return None
    visit = Visit.query.get(visit_id)
    if not visit:
        raise ValueError("Visit not found")
    if visit.patient_id != patient_id:
        raise ValueError("Visit does not belong to this patient")
    return visit


def auto_allocate(account, amount):
    """Oldest outstanding charge first. Returns [(charge, amount), ...]."""
    remaining = money(amount)
    allocations = []
    charges = BillingCharge.query.filter_by(account_id=account.id, status="ACTIVE").order_by(
        BillingCharge.charge_date.asc(), BillingCharge.id.asc()
    ).with_for_update().all()

    for charge in charges:
        if remaining <= 0:
            break
        due = charge_balance(charge)
        if due <= 0:
            continue
        take = min(remaining, due)
        allocations.append((charge, take))
        remaining -= take

    return allocations, remaining


def manual_allocate(account, requested):
    allocations = []
    requested_total = Decimal("0.00")
    for item in requested:
        charge_id = item.get("charge_id")
        amount = money(item.get("amount"))
        if not charge_id or amount <= 0:
            continue
        charge = BillingCharge.query.filter_by(id=int(charge_id), account_id=account.id, status="ACTIVE").with_for_update().first()
        if not charge:
            raise ValueError(f"Charge {charge_id} not found for this patient")
        due = charge_balance(charge)
        if amount > due:
            raise ValueError(f"Allocation for charge {charge_id} exceeds its outstanding balance ({dec(due)})")
        allocations.append((charge, amount))
        requested_total += amount
    return allocations, requested_total


def create_receipt_and_excel(payment, visit_id=None):
    """Reuse the existing receipt/Excel engine so current documents continue to work."""
    try:
        from routes.payments import _save_receipt_pdf, _append_excel_row, _visit_data, _parse_treatments
        treatments = _parse_treatments(payment)
        vdata = _visit_data(visit_id)
        payment.receipt_path = _save_receipt_pdf(payment, treatments, vdata)
        db.session.flush()
        _append_excel_row(payment, vdata, treatments)
    except Exception as exc:
        # Ledger/payment transaction should not be rolled back only because a
        # document writer failed. The API reports the warning to the caller.
        print(f"[billing_ledger] receipt/Excel warning: {exc}")
        return str(exc)
    return None


@billing_ledger_bp.route("/billing/accounts/<int:patient_id>", methods=["GET"])
def get_account(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    account = get_or_create_account(patient.id)
    db.session.commit()
    result = account_summary(account)
    result["patient"] = {
        "id": patient.id,
        "name": patient.name,
        "case_number": patient.case_number,
        "mobile": patient.mobile,
    }
    return jsonify(result)


@billing_ledger_bp.route("/billing/accounts/by-case/<case_number>", methods=["GET"])
def get_account_by_case(case_number):
    patient = Patient.query.filter_by(case_number=case_number).first_or_404()
    return get_account(patient.id)


@billing_ledger_bp.route("/billing/charges", methods=["POST"])
def create_charge():
    data = request.get_json(force=True) or {}
    try:
        patient_id = int(data["patient_id"])
        patient = Patient.query.get(patient_id)
        if not patient:
            raise ValueError("Patient not found")
        visit_id = data.get("visit_id")
        if visit_id is not None:
            visit_id = int(visit_id)
        validate_patient_visit(patient_id, visit_id)

        gross = money(data.get("gross_amount", data.get("amount", 0)))
        discount = money(data.get("discount", 0))
        if gross < 0 or discount < 0 or discount > gross:
            raise ValueError("Invalid charge/discount amount")
        net = gross - discount
        if not data.get("description"):
            raise ValueError("Charge description is required")

        account = get_or_create_account(patient_id)
        charge_date = date.today()
        if data.get("charge_date"):
            charge_date = datetime.strptime(data["charge_date"], "%Y-%m-%d").date()

        charge = BillingCharge(
            account_id=account.id,
            patient_id=patient_id,
            visit_id=visit_id,
            description=str(data["description"]).strip(),
            treatment_code=data.get("treatment_code"),
            gross_amount=gross,
            discount=discount,
            net_amount=net,
            charge_date=charge_date,
            notes=data.get("notes"),
        )
        db.session.add(charge)
        db.session.commit()
        return jsonify({"charge": {"id": charge.id, "net_amount": dec(charge.net_amount)}, "account": account_summary(account)}), 201
    except (KeyError, ValueError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "Could not create charge", "details": str(exc)}), 500


@billing_ledger_bp.route("/billing/charges/<int:charge_id>/void", methods=["POST"])
def void_charge(charge_id):
    charge = BillingCharge.query.get_or_404(charge_id)
    if charge.status != "ACTIVE":
        return jsonify({"error": "Charge is already inactive"}), 400
    if charge_balance(charge) != money(charge.net_amount):
        return jsonify({"error": "A charge with payments allocated to it cannot be voided. Reverse the payment first."}), 409
    charge.status = "VOID"
    db.session.commit()
    return jsonify({"message": "Charge voided", "charge_id": charge.id})


@billing_ledger_bp.route("/billing/collect", methods=["POST"])
def collect_payment():
    data = request.get_json(force=True) or {}
    try:
        patient_id = int(data["patient_id"])
        patient = Patient.query.get(patient_id)
        if not patient:
            raise ValueError("Patient not found")
        visit_id = data.get("visit_id")
        if visit_id is not None:
            visit_id = int(visit_id)
        validate_patient_visit(patient_id, visit_id)

        amount = money(data.get("amount", data.get("paid_amount", 0)))
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        receipt_date = date.today()
        if data.get("payment_date"):
            receipt_date = datetime.strptime(data["payment_date"], "%Y-%m-%d").date()

        account = get_or_create_account(patient_id)

        # New treatments can be created in the same transaction as the
        # payment. This prevents a half-saved billing operation where the
        # charge exists but the payment failed.
        new_charges = data.get("new_charges") or []
        created_charges = []
        for item in new_charges:
            description = str(item.get("description") or "").strip()
            if not description:
                raise ValueError("Every new treatment must have a description")
            gross = money(item.get("gross_amount", item.get("amount", 0)))
            discount = money(item.get("discount", 0))
            if gross <= 0 or discount < 0 or discount > gross:
                raise ValueError(f"Invalid amount for new treatment: {description}")
            charge = BillingCharge(
                account_id=account.id,
                patient_id=patient_id,
                visit_id=visit_id,
                description=description,
                treatment_code=item.get("treatment_code"),
                gross_amount=gross,
                discount=discount,
                net_amount=gross - discount,
                charge_date=receipt_date if 'receipt_date' in locals() else date.today(),
                notes=item.get("notes"),
            )
            db.session.add(charge)
            db.session.flush()
            created_charges.append(charge)

        explicit = data.get("allocations")
        if explicit:
            allocations, allocated_total = manual_allocate(account, explicit)
            if allocated_total > amount:
                raise ValueError("Allocation total cannot exceed payment amount")
            remaining_for_auto = amount - allocated_total
            if remaining_for_auto > 0 and data.get("auto_allocate_remaining", True):
                extra, leftover = auto_allocate(account, remaining_for_auto)
                allocations.extend(extra)
                remaining_for_auto = leftover
        else:
            allocations, remaining_for_auto = auto_allocate(account, amount)

        allow_credit = bool(data.get("allow_credit", False))
        if remaining_for_auto > 0 and not allow_credit:
            outstanding = account_summary(account)["net_due"]
            raise ValueError(
                f"Payment exceeds current outstanding balance. Current due is {outstanding}. "
                "Use allow_credit=true for an advance payment."
            )

        receipt_date = date.today()
        if data.get("payment_date"):
            receipt_date = datetime.strptime(data["payment_date"], "%Y-%m-%d").date()

        # Preserve the existing Payment table so existing receipt/history code works.
        receipt_no = None
        try:
            from routes.payments import _next_receipt_number
            receipt_no = _next_receipt_number()
        except Exception:
            receipt_no = None

        description = data.get("treatment_description") or ", ".join(c.description for c, _ in allocations)
        payment = Payment(
            visit_id=visit_id,
            account_id=account.id,
            ledger_status="ACTIVE",
            patient_name=patient.name,
            case_number=patient.case_number,
            mobile=patient.mobile,
            treatment_description=description[:5000],
            fee=sum((money(c.net_amount) for c, _ in allocations), Decimal("0.00")),
            discount=0,
            paid_amount=amount,
            balance=max(money(account_summary(account)["net_due"]) - amount, Decimal("0.00")),
            payment_method=data.get("payment_method", "Cash"),
            receipt_number=receipt_no,
            payment_date=receipt_date,
        )
        db.session.add(payment)
        db.session.flush()

        for charge, allocation_amount in allocations:
            db.session.add(PaymentAllocation(
                payment_id=payment.id,
                charge_id=charge.id,
                allocation_type="CHARGE",
                amount=allocation_amount,
            ))

        if remaining_for_auto > 0:
            account.credit_balance = money(account.credit_balance) + remaining_for_auto
            db.session.add(PaymentAllocation(
                payment_id=payment.id,
                charge_id=None,
                allocation_type="CREDIT",
                amount=remaining_for_auto,
            ))

        db.session.flush()
        warning = create_receipt_and_excel(payment, visit_id)
        db.session.commit()

        summary = account_summary(account)

        # Structured line items for the receipt's treatments table — one
        # row per charge this payment was allocated against, with the
        # amount actually applied to that charge (not its full price, so
        # partial payments show correctly on the receipt).
        treatments_list = [
            {"description": c.description, "amount": float(dec(a))}
            for c, a in allocations
        ]

        return jsonify({
            "message": "Payment collected successfully",
            "payment": {
                "id": payment.id,
                "receipt_number": payment.receipt_number,
                "amount": dec(payment.paid_amount),
                "paid_amount": dec(payment.paid_amount),
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                "patient_name": payment.patient_name,
                "case_number": payment.case_number,
                "mobile": payment.mobile,
                "fee": dec(payment.fee),
                "balance": dec(payment.balance),
                "is_partial": money(payment.balance) > 0,
                "is_fully_paid": money(payment.balance) <= 0,
                "treatment_description": json.dumps(treatments_list),
            },
            "allocations": [
                {"charge_id": c.id, "description": c.description, "amount": dec(a)}
                for c, a in allocations
            ],
            "credit_added": dec(remaining_for_auto),
            "account": summary,
            "document_warning": warning,
        }), 201

    except (KeyError, ValueError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "Could not collect payment", "details": str(exc)}), 500


@billing_ledger_bp.route("/billing/payments/<int:payment_id>/void", methods=["POST"])
def void_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    if not payment.account_id:
        return jsonify({"error": "This is a legacy payment. Use the existing payment history workflow."}), 409
    if payment.ledger_status != "ACTIVE":
        return jsonify({"error": "Payment is already voided"}), 409

    account = PatientAccount.query.get(payment.account_id)
    allocations = PaymentAllocation.query.filter_by(payment_id=payment.id).all()
    for allocation in allocations:
        if allocation.allocation_type == "CREDIT":
            account.credit_balance = max(money(account.credit_balance) - money(allocation.amount), Decimal("0.00"))

    payment.ledger_status = "VOID"
    # Cancel the associated receipt without deleting the financial history.
    for receipt in payment.receipts:
        receipt.status = "CANCELLED"
    db.session.commit()
    return jsonify({"message": "Payment voided", "payment_id": payment.id, "account": account_summary(account)})


@billing_ledger_bp.route("/billing/payments/<int:payment_id>", methods=["GET"])
def get_ledger_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    allocations = PaymentAllocation.query.filter_by(payment_id=payment.id).all()
    return jsonify({
        "id": payment.id,
        "receipt_number": payment.receipt_number,
        "patient_name": payment.patient_name,
        "amount": dec(payment.paid_amount),
        "payment_method": payment.payment_method,
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "allocations": [
            {"charge_id": a.charge_id, "amount": dec(a.amount), "allocation_type": a.allocation_type}
            for a in allocations
        ],
    })


def run_billing_ledger_migrations():
    """Safe startup migration for the new ledger tables and Payment.account_id."""
    try:
        # Models are already imported before app startup, so create_all creates
        # only the new missing tables and never drops existing tables.
        db.create_all()

        inspector = inspect(db.engine)
        payment_columns = {c["name"] for c in inspector.get_columns("payments")}
        with db.engine.begin() as conn:
            if "account_id" not in payment_columns:
                conn.execute(db.text(
                    'ALTER TABLE payments ADD COLUMN account_id INTEGER NULL '
                    'REFERENCES patient_accounts(id)'
                ))
            if "ledger_status" not in payment_columns:
                conn.execute(db.text(
                    "ALTER TABLE payments ADD COLUMN ledger_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"
                ))
        print("Billing ledger migration completed")
    except Exception as exc:
        print(f"Billing ledger migration failed: {exc}")


def backfill_legacy_visit_charges():
    """Create one legacy charge per patient/visit without changing old payments.

    The legacy charge uses the maximum net fee recorded for that visit and the
    old Payment rows are allocated chronologically up to that amount. This is
    intentionally conservative: it does not invent charges for visits where
    the old records do not contain enough information.
    """
    try:
        visits = Visit.query.filter(Visit.patient_id.isnot(None)).all()
        created = 0
        for visit in visits:
            if BillingCharge.query.filter_by(visit_id=visit.id, treatment_code="LEGACY").first():
                continue
            payments = Payment.query.filter_by(visit_id=visit.id).order_by(Payment.created_at.asc(), Payment.id.asc()).all()
            if not payments:
                continue
            net_fee = max((money((p.fee or 0) - (p.discount or 0)) for p in payments), default=Decimal("0.00"))
            if net_fee <= 0:
                continue
            patient = Patient.query.get(visit.patient_id)
            if not patient:
                continue
            account = get_or_create_account(patient.id)
            description = next((p.treatment_description for p in payments if p.treatment_description), None) or "Legacy treatment balance"
            charge = BillingCharge(
                account_id=account.id,
                patient_id=patient.id,
                visit_id=visit.id,
                description=description,
                treatment_code="LEGACY",
                gross_amount=net_fee,
                discount=0,
                net_amount=net_fee,
                charge_date=(visit.visit_date.date() if visit.visit_date else date.today()),
                notes="Imported from legacy visit payment records; original payments preserved.",
            )
            db.session.add(charge)
            db.session.flush()
            remaining = net_fee
            for p in payments:
                if remaining <= 0:
                    break
                take = min(remaining, money(p.paid_amount))
                if take > 0:
                    db.session.add(PaymentAllocation(payment_id=p.id, charge_id=charge.id, allocation_type="CHARGE", amount=take))
                    if not p.account_id:
                        p.account_id = account.id
                    remaining -= take
            created += 1
        db.session.commit()
        print(f"Legacy billing backfill completed: {created} charges")
    except Exception as exc:
        db.session.rollback()
        print(f"Legacy billing backfill skipped: {exc}")


# ---------------------------------------------------------------------------
# Backward-compatible API expected by the existing routes/payments.py
# ---------------------------------------------------------------------------
def ensure_billing_ledger(app=None):
    """Compatibility wrapper for the existing payments.py startup hook."""
    run_billing_ledger_migrations()


def migrate_legacy_payments():
    """Compatibility wrapper for the existing payments.py migration hook."""
    backfill_legacy_visit_charges()