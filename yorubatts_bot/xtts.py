"""
Text-to-speech service based on the xtts model.

The following code is based on the [XTTS-v2 model](https://huggingface.co/coqui/XTTS-v2)
and Coqui's [TTS package](https://github.com/coqui-ai/TTS) repository.

The TTS package is licensed under the Mozilla Public License 2.0,
which you may find at https://github.com/coqui-ai/TTS/blob/dev/LICENSE.txt

The model itself is licensed under the Coqui Public Model License,
which you may find at https://coqui.ai/cpml

"""

import io
import modal
import time

from yorubatts_bot import app

tts_image = (
    modal.Image.debian_slim(python_version="3.11.9")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "deepspeed==0.10.3",
        "ffmpeg-python==0.2.0",
        "git+https://github.com/coqui-ai/TTS@8c20a599d8d4eac32db2f7b8cd9f9b3d1190b73a",
    )

    # Coqui requires you to agree to the terms of service before downloading the model
    .env(
        {"COQUI_TOS_AGREED": "1"}
    )
)

with tts_image.imports():
    import torch
    import ffmpeg
    from TTS.api import TTS


# Make sure to deploy the model with modal deploy yorubatts_bot.xtts
@app.cls(
    gpu="A10G",
    timeout=600,  # slow load so make sure timeout is long enough to support model load
    image=tts_image,
    concurrency_limit=1,
    container_idle_timeout=600,
)
class XTTS:
    def __init__(self):
        pass

    # We can stack the build and enter methods to download the model during build and load it during entry
    @modal.build()
    @modal.enter()
    def load_model(self):
        # """
        # Load the model weights into GPU memory when the container starts.
        # """
        print("Loading XTTS model")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = TTS("tts_models/yor/openbible/vits").to(
            self.device
        )
        print("XTTS model loaded")

    @modal.method()
    def prewarm(self):
        # no-op to prewarm XTTS model instance
        pass

    def convert_to_mp4(self, wav_file: str, output_file):
        """
        Convert wav file to mp4 using ffmpeg.
        """
        (
            ffmpeg
            .input(wav_file)
            .output(output_file, acodec="aac", vcodec="libx264")
            .overwrite_output()
            .run()
        )

    @modal.method()
    def speak(self, text):
        """
        Runs xtts-v2 on a given text.
        """
        import tempfile

        t0 = time.time()
        # Save into an in-memory wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_f:
                self.model.tts_to_file(
                    text=text,
                    file_path=f,
                )
                print(f"TTS completed in {time.time() - t0:.2f}s")

                # Convert wav to mp4
                f.seek(0)
                self.convert_to_mp4(f.name, mp4_f.name)

                mp4_file = io.BytesIO()
                mp4_file.write(mp4_f.read())

                # return wav as a file object
                return text, mp4_file


# For local testing, run `modal run -q src.xtts --text "Hello, how are you doing on this fine day?"`
@app.local_entrypoint()
def tts_entrypoint(text: str = "Hello, how are you doing on this fine day?"):
    tts = XTTS()

    # run multiple times to ensure cache is warmed up
    text, wav = tts.speak.remote(text)
    with open("/tmp/output_xtts.mp4", "wb") as f:
        f.write(wav.getvalue())

    print("Done, output audio saved to /tmp/output_xtts.mp4")
