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

### 1. Install System Dependencies
Before setting up the Python environment, you need to install the core AI and audio engines:

* **Ollama (LLM Engine):**
  1. Download and install [Ollama](https://ollama.com/download) for your operating system.
  2. Open your terminal and download the default Furina model:
     ```bash
     ollama run gemma4:e2b
     ```
     *(This ensures the Ollama daemon is running and the model is ready in the background).*
     
* **FFmpeg (Audio Processing):**
  * **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or install via winget: `winget install ffmpeg`
  * **Linux:** `sudo apt install ffmpeg`
  * **Mac:** `brew install ffmpeg`

### 2. Clone the Repository
```bash
git clone https://github.com/Keerthik-T/AI_Assistant.git
cd AI_Assistant
```

### 3. Set up the Python Environment
We highly recommend using a virtual environment to prevent conflicts with system packages.
```powershell
# Create the virtual environment
python -m venv .venv

# Activate it (Windows)
.\.venv\Scripts\activate

# Activate it (Linux/Mac)
# source .venv/bin/activate

# Install all required Python packages
pip install -r requirements.txt
```
*(Note: If you encounter PyAudio installation errors on Windows, you may need to install the Visual Studio C++ Build Tools).*

### 4. Download Kokoro TTS Models
The high-fidelity voice engine requires two specific files to be placed in the **root directory** of the project before running:
* Download [kokoro-v1.0.onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx) (~300MB)
* Download [voices-v1.0.bin](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin) (~100MB)

*(Note: The `faster-whisper` STT model will automatically download on its first run).*

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

## 🐳 Docker Deployment (Terminal Mode)

You can run the Terminal Mode of FurinaOS in a Docker container using the included `docker-compose.yml` file.

1. Ensure Ollama is running on your host machine.
2. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```
3. Attach to the container's interactive terminal to talk to Furina:
   ```bash
   docker exec -it furinaos-terminal python run_terminal.py
   ```

**⚠️ Important Audio Warning for Windows/Mac Users:**
By default, Docker maps the `/dev/snd` audio device, which only works out-of-the-box on **Native Linux**. If you are using Docker Desktop on Windows or Mac, the container cannot hear your microphone or play sound to your speakers without running a PulseAudio TCP server on your host machine and uncommenting the `PULSE_SERVER` lines in the `docker-compose.yml`.

## 🔒 Privacy & Security

FurinaOS is built with a strict emphasis on local-first execution. 
* All LLM inferences are handled locally through Ollama.
* Voice synthesis (TTS) operates entirely offline.
* Command transcription (STT) runs via local engines.

## 📄 License

This project is open-source and available for modification. See the LICENSE file for details.
