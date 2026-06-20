import psycopg2
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Connecting to database...")

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

cur.execute("""
TRUNCATE TABLE
receipts,
payments,
other_expenses,
appointments,
cbct_annotations,
cbct_slices,
cbct_volumes,
cbct_files,
images,
prescriptions,
consultations,
other_findings,
dental_chart,
visits,
woman_history,
habits,
allergy_records,
medical_history,
consents,
family_doctors,
patients
RESTART IDENTITY CASCADE;
""")

conn.commit()

print("✅ All patient data deleted successfully.")

cur.close()
conn.close()