from database import db
from models import Receipt

def get_next_receipt_number():
    last = db.session.query(db.func.max(Receipt.receipt_number)).scalar()
    return 1 if last is None else last + 1
