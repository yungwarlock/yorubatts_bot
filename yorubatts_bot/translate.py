import os
import google.generativeai as genai


genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "top_k": 64,
    "top_p": 0.95,
    "temperature": 1,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,  # type: ignore
    system_instruction="Translate the following text to yoruba. Please do not do anything else!",
)

chat_session = model.start_chat(history=[])


def translate_to_yoruba(text: str):
    response = chat_session.send_message(text)
    return response.text
