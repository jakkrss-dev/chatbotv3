import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://app:app@localhost:5432/ragdb")
EMBED_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash") 
EMBED_DIM = int(os.getenv("EMBED_DIM", 768))

print(f"DEBUG: Initializing with CHAT_MODEL = {CHAT_MODEL}")

if os.getenv("VERCEL") or os.getenv("RENDER"):
    UPLOAD_DIR = "/tmp"
else:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# AI Utilities
_client = None

def get_genai_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY is not set in environment variables.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

# Broad fallback list tailored to available models in this specific environment
FALLBACK_MODELS = [
    CHAT_MODEL, 
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
]

def generate_with_fallback(prompt: str = None, contents=None, config=None):
    """Generates content with automatic model fallback and retry logic for 429 errors."""
    last_err = None
    all_errors = {}
    is_vercel = bool(os.getenv("VERCEL"))
    max_retries = 1 if is_vercel else 2
    retry_sleep = 0.5 if is_vercel else 2
    # Deduplicate while preserving order
    models_to_try = []
    for m in FALLBACK_MODELS:
        if m and m not in models_to_try:
            models_to_try.append(m)
            
    for model_name in models_to_try:
        retries = max_retries
        while retries >= 0:
            try:
                # Support both simple prompt and full contents
                input_contents = contents if contents is not None else prompt
                response = get_genai_client().models.generate_content(
                    model=model_name,
                    contents=input_contents,
                    config=config
                )
                return response
            except Exception as e:
                err_str = str(e).lower()
                print(f"Generation attempt with {model_name} failed: {err_str}")
                all_errors[model_name] = str(e)
                
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    print(f"Quota hit for {model_name}, retrying... ({retries} retries left)")
                    retries -= 1
                    time.sleep(retry_sleep)
                    last_err = e
                    continue
                else:
                    # For non-quota errors (like 404), switch to next model immediately
                    print(f"Non-quota error with {model_name}, trying fallback...")
                    last_err = e
                    break 
                    
    error_summary = []
    for m, err in all_errors.items():
        error_summary.append(f"{m}: {err}")
    error_msg = "Generation failed with all models:\n" + "\n".join(error_summary)
    raise Exception(error_msg)

