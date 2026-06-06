import os
import tempfile
import subprocess
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from orchestrator import FurinaOrchestrator
from stt_engine import STTEngine

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = 'fontaine_secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create orchestrator (it will lazy-load LLM and TTS)
orchestrator = FurinaOrchestrator()
# Initialize STT engine
stt = STTEngine()

# Ensure static folder exists for responses
os.makedirs("static", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/toggles", methods=["GET", "POST"])
def manage_toggles():
    """
    Get or update the active security guardrails toggles.
    """
    if request.method == "POST":
        data = request.json or {}
        for key in orchestrator.guardrails.toggles:
            if key in data:
                orchestrator.guardrails.toggles[key] = bool(data[key])
        
        # Log toggle event
        orchestrator.guardrails.log_event(
            "CONFIGURATION", 
            "UPDATE", 
            f"Guardrail states modified: {orchestrator.guardrails.toggles}"
        )
        
    return jsonify(orchestrator.guardrails.toggles)

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint for text-based requests.
    """
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Run query through orchestrator
    result = orchestrator.route_and_execute(prompt)
    
    # Broadcast logs via WebSocket if any clients are listening
    socketio.emit("security_logs", result["logs"])
    
    return jsonify(result)

@app.route("/api/voice", methods=["POST"])
def voice():
    """
    Voice upload endpoint for mic recordings.
    Converts WebM/WAV from browser to 16kHz mono WAV using ffmpeg.
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Save incoming audio file to a temporary file
    temp_in_path = os.path.join(tempfile.gettempdir(), "incoming_mic_recording.webm")
    temp_out_path = os.path.join(tempfile.gettempdir(), "converted_16k_mono.wav")
    
    # Clean up old conversions
    if os.path.exists(temp_in_path):
        os.remove(temp_in_path)
    if os.path.exists(temp_out_path):
        os.remove(temp_out_path)
        
    audio_file.save(temp_in_path)

    # Convert audio to mono 16kHz WAV using FFmpeg
    try:
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", temp_in_path,
            "-ar", "16000", "-ac", "1", temp_out_path
        ]
        # Run conversion silently
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"FFmpeg conversion failed: {e}")
        return jsonify({"error": f"Audio processing error: FFmpeg failed: {e}"}), 500

    # Transcribe the converted WAV file
    try:
        orchestrator.guardrails.log_event("STT_ENGINE", "TRANSCRIPTION_START", "Transcribing client audio...")
        transcription = stt.transcribe_file(temp_out_path)
        orchestrator.guardrails.log_event("STT_ENGINE", "TRANSCRIPTION_COMPLETE", f"Transcribed text: '{transcription}'")
        
        if not transcription.strip():
            # Broadcast logs
            socketio.emit("security_logs", orchestrator.guardrails.security_logs)
            return jsonify({
                "route": "stt_empty",
                "text": "*looks confused* I couldn't hear a single word! Speak up, my dear audience!",
                "audio_path": None,
                "logs": orchestrator.guardrails.security_logs,
                "risk_score": 0
            })
            
    except Exception as e:
        print(f"STT transcription failed: {e}")
        return jsonify({"error": f"Speech transcription failed: {e}"}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(temp_in_path):
            os.remove(temp_in_path)
        if os.path.exists(temp_out_path):
            os.remove(temp_out_path)

    # Run transcribed text through orchestrator pipeline
    result = orchestrator.route_and_execute(transcription)
    result["transcribed_text"] = transcription
    
    # Broadcast logs
    socketio.emit("security_logs", result["logs"])
    
    return jsonify(result)

if __name__ == "__main__":
    print("Starting FurinaOS Web Server on http://localhost:5000...")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
