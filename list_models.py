import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    if not GEMINI_API_KEY:
        print("No API Key found")
        return
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        models = client.models.list()
        for m in models:
            if "generateContent" in m.supported_actions:
                print(f"Supported for generateContent: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    main()
