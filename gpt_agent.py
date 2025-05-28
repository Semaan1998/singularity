import os
import base64
import logging
import binascii
from PIL import Image
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Enable logging
logging.basicConfig(level=logging.INFO)

# ✅ Default system prompt
default_system_prompt = """
You are Singularity, a warm and helpful AI tutor with deep knowledge of science, math, and humanities.
You explain clearly and step-by-step, using a friendly tone and numbered structure when helpful.
You are patient, supportive, and curious. You never make the user feel dumb.
Your answers are optimized for clarity and usefulness, not exceeding 1000 tokens.
"""

def is_valid_base64(b64_string: str) -> bool:
    try:
        base64.b64decode(b64_string, validate=True)
        return True
    except binascii.Error:
        return False

# ✅ Ask Singularity (with history)
def ask_singularity(prompt: str, model: str = "gpt-4o", history: list = None, system: str = default_system_prompt) -> str:
    try:
        messages = [{"role": "system", "content": system}]
        if history and isinstance(history, list):
            messages.extend(history)
        else:
            messages.append({"role": "user", "content": prompt})

        # ✅ Debug: Show what’s being sent
        print("📤 Sending the following messages to OpenAI:")
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"[Text Model Error] {e}")
        return f"[OpenAI Error using {model} for text] {str(e)}"

# ✅ Combine images into one tall PNG and return base64
def combine_images_to_base64(images: list[bytes]) -> str:
    try:
        if not images:
            logging.warning("No images provided to combine.")
            return ""

        pil_images = [Image.open(BytesIO(img)).convert("RGB") for img in images]
        total_height = sum(img.height for img in pil_images)
        max_width = max(img.width for img in pil_images)

        combined = Image.new("RGB", (max_width, total_height), (255, 255, 255))
        y_offset = 0
        for img in pil_images:
            combined.paste(img, (0, y_offset))
            y_offset += img.height

        buffer = BytesIO()
        combined.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logging.error(f"[Image Combination Error] {e}")
        return ""

# ✅ Ask Singularity with vision (with optional history)
def ask_vision(prompt: str, images: list[bytes], model: str = "gpt-4o", history: list = None) -> str:
    if not images:
        return "[Vision Error] No images provided."

    b64_image = combine_images_to_base64(images)
    if not b64_image or not is_valid_base64(b64_image):
        return "[Vision Error] Invalid or empty base64 image string."

    try:
        logging.info(f"[Vision Prompt] {prompt} | {len(images)} image(s)")

        messages = [{"role": "system", "content": "You are a visual reasoning tutor AI. Describe and explain what you see."}]
        if history and isinstance(history, list):
            messages.extend(history)

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
            ]
        })

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"[Vision Model Error] {e}")
        return f"[Vision Error using {model} for image] {str(e)}"

