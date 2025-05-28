import os
from dotenv import load_dotenv

# Load .env explicitly from the current file's directory
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
loaded = load_dotenv(dotenv_path=dotenv_path)

print("✅ .env loaded:", loaded)
print("🔑 OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))
