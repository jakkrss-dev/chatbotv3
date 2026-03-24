import pypdf
from google import genai
from sqlalchemy.orm import Session
from backend.database import SessionLocal, DocChunk
from backend.config import GEMINI_API_KEY, EMBED_MODEL
import uuid
import os

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_text_pypdf(file_path: str) -> str:
    try:
        reader = pypdf.PdfReader(file_path, strict=False)
        pages_text = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            
            uris = []
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    try:
                        annot_obj = annot.get_object()
                        if annot_obj.get("/Subtype") == "/Link":
                            if "/A" in annot_obj and "/URI" in annot_obj["/A"]:
                                uri = annot_obj["/A"]["/URI"]
                                uris.append(str(uri))
                    except Exception:
                        pass
            
            if uris:
                extracted += "\n\n[Links embedded in page: " + " , ".join(uris) + "]"
                
            if extracted and extracted.strip():
                pages_text.append(extracted.strip())
                
        text = "\n\n".join(pages_text)
        print(f"Extracted {len(text)} chars from {len(reader.pages)} pages.")
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100):
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed text chunks using Gemini. Forces output_dimensionality=768 to match VECTOR(768) in DB."""
    from google import genai as _genai
    embeddings = []
    batch_size = 20  # smaller batches to avoid quota issues
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"Embedding batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)...")
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=_genai.types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768
            )
        )
        for emb in response.embeddings:
            embeddings.append(list(emb.values))
    return embeddings

def process_file(file_path: str, doc_id: str, chunk_size: int = 600, overlap: int = 100):
    print(f"Processing {file_path}")
    text = ""
    if file_path.lower().endswith('.pdf'):
        text = extract_text_pypdf(file_path)
    else:
        # fallback for txt, md
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    
    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        print("No text extracted.")
        return
        
    embeddings = embed_chunks(chunks)
    
    db: Session = SessionLocal()
    try:
        filename = os.path.basename(file_path)
        for idx, (chunk_text_data, embedding) in enumerate(zip(chunks, embeddings)):
            doc_chunk = DocChunk(
                chunk_id=uuid.uuid4(),
                doc_id=doc_id,
                chunk_index=idx,
                content=chunk_text_data,
                embedding=embedding,
                metadata_col={"filename": filename}
            )
            db.add(doc_chunk)
        db.commit()
        print(f"Successfully ingrained {len(chunks)} chunks into DB.")
    except Exception as e:
        db.rollback()
        print(f"DB insertion error: {e}")
    finally:
        db.close()
