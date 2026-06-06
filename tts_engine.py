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
            print("TTS model files not found yet. Will load dynamically on first request.")

    def load_model(self):
        if self.kokoro is None:
            print(f"Initializing Kokoro TTS Engine with model={self.model_path} voices={self.voices_path}...")
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            print("TTS Engine initialized.")

    def synthesize(self, text: str, output_path: str, voice: str = "af_sarah", speed: float = 1.0) -> bool:
        """
        Synthesize text into speech and save as a WAV file.
        """
        try:
            self.load_model()
            if not self.kokoro:
                print("Cannot synthesize: Kokoro models are not loaded.")
                return False

            print(f"Synthesizing text: '{text}' using voice '{voice}'...")
            
            # Create audio samples
            # default language is 'en-us'
            samples, sample_rate = self.kokoro.create(
                text, 
                voice=voice, 
                speed=speed, 
                lang="en-us"
            )
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Write WAV file
            sf.write(output_path, samples, sample_rate)
            print(f"Saved generated speech to {output_path}")
            return True
            
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            return False

# Simple sanity test when run directly
if __name__ == "__main__":
    tts = TTSEngine()
    print("TTS Engine configured!")
