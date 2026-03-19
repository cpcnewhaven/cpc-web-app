import psycopg2
import sys

conn_string = "postgresql://cpc_admin:Vi6LSZ2vOP3emQPV9HZLtkMnXxTMzvcj@dpg-d64bql24d50c73eaqle0-a.oregon-postgres.render.com/cpc_newhaven"

try:
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    # 1. Check table schema for announcements
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'announcements';
    """)
    columns = cursor.fetchall()
    print("Columns in 'announcements' table:")
    for col in columns:
        print(f" - {col[0]} ({col[1]})")

    print("\n----------------\n")
    
    # 2. Query the latest 5 announcements
    cursor.execute("""
        SELECT id, title, active, archived, date_entered, event_start_time, event_end_time, expires_at 
        FROM announcements 
        ORDER BY date_entered DESC 
        LIMIT 5;
    """)
    rows = cursor.fetchall()
    print("Latest 5 Announcements:")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print("Database connection or query failed:", e)
    sys.exit(1)
