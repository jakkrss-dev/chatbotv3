import os
import sys

# Add root directory to sys.path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.append(root)

try:
    from backend.main import app
except Exception as e:
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def crash(path: str):
        return {"error": "Backend Import Failed", "detail": str(e)}
