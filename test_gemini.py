from dotenv import load_dotenv
load_dotenv()
from google import genai
import os

api_key = os.getenv("GEMINI_API_KEY")
print("Key loaded:", api_key[:15], "...")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello in one sentence"
)
print("Response:", response.text) 
