from google import genai
from sqlalchemy import text
from backend.database import SessionLocal
from backend.config import GEMINI_API_KEY, EMBED_MODEL
import json

client = genai.Client(api_key=GEMINI_API_KEY)

def embed_query(query: str) -> list[float]:
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[query],
        config=genai.types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768
        )
    )
    # Handle API response extraction
    return list(response.embeddings[0].values)

def search_documents(query: str, top_k: int = 5):
    query_vec = embed_query(query)
    
    # 1 - cosine_distance = cosine similarity
    sql = text("""
        SELECT chunk_id, doc_id, chunk_index, content, metadata,
               1 - (embedding <=> :query_vec) AS score
        FROM doc_chunks
        ORDER BY embedding <=> :query_vec
        LIMIT :top_k
    """)
    
    db = SessionLocal()
    # pgvector expects string representation like '[0.1, 0.2, ...]'
    vec_str = "[" + ",".join(map(str, query_vec)) + "]"
    
    results = db.execute(sql, {"query_vec": vec_str, "top_k": top_k}).fetchall()
    db.close()
    
    formatted_results = []
    for row in results:
        formatted_results.append({
            "chunk_id": str(row.chunk_id),
            "doc_id": row.doc_id,
            "chunk_index": row.chunk_index,
            "content": row.content,
            "metadata": row.metadata,
            "score": float(row.score)
        })
        
    return formatted_results
