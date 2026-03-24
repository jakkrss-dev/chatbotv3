import os
import sys
# Add parent directory to sys.path to allow importing backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag.ingest import process_file
import uuid

if __name__ == "__main__":
    file_path = r"d:\chatbotv2\uploads\11.pdf"
    doc_id = str(uuid.uuid4())
    print(f"Starting manual ingestion of {file_path} with doc_id {doc_id}")
    try:
        process_file(file_path, doc_id)
        print("Finalizing ingestion test.")
    except Exception as e:
        print(f"FAILED manual ingestion: {e}")
