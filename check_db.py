import psycopg2

conn = psycopg2.connect('postgresql://postgres:Admin123@localhost:5432/dental_clinic')
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = cur.fetchall()
print("TABLES:", tables)

conn.close()