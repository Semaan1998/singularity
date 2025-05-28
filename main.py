from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from gpt_agent import ask_singularity, ask_vision

# ✅ Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

if os.getenv("OPENAI_API_KEY"):
    print("✅ OPENAI_API_KEY loaded.")
else:
    raise RuntimeError("❌ OPENAI_API_KEY not found in .env")

app = FastAPI()

# ✅ Serve static files from root directory
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
def serve_home():
    return FileResponse("index.html")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

# ✅ In-memory conversation memory
last_exchange = {
    "user_prompt": None,
    "assistant_reply": None,
    "continue_count": 0,
    "history": []
}

@app.post("/prompt")
async def handle_prompt(data: PromptRequest):
    prompt = data.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    # Append new user message to history
    last_exchange["history"].append({"role": "user", "content": prompt})

    # Ask model using full history
    reply = ask_singularity(prompt, model="gpt-4o", history=last_exchange["history"])

    # Append assistant reply to history
    last_exchange["history"].append({"role": "assistant", "content": reply})

    last_exchange.update({
        "user_prompt": prompt,
        "assistant_reply": reply,
        "continue_count": 0
    })
    return {"model_used": "gpt-4o", "response": reply}

@app.get("/continue")
def continue_last_reply():
    if last_exchange["continue_count"] >= 2:
        return {"error": "Continuation limit reached for this prompt."}
    if not last_exchange["assistant_reply"]:
        return {"error": "No previous response to continue."}

    continuation_prompt = f"Continue from here:\n{last_exchange['assistant_reply']}"
    last_exchange["history"].append({"role": "user", "content": continuation_prompt})
    reply = ask_singularity(continuation_prompt, model="gpt-4o", history=last_exchange["history"])
    last_exchange["history"].append({"role": "assistant", "content": reply})

    last_exchange["continue_count"] += 1
    last_exchange["assistant_reply"] += "\n" + reply

    return {
        "continued": True,
        "continue_count": last_exchange["continue_count"],
        "response": reply
    }

@app.post("/analyze-image/")
async def analyze_image(
    prompt: str = Form(...),
    file0: UploadFile = File(None),
    file1: UploadFile = File(None),
    file2: UploadFile = File(None),
    file3: UploadFile = File(None),
):
    files = [file for file in [file0, file1, file2, file3] if file is not None]

    if not files:
        raise HTTPException(status_code=400, detail="No image files provided.")
    if not all(file.content_type.startswith("image/") for file in files):
        raise HTTPException(status_code=400, detail="All files must be images.")

    image_bytes_list = [await file.read() for file in files]

    vision_prompt = prompt.strip() or "What do you see in these images?"
    reply = ask_vision(prompt=vision_prompt, images=image_bytes_list, history=last_exchange["history"])

    # Append vision question and reply to history
    last_exchange["history"].append({"role": "user", "content": vision_prompt})
    last_exchange["history"].append({"role": "assistant", "content": reply})

    return {
        "response": reply or "[Vision Error: Empty Response]",
        "filename": "collage.png"
    }
