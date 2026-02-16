from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = client.models.list()

for m in models:
    print("Model Name:", m.name)
    print("Model Type:", m.display_name)
    print("----")
