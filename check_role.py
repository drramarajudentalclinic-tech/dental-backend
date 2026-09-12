import psycopg2
conn = psycopg2.connect("postgresql://postgres:Admin123@localhost:5432/dental_clinic")
cur = conn.cursor()
cur.execute("SELECT id, username, role FROM \"user\" WHERE id = %s", (3,))
print("ROW:", cur.fetchone())
cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = %s AND column_name = %s", ("user", "role"))
print("COLUMN INFO:", cur.fetchall())
conn.close()
