import sys
import os
import json
from google import genai

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

load_dotenv(override=True)
client = genai.Client()

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say exactly 'hello'"
    )
    print("gemini-2.5-flash")
    print(response.text)
except Exception as e:
    print(f"gemini-2.5-flash {str(e)}")

