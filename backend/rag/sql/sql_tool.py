from sqlalchemy import text
from backend.database import SessionLocal

def execute_sql_query(sql_query: str):
    """Safely executes an SQL query containing only SELECT statements."""
    if not sql_query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed for security reasons."}
        
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK"]
    upper_query = sql_query.upper()
    
    for kw in forbidden_keywords:
        # basic check, better parser needed for prod
        if f" {kw} " in f" {upper_query} ":
            return {"error": f"Keyword {kw} is not allowed."}
            
    db = SessionLocal()
    try:
        result = db.execute(text(sql_query))
        rows = result.fetchall()
        # Convert to list of dicts for safety and serialization
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        return data
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
