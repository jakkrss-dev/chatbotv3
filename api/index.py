try:
    from backend.main import app as handler
    app = handler
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    error_msg = str(e)
    error_trace = traceback.format_exc()
    
    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Import Error (Startup Crash)",
                "detail": error_msg,
                "trace": error_trace
            }
        )
