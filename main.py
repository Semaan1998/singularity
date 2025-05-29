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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not found in .env or environment variables.")
else:
    print("✅ OPENAI_API_KEY loaded.")

MODEL_NAME = "gpt-4o"

app = FastAPI()

# ✅ Serve frontend from /static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

# ✅ Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

# ✅ In-memory conversation state
last_exchange = {
    "user_prompt": None,
    "assistant_reply": None,
    "continue_count": 0,
    "history": []
}

@app.post("/prompt")
async def handle_prompt(data: PromptRequest):
    """Handle text-only prompts."""
    prompt = data.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    last_exchange["history"].append({"role": "user", "content": prompt})
    reply = ask_singularity(prompt, model=MODEL_NAME, history=last_exchange["history"])

    if not reply:
        raise HTTPException(status_code=500, detail="Model returned no response.")

    last_exchange["history"].append({"role": "assistant", "content": reply})
    last_exchange.update({
        "user_prompt": prompt,
        "assistant_reply": reply,
        "continue_count": 0
    })

    return {"model_used": MODEL_NAME, "response": reply}

@app.get("/continue")
def continue_last_reply():
    """Continue last response up to 2 times."""
    if last_exchange["continue_count"] >= 2:
        return {"error": "Continuation limit reached."}
    if not last_exchange["assistant_reply"]:
        return {"error": "No previous response to continue."}

    continuation_prompt = f"Continue from here:\n{last_exchange['assistant_reply']}"
    last_exchange["history"].append({"role": "user", "content": continuation_prompt})

    reply = ask_singularity(continuation_prompt, model=MODEL_NAME, history=last_exchange["history"])
    if not reply:
        raise HTTPException(status_code=500, detail="Model returned no continuation.")

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
    """Analyze up to 4 uploaded images with a prompt."""
    files = [file for file in [file0, file1, file2, file3] if file is not None]
    if not files:
        raise HTTPException(status_code=400, detail="No image files provided.")
    if not all(file.content_type.startswith("image/") for file in files):
        raise HTTPException(status_code=400, detail="All files must be images.")

    image_bytes_list = [await file.read() for file in files]
    vision_prompt = prompt.strip() or "What do you see in these images?"

    reply = ask_vision(prompt=vision_prompt, images=image_bytes_list, history=last_exchange["history"])
    if not reply:
        reply = "[Vision Error: Empty Response]"

    last_exchange["history"].append({"role": "user", "content": vision_prompt})
    last_exchange["history"].append({"role": "assistant", "content": reply})

    return {
        "response": reply,
        "filename": "virtual_collage.png"
    }
