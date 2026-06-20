import psycopg2

conn = psycopg2.connect(
    "postgresql://dental_db_6ih0_user:Bl56Svd1gXsFzIUDr8uqN34DyWZYHRhS@dpg-d8lu55d8nd3s73a8lk1g-a.oregon-postgres.render.com/dental_db_6ih0",
    sslmode="require"
)

cur = conn.cursor()

cur.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
ORDER BY table_name;
""")

for row in cur.fetchall():
    print(row[0])

cur.close()
conn.close()