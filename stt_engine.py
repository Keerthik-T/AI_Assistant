import os
import numpy as np
from faster_whisper import WhisperModel

class STTEngine:
    def __init__(self, model_size="tiny.en", device="cpu", compute_type="int8"):
        print(f"Initializing STT Engine with model '{model_size}' on '{device}'...")
        # Under low resource (Ryzen 5 5600G CPU), using CPU with int8 quantization
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.sample_rate = 16000

    def transcribe_audio_array(self, audio_data: np.ndarray) -> str:
        """
        Transcribe raw float32 mono 16kHz audio data.
        """
        segments, info = self.model.transcribe(audio_data, beam_size=5)
        text = "".join([segment.text for segment in segments]).strip()
        return text

    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe an audio file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file {file_path} not found.")
        segments, info = self.model.transcribe(file_path, beam_size=5)
        text = "".join([segment.text for segment in segments]).strip()
        return text

    def record_microphone(self, duration: float = 5.0) -> np.ndarray:
        """
        Record audio from microphone using sounddevice.
        Strictly configured for 16000Hz, Mono, float32.
        """
        import sounddevice as sd
        print(f"Recording microphone for {duration} seconds...")
        # Record mono channel
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait() # Wait until recording is finished
        print("Recording finished.")
        return recording.flatten()

    def record_and_transcribe(self, duration: float = 5.0) -> str:
        try:
            audio_data = self.record_microphone(duration)
            return self.transcribe_audio_array(audio_data)
        except Exception as e:
            print(f"Failed to record/transcribe: {e}")
            return ""

# Simple sanity test when run directly
if __name__ == "__main__":
    stt = STTEngine()
    print("STT Engine initialized successfully!")
