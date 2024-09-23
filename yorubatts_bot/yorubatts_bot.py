import os
import tempfile

import modal
from whatsapp.events import Message
from whatsapp.chat import ChatHandler
from whatsapp.reply_message import Message as ReplyMessage, Audio

from yorubatts_bot.translate import translate_to_yoruba


class SimpleChatHandler(ChatHandler):
    xtts = modal.Cls.lookup("yoruba-tts", "XTTS")()
    token = os.environ.get("WHATSAPP_ACCOUNT_TOKEN", "")
    whatsapp_number = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

    def on_message(self, message: Message):
        if message.type == "text" and message.message.text:
            text = message.message.text.body

            yoruba_text = translate_to_yoruba(text)
            print(f"Translated text: {yoruba_text}")

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_file:
                _, wav = self.xtts.speak.remote(yoruba_text)
                mp4_file.write(wav.getvalue())
                mp4_file.seek(0)

                req = ReplyMessage(
                    audio=Audio(
                        file=mp4_file.name,
                        mime_type="audio/mp4",
                    ),
                    type="audio",
                    to=message.to,
                )
                self.send(req)


def main():
    print("Starting server")
    chat_handler = SimpleChatHandler(debug=False, start_proxy=False)
    chat_handler.start("0.0.0.0", 5000)
