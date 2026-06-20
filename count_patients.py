import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    os.getenv("DATABASE_URL"),
    sslmode="require"
)

cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM patients")
print("Patients:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM visits")
print("Visits:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM payments")
print("Payments:", cur.fetchone()[0])

cur.close()
conn.close()