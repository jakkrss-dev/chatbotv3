import sys
import os
from sqlalchemy import create_engine, text

def init_supabase(db_url):
    sql_file = os.path.join(os.path.dirname(__file__), "..", "..", "infra", "init_pgvector.sql")
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    print(f"Connecting to Supabase...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("Reading schema from infra/init_pgvector.sql...")
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_commands = f.read().split(";")
            
            print("Executing commands...")
            for cmd in sql_commands:
                if cmd.strip():
                    conn.execute(text(cmd.strip() + ";"))
            conn.commit()
            print("Supabase database initialized successfully with schema and seed data!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/init_supabase.py <SUPABASE_DB_URL>")
        sys.exit(1)
    init_supabase(sys.argv[1])
