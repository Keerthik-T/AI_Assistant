# FurinaOS: Native Theatrical AI Agent Core

FurinaOS is a fully localized, voice-activated AI assistant designed to run seamlessly on local hardware. It features a passive wake-word detection loop, state-of-the-art offline speech-to-text (STT), large language model orchestration via Langchain/Ollama, and high-quality offline text-to-speech (TTS) synthesis using the Kokoro ONNX engine.

## 🚀 Features

* **Wake-Word Activation:** Passively listens for the wake-word ("hello") in the background without blocking execution, dynamically adjusting to ambient room noise.
* **Offline Speech-To-Text:** Integrates with local speech recognition capabilities (Faster Whisper/Google Speech Recognition) for precise transcription of commands.
* **LLM Orchestration:** Powered by an intelligent orchestrator (`llm_engine.py` & `orchestrator.py`) utilizing Langchain and local Ollama deployments to maintain full privacy and offline capabilities.
* **High-Fidelity TTS:** Leverages the Kokoro ONNX engine (`kokoro-onnx`) to deliver incredibly fast, high-quality synthesized speech without relying on cloud APIs.
* **Docker Support:** Includes a lightweight `Dockerfile` for containerized execution.

## 📋 Prerequisites

To run FurinaOS locally, you will need:
* **Python 3.10+**
* **Ollama** installed and running locally with your desired LLM model (e.g., `llama3` or `mistral`).
* **FFmpeg** installed and accessible in your system's PATH.
* Required Python dependencies listed in `requirements.txt`.

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Keerthik-T/AI_Assistant.git
   cd AI_Assistant
   ```

2. **Set up the Virtual Environment**
   Run the included setup script to automatically create a virtual environment and install dependencies:
   ```powershell
   .\setup_venv.ps1
   ```
   *Alternatively, you can manually install the dependencies:*
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Required Models**
   Run the downloader script to fetch the required local STT/TTS models (such as the Kokoro ONNX voices):
   ```bash
   python download_models.py
   ```

## 🎙️ Usage

To start the assistant, simply execute the startup batch script:
```cmd
start_furina.bat
```
Once the system initializes, the daemon will begin listening. Simply say **"hello"** followed by your command to interact with FurinaOS.

## 🐳 Docker Deployment

To build and run FurinaOS inside a Docker container:
```bash
docker build -t furinaos .
docker run -it --device /dev/snd furinaos
```
*Note: Audio passthrough in Docker may require additional configuration depending on your host operating system (e.g., PulseAudio/ALSA on Linux).*

## 🔒 Privacy & Security

FurinaOS is built with a strict emphasis on local-first execution. 
* All LLM inferences are handled locally through Ollama.
* Voice synthesis (TTS) operates entirely offline.
* Command transcription (STT) runs via local engines.
* A built-in guardrails engine ensures outputs remain safe and properly formatted before reaching the audio synthesis layer.

## 📄 License

This project is open-source and available for modification. See the LICENSE file for details.
