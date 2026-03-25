from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import os
import uuid

from backend.rag.ingest import process_file
from backend.rag.agent.graph import process_chat
from backend.config import UPLOAD_DIR

app = FastAPI(title="RAG Chatbot Workshop")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve frontend static files
if os.path.exists("./public"):
    app.mount("/", StaticFiles(directory="./public", html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request, __):
        if not request.url.path.startswith("/api"):
            from fastapi.responses import FileResponse
            return FileResponse("./public/index.html")
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows Vercel frontend to call Render backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_user"
    mode: str = "auto"
    top_k: int = 5

@app.get("/health")
def health_check():
    return {"status": "healthy", "db": "connected"}

@app.get("/debug")
def debug_check():
    """Debug endpoint to verify Gemini API config on Vercel."""
    import os
    from backend.config import GEMINI_API_KEY, CHAT_MODEL, FALLBACK_MODELS, DATABASE_URL
    
    result = {
        "api_key_set": bool(GEMINI_API_KEY),
        "api_key_preview": (GEMINI_API_KEY[:8] + "..." + GEMINI_API_KEY[-4:]) if GEMINI_API_KEY else "NOT SET",
        "chat_model": CHAT_MODEL,
        "fallback_models": FALLBACK_MODELS,
        "database_url_set": bool(DATABASE_URL),
        "is_vercel": bool(os.getenv("VERCEL")),
    }
    
    # Quick test: try a minimal Gemini API call
    try:
        from backend.config import get_genai_client
        client = get_genai_client()
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents="Say OK",
        )
        result["api_test"] = "SUCCESS"
        result["api_response"] = response.text[:100]
    except Exception as e:
        result["api_test"] = "FAILED"
        result["api_error"] = str(e)[:500]
    
    return result

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        answer, citations, trace, chart_data = process_chat(request.message, request.mode, session_id=request.session_id)
        return {
            "answer_text": answer,
            "citations": citations,
            "tool_trace": trace,
            "chart_data": chart_data,
            "latency_ms": 10
        }
    except Exception as e:
        import traceback
        err_str = str(e)
        print(f"ERROR in /chat: {err_str}")
        print(traceback.format_exc())
        
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            return JSONResponse(
                status_code=503,
                content={"error": "Gemini API quota exceeded.", "detail": err_str[:500]}
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": err_str[:500],
                "type": type(e).__name__
            }
        )

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    # This will stream responses
    async def event_generator():
        yield {"data": f"Receiving streaming chunk for {request.message}...\n\n"}
    
    return EventSourceResponse(event_generator())

@app.get("/documents")
def list_documents():
    """List all unique documents that have been ingested."""
    try:
        from backend.database import SessionLocal, DocChunk
        from sqlalchemy import text
        db = SessionLocal()
        try:
            rows = db.execute(text(
                "SELECT DISTINCT doc_id, metadata->>'filename' AS filename, COUNT(*) AS chunks "
                "FROM doc_chunks GROUP BY doc_id, filename ORDER BY filename"
            )).fetchall()
            return [{"doc_id": r.doc_id, "filename": r.filename or "Unknown", "chunks": r.chunks} for r in rows]
        except Exception as db_err:
            print(f"Database Query Error: {db_err}")
            raise HTTPException(status_code=500, detail=f"Database connection or query failed: {str(db_err)}")
        finally:
            db.close()
    except Exception as e:
        print(f"Server Error in /documents: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete all chunks for a given document."""
    from backend.database import SessionLocal, DocChunk
    db = SessionLocal()
    try:
        db.query(DocChunk).filter(DocChunk.doc_id == doc_id).delete()
        db.commit()
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/ingest/file")
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_id: str = Form(None),
    chunk_size: int = Form(600),
    overlap: int = Form(100)
):
    from backend.config import UPLOAD_DIR
    
    if doc_id is None:
        doc_id = str(uuid.uuid4())
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    # Process asynchronously
    background_tasks.add_task(process_file, file_path, doc_id, chunk_size, overlap)
    
    return {"status": "processing", "doc_id": doc_id, "filename": file.filename}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
