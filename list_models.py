import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Available Gemini models:")
    for model in genai.list_models():
        print(f"Model: {model.name}")
        if model.supported_generation_methods:
            print(f"  Supported methods: {model.supported_generation_methods}")
        print(f"  Description: {model.description}")
        print("---")