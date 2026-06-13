FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for pyaudio, sounddevice, and speech recognition
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Note: Model downloading is kept out of the Dockerfile build process by default to keep the image lightweight.
# You can run `python download_models.py` inside the container or download them locally first.

# Start the terminal interface
CMD ["python", "run_terminal.py"]
