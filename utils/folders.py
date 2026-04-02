import os
from datetime import datetime

BASE_UPLOAD_DIR = "uploads/visits"
BASE_RECEIPTS_DIR = "receipts"


def ensure_month_folders():
    """
    Creates:
      receipts/
        march/
          pdf/
          excel/
          other_expenses/

    Returns: (month_label, pdf_dir, excel_dir, other_expenses_dir)
    e.g.     ("march",
               "receipts/march/pdf",
               "receipts/march/excel",
               "receipts/march/other_expenses")
    """
    month = datetime.now().strftime("%B").lower()    # e.g. "march"

    base             = os.path.join(BASE_RECEIPTS_DIR, month)
    pdf_dir          = os.path.join(base, "pdf")
    excel_dir        = os.path.join(base, "excel")
    other_exp_dir    = os.path.join(base, "other_expenses")

    os.makedirs(pdf_dir,       exist_ok=True)
    os.makedirs(excel_dir,     exist_ok=True)
    os.makedirs(other_exp_dir, exist_ok=True)

    return month, pdf_dir, excel_dir, other_exp_dir


def get_excel_path(month: str) -> str:
    """Returns path to the main receipts Excel file for the given month.
    e.g. receipts/march/excel/march.xlsx
    """
    return os.path.join(BASE_RECEIPTS_DIR, month, "excel", f"{month}.xlsx")


def get_other_expenses_path(month: str) -> str:
    """Returns path to the other expenses Excel file for the given month.
    e.g. receipts/march/other_expenses/march_other_expenses.xlsx
    """
    return os.path.join(BASE_RECEIPTS_DIR, month, "other_expenses",
                        f"{month}_other_expenses.xlsx")


def get_pdf_path(month: str, patient_name: str, receipt_number) -> str:
    """Returns the full PDF path for a receipt.
    e.g. receipts/march/pdf/Ravi.0001.pdf
    Receipt number is zero-padded to 4 digits.
    """
    safe_name    = patient_name.replace(" ", "")
    padded_no    = str(receipt_number).zfill(4)
    pdf_filename = f"{safe_name}.{padded_no}.pdf"
    return os.path.join(BASE_RECEIPTS_DIR, month, "pdf", pdf_filename)


def ensure_image_folder(visit_id, image_type):
    """
    Creates:
      uploads/visits/<visit_id>/xray
      uploads/visits/<visit_id>/intraoral
    """
    folder = os.path.join(BASE_UPLOAD_DIR, str(visit_id), image_type.lower())
    os.makedirs(folder, exist_ok=True)
    return folder