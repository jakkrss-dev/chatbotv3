import sys
import os
from google import genai

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")

try:
    # Test v1alpha explicitly
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello"
    )
    print("SUCCESS: gemini-2.0-flash (v1alpha)")
    print(response.text)
except Exception as e:
    print(f"FAILED gemini-2.0-flash (v1alpha): {str(e)}")

try:
    # Test v1beta explicitly
    client2 = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    response2 = client2.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello"
    )
    print("SUCCESS: gemini-2.0-flash (v1beta)")
    print(response2.text)
except Exception as e:
    print(f"FAILED gemini-2.0-flash (v1beta): {str(e)}")
