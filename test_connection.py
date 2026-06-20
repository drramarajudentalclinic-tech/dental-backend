import psycopg2

try:
    print("STEP 1")

    conn = psycopg2.connect(
        "postgresql://dental_db_6ih0_user:Bl56Svd1gXsFzIUDr8uqN34DyWZYHRhS@dpg-d8lu55d8nd3s73a8lk1g-a.oregon-postgres.render.com/dental_db_6ih0",
        sslmode="require"
    )

    print("STEP 2 - CONNECTED")

    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())

    cur.close()
    conn.close()

except Exception as e:
    print("ERROR:")
    print(e)