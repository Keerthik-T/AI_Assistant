import os

import soundfile as sf
from kokoro_onnx import Kokoro


class TTSEngine:
    def __init__(self, model_path="kokoro-v1.0.onnx", voices_path="voices-v1.0.bin"):
        self.model_path = model_path
        self.voices_path = voices_path
        self.kokoro = None

        # We will lazy-load the model to prevent crash if running before models download finishes
        if os.path.exists(model_path) and os.path.exists(voices_path):
            self.load_model()
        else:
            print(
                "TTS model files not found yet. Will load dynamically on first request."
            )

    def load_model(self):
        if self.kokoro is None:
            print(
                f"Initializing Kokoro TTS Engine with model={self.model_path} voices={self.voices_path}..."
            )
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            print("TTS Engine initialized.")

    def synthesize(
        self, text: str, output_path: str, voice: str = "af_bella", speed: float = 1.0
    ) -> bool:
        """
        Legacy synthesize method for backwards compatibility.
        Routes to the new streaming engine and ignores output_path.
        """
        return self.synthesize_stream(text, voice, speed)

    def synthesize_stream(
        self, text: str, voice: str = "af_bella", speed: float = 1.0
    ) -> bool:
        """
        Synthesize text into speech and stream it live to the speakers.
        """
        voice = "af_bella"
        try:
            self.load_model()
            if not self.kokoro:
                print("Cannot synthesize: Kokoro models are not loaded.")
                return False

            print(f"Streaming text: '{text}' using voice profile '{voice}'...")

            import asyncio

            import sounddevice as sd

            async def _stream():
                stream = None
                try:
                    async for samples, sample_rate in self.kokoro.create_stream(
                        text, voice=voice, speed=speed, lang="en-us"
                    ):
                        if stream is None:
                            stream = sd.OutputStream(
                                samplerate=sample_rate, channels=1, dtype="float32"
                            )
                            stream.start()
                        stream.write(samples.astype("float32"))
                finally:
                    if stream is not None:
                        stream.stop()
                        stream.close()

            asyncio.run(_stream())
            return True

        except Exception as e:
            print(f"TTS streaming error: {e}")
            return False


# Simple sanity test when run directly
if __name__ == "__main__":
    tts = TTSEngine()
    print("TTS Engine configured!")
