import os
from datetime import datetime


def get_financial_year(date: datetime) -> str:
    """
    Returns financial year string e.g. '2025-2026'
    Indian FY: April 1 to March 31
    """
    if date.month >= 4:
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"


def get_month_name(date: datetime) -> str:
    return date.strftime("%B")  # e.g. 'March', 'April'


def ensure_month_folders(base: str = "Receipts") -> tuple:
    """
    Creates and returns folder paths based on current date.

    Structure:
        Receipts/
          Financial year2025-2026/
            March/
              Pdf/
              Excel/
              Other Expenses/

    Returns:
        (month, pdf_dir, excel_dir, other_expenses_dir)
    """
    now = datetime.now()
    fy = get_financial_year(now)
    month = get_month_name(now)

    fy_folder     = os.path.join(base, f"Financial year{fy}")
    month_folder  = os.path.join(fy_folder, month)
    pdf_dir       = os.path.join(month_folder, "Pdf")
    excel_dir     = os.path.join(month_folder, "Excel")
    other_exp_dir = os.path.join(month_folder, "Other Expenses")

    for folder in [pdf_dir, excel_dir, other_exp_dir]:
        os.makedirs(folder, exist_ok=True)

    return month, pdf_dir, excel_dir, other_exp_dir


def get_excel_path(month: str, base: str = "Receipts") -> str:
    """
    Returns path to the monthly receipts Excel file.
    e.g. Receipts/Financial year2025-2026/March/Excel/March2026.xlsx
    """
    now = datetime.now()
    fy = get_financial_year(now)
    filename = f"{month}{now.year}.xlsx"

    return os.path.join(
        base,
        f"Financial year{fy}",
        month,
        "Excel",
        filename
    )


def get_other_expenses_excel_path(expense_date: str, base: str = "Receipts") -> str:
    """
    Returns path to the Other Expenses Excel file for a given date.
    e.g. Receipts/Financial year2025-2026/March/Other Expenses/Other Exp March 2026.xlsx

    expense_date: "YYYY-MM-DD"
    """
    d = datetime.strptime(expense_date, "%Y-%m-%d")
    fy = get_financial_year(d)
    month = get_month_name(d)
    filename = f"Other Exp {month} {d.year}.xlsx"

    folder = os.path.join(base, f"Financial year{fy}", month, "Other Expenses")
    os.makedirs(folder, exist_ok=True)

    return os.path.join(folder, filename)