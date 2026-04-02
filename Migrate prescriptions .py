"""
migrate_prescriptions.py
────────────────────────
Run this ONCE from your backend folder to add the new columns
to the existing prescriptions table.

Usage:
    cd E:\\backend
    python migrate_prescriptions.py

Safe to run multiple times — it skips columns that already exist.
"""

import sqlite3
import os

# ── Adjust this path to your actual .db file ──────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")
# If your db file has a different name, change it above.
# Common names: clinic.db, app.db, dental.db, database.db
# ──────────────────────────────────────────────────────────────

NEW_COLUMNS = [
    # (column_name,        sql_type,          default_value)
    ("patient_name",         "VARCHAR(150)",    None),
    ("patient_age",          "VARCHAR(20)",     None),
    ("patient_gender",       "VARCHAR(10)",     None),
    ("case_number",          "VARCHAR(50)",     None),
    ("date",                 "VARCHAR(20)",     None),
    ("diagnosis",            "TEXT",            None),
    ("advice",               "TEXT",            None),
    ("treatment_done_today", "TEXT",            None),
    ("medicines",            "TEXT",            "'[]'"),
    ("follow_up_date",       "VARCHAR(30)",     None),
    ("status",               "VARCHAR(20)",     "'confirmed'"),
]


def get_existing_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at: {DB_PATH}")
        print("Please update DB_PATH in this script to point to your .db file.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    existing = get_existing_columns(cur, "prescriptions")
    print(f"Existing columns: {sorted(existing)}\n")

    added = []
    skipped = []

    for col_name, col_type, default in NEW_COLUMNS:
        if col_name in existing:
            skipped.append(col_name)
            continue

        if default:
            sql = f"ALTER TABLE prescriptions ADD COLUMN {col_name} {col_type} DEFAULT {default}"
        else:
            sql = f"ALTER TABLE prescriptions ADD COLUMN {col_name} {col_type}"

        cur.execute(sql)
        added.append(col_name)
        print(f"  ✔ Added column: {col_name} ({col_type})")

    conn.commit()
    conn.close()

    print(f"\n{'─'*50}")
    print(f"Added   : {len(added)} columns  → {added}")
    print(f"Skipped : {len(skipped)} already existed → {skipped}")
    print(f"\nMigration complete. Restart your Flask server.")


if __name__ == "__main__":
    migrate()