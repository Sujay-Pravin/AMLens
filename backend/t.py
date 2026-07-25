import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from the .env file
load_dotenv()

# The client automatically picks up GEMINI_API_KEY from the environment
client = genai.Client()

response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="Hello Gemma!",
)

print(response.text)
