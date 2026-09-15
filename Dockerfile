FROM python:3.10-slim

# Install system dependencies for audio, STT, TTS, and basic build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    ffmpeg \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application source
COPY . /app

# Run the terminal mode of Furina
CMD ["python", "run_terminal.py"]
