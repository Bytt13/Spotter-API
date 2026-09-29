import os
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai

load_dotenv()

print("=== GROQ MODELS ===")
try:
    groq_client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
    )
    models = groq_client.models.list()
    for m in models.data:
        print(m.id)
except Exception as e:
    print("Error getting Groq models:", e)

print("\n=== GEMINI MODELS ===")
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Error getting Gemini models:", e)
