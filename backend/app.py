import os
import gradio as gr
from dotenv import load_dotenv
from PIL import Image
import base64
import io
import hashlib
import traceback
from openai import AzureOpenAI

load_dotenv()

# ===============================
# AZURE CONFIG
# ===============================
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv(
        "AZURE_OPENAI_API_VERSION",
        "2024-02-15-preview"
    ),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ===============================
# IMAGE CACHE ONLY
# ===============================
crop_cache = {}


def get_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()


# ===============================
# IDENTIFY CROP
# ===============================
def identify_crop(image_file, crop_state):

    if image_file is None:
        return "❌ Please upload a crop image.", crop_state

    try:
        img = Image.open(image_file)

        if img.width > 1000 or img.height > 1000:
            img.thumbnail((1000, 1000))

        if img.mode != "RGB":
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)

        image_bytes = buffer.getvalue()
        image_hash = get_hash(image_bytes)

        # ✅ cache
        if image_hash in crop_cache:
            result = crop_cache[image_hash]
            return f"🌾 Cached Crop Result:\n\n{result}", result

        image_base64 = base64.b64encode(image_bytes).decode()

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content":
                    "You are an expert agricultural scientist."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":
                            "Identify this crop briefly."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":
                                f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                },
            ],
            max_tokens=300,
        )

        result = response.choices[0].message.content
        crop_cache[image_hash] = result

        # ✅ SAVE ONLY IN SESSION
        return f"🌾 Crop Identification:\n\n{result}", result

    except Exception:
        return traceback.format_exc(), crop_state


# ===============================
# CHATBOT
# ===============================
def ask_chatbot(message, crop_state):

    if not crop_state:
        return "⚠️ Please upload and identify a crop image first."

    context = f"\nCrop Info:\n{crop_state}\n"

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content":
                "You are a farming advisor. Give direct practical answers."
            },
            {
                "role": "user",
                "content": context + message
            }
        ],
        max_tokens=400,
    )

    return response.choices[0].message.content


# ===============================
# CHAT UI
# ===============================
def chat_ui(message, history, crop_state):

    if history is None:
        history = []

    if not message:
        return history, "", crop_state

    reply = ask_chatbot(message, crop_state)

    history.append([message, reply])

    return history, "", crop_state


# ===============================
# UI
# ===============================
with gr.Blocks(title="Crop Prediction") as demo:

    gr.Markdown(
        "# 🌾 Smart Crop Identification & Farming Assistant"
    )

    # ✅ SESSION MEMORY
    crop_state = gr.State(None)

    with gr.Row():

        with gr.Column():
            image_input = gr.Image(
                type="filepath",
                label="Upload Crop Image"
            )

            identify_btn = gr.Button("🔍 Identify Crop")

            image_output = gr.Textbox(
                lines=10,
                label="Result"
            )

        with gr.Column():
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(
                placeholder="Ask about soil, disease..."
            )
            send = gr.Button("Send")

    identify_btn.click(
        identify_crop,
        [image_input, crop_state],
        [image_output, crop_state]
    )

    send.click(
        chat_ui,
        [msg, chatbot, crop_state],
        [chatbot, msg, crop_state]
    )

    msg.submit(
        chat_ui,
        [msg, chatbot, crop_state],
        [chatbot, msg, crop_state]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        pwa=True,
        favicon_path="favicon.ico"
    )