import os
import io
import sys

# Write output to a file so it doesn't get blocked by console
with open("test_api_log.txt", "w") as f:
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            f.write("No API key\n")
            sys.exit(1)
            
        from google import genai
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ]
        
        for m in models_to_test:
            f.write(f"Testing {m}...\n")
            try:
                response = client.models.generate_content(
                    model=m,
                    contents="Reply exactly with 'hello'."
                )
                f.write(f"SUCCESS {m}: {response.text}\n")
            except Exception as e:
                f.write(f"FAILED {m}: {str(e)}\n")
    except Exception as e:
        f.write(f"CRITICAL ERROR: {str(e)}\n")
