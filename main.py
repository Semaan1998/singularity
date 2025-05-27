from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# ✅ Enable CORS for all origins (for now)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later you can replace * with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Add root route for render health check and testing
@app.get("/")
def read_root():
    return {"message": "Singularity backend is live."}

# Define the expected request structure
class PromptRequest(BaseModel):
    prompt: str

# Classify the prompt to simulate different AI model responses
def classify_prompt(prompt: str) -> str:
    prompt = prompt.lower()
    if "image" in prompt or "draw" in prompt:
        return "Image Generation (Simulated)"
    elif "code" in prompt or "function" in prompt:
        return "DeepSeek (Simulated)"
    elif "why" in prompt or "analyze" in prompt:
        return "GPT-4o (Simulated)"
    else:
        return "Mistral (Simulated)"

# Simulate a response (placeholder logic)
def simulate_response(prompt: str, model: str) -> str:
    return f"[{model}] Response to: \"{prompt}\""

# Endpoint that receives POST requests from the frontend
@app.post("/prompt")
async def handle_prompt(data: PromptRequest):
    model = classify_prompt(data.prompt)
    reply = simulate_response(data.prompt, model)
    return {"model_used": model, "response": reply}
