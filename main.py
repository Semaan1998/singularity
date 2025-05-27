from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

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

def simulate_response(prompt: str, model: str) -> str:
    return f"[{model}] Response to: \"{prompt}\""

@app.post("/prompt")
async def handle_prompt(data: PromptRequest):
    model = classify_prompt(data.prompt)
    reply = simulate_response(data.prompt, model)
    return { "model_used": model, "response": reply }
