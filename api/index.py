import os
import sys

# Ensure the root is in the path so 'backend' package is found
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.append(root)

try:
    from backend.main import app as handler
    # Standard entry point for Vercel
    app = handler
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    # Debug app in case of import crash
    app = FastAPI()
    error_msg = str(e)
    error_trace = traceback.format_exc()
    
    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend Import Error",
                "detail": error_msg,
                "trace": error_trace
            }
        )
