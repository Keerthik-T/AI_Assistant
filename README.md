# FurinaOS: Native Theatrical AI Agent Core

FurinaOS is a fully localized, voice-activated AI assistant designed to run seamlessly on local hardware. It features a passive wake-word detection loop, state-of-the-art offline speech-to-text (STT) via Faster-Whisper, large language model orchestration via Langchain/Ollama, and high-quality offline text-to-speech (TTS) synthesis using the Kokoro ONNX engine.

## 🚀 Features

* **Desktop Orb UI:** A beautiful, glowing, translucent desktop widget that pulses and changes color based on Furina's current state (Idle, Listening, Thinking, Speaking).
* **Wake-Word Activation:** Passively listens for the wake-word ("hello") in the background without blocking execution, dynamically adjusting to ambient room noise using Voice Activity Detection (VAD).
* **Offline Speech-To-Text:** Integrates with `faster-whisper` (base.en with int8 quantization) for blazing-fast transcription of commands entirely on your CPU.
* **LLM Orchestration:** Powered by an intelligent orchestrator (`llm_engine.py` & `orchestrator.py`) utilizing local Ollama deployments to maintain full privacy and offline capabilities.
* **High-Fidelity TTS:** Leverages the Kokoro ONNX engine to deliver incredibly fast, high-quality synthesized speech without relying on cloud APIs.

## 📋 Prerequisites

To run FurinaOS locally, you will need:
* **Python 3.10+**
* **Ollama** installed and running locally with your desired LLM model (default is `gemma4:e2b`).
* Required Python dependencies listed in `requirements.txt`.
* (Optional) **FFmpeg** installed and accessible in your system's PATH.

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Keerthik-T/AI_Assistant.git
   cd AI_Assistant
   ```

2. **Set up the Virtual Environment & Install Dependencies**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Download Kokoro TTS Models**
   You must place the Kokoro model files in the root directory before running:
   * [kokoro-v1.0.onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx)
   * [voices-v1.0.bin](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin)

   *(Note: The `faster-whisper` STT model will download automatically on first run).*

## 🎙️ Usage

FurinaOS comes in two flavors: a graphical Desktop Orb and a lightweight Terminal mode.

### 1. Desktop Orb Mode (Recommended)
This launches a native, frameless, draggable glowing orb on your desktop that visualizes her state.
* **Via Script:** Run `python ui_desktop.py`
* **Via Batch:** Double click `furinaos.bat`
* **On Startup (Invisible Console):** Place a shortcut to `invisible_launcher.vbs` in your Windows Startup folder to have her silently boot when you turn on your PC.

### 2. Terminal Mode
If you prefer to see the raw text outputs, logs, and STT transcripts:
* **Via Script:** Run `python run_terminal.py`
* **Via Batch:** Double click `furina_terminal.bat`

Once the system initializes, the daemon will begin listening. Simply say **"hello"** followed by your command to interact with FurinaOS.

## 🔒 Privacy & Security

FurinaOS is built with a strict emphasis on local-first execution. 
* All LLM inferences are handled locally through Ollama.
* Voice synthesis (TTS) operates entirely offline.
* Command transcription (STT) runs via local engines.

## 📄 License

This project is open-source and available for modification. See the LICENSE file for details.
