import os
import sys
import re
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
from stt_engine import STTEngine
from orchestrator import FurinaOrchestrator

# Reconfigure stdout and stderr to use utf-8 to print emojis and unicode characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Enable ANSI escape sequences on Windows consoles natively
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# ANSI Styling Classes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    PURPLE = '\033[35m'

BANNER = f"""
{Colors.CYAN}{Colors.BOLD}*******************************************************************************
*             🎭  FurinaOS: Native Theatrical AI Agent Core v2.0  🎭           *
*             Executing on Ryzen 5600G Local Audio & Subprocess Loop          *
*******************************************************************************{Colors.ENDC}
"""

def play_activation_sound():
    """
    Play a short, high-quality chime sound using sounddevice and numpy.
    Uses a sine wave with a fade envelope to avoid clicks.
    """
    try:
        sample_rate = 16000
        duration = 0.2
        frequency = 1000
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        # Apply sine envelope for fade-in/fade-out
        envelope = np.sin(np.linspace(0, np.pi, len(t)))
        wave = np.sin(frequency * t * 2 * np.pi) * 0.2 * envelope
        sd.play(wave, sample_rate)
        sd.wait()
    except Exception as e:
        print(f"\n{Colors.WARNING}*Chime failed: {e}*{Colors.ENDC}\n")

def play_audio_response(audio_path=None):
    """
    Stream audio response waveform.
    """
    if audio_path is None:
        audio_path = os.path.join("static", "response.wav")
    if os.path.exists(audio_path):
        try:
            data, fs = sf.read(audio_path)
            sd.play(data, fs)
            # Block execution until audio completes, supporting interruption
            try:
                sd.wait()
            except KeyboardInterrupt:
                sd.stop()
                print(f"\n{Colors.WARNING}*Lady Furina has been politely interrupted*{Colors.ENDC}\n")
        except Exception as audio_err:
            print(f"{Colors.FAIL}[Audio Engine Error] Failed to stream audio waveform: {audio_err}{Colors.ENDC}")

def listen_for_wake_word(recognizer, microphone):
    """
    Continuously listens for the wake-word "hello".
    Returns True when a match is detected.
    """
    print(f"{Colors.BLUE}Listening for wake-word ('hello')...{Colors.ENDC}")
    try:
        with microphone as source:
            # We set timeout so we don't block forever and can handle interrupts
            audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=4.0)
            text = recognizer.recognize_google(audio).lower()
            print(f"{Colors.BLUE}[Speech Heard]: \"{text}\"{Colors.ENDC}")
            # Use split or word boundaries to prevent matching substrings
            words = text.split()
            if "hello" in words:
                return True
    except sr.WaitTimeoutError:
        pass
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"{Colors.WARNING}[SpeechRecognition Engine] API error: {e}{Colors.ENDC}")
        import time
        time.sleep(1)
    except Exception as e:
        print(f"{Colors.WARNING}[SpeechRecognition Engine] Error: {e}{Colors.ENDC}")
        import time
        time.sleep(1)
    return False

def print_guardrail_logs(logs):
    if not logs:
        return
    print(f"\n{Colors.PURPLE}{Colors.BOLD}[Security Guardrail logs]{Colors.ENDC}")
    for log in logs:
        status = log.get('status', '')
        if status == 'PASS':
            status_str = f"{Colors.GREEN}PASS{Colors.ENDC}"
        elif status in ['BLOCKED', 'HALTED']:
            status_str = f"{Colors.FAIL}!!! {status} !!!{Colors.ENDC}"
        elif status == 'ALERT' or status == 'SANITIZED':
            status_str = f"{Colors.WARNING}{status}{Colors.ENDC}"
        else:
            status_str = f"{Colors.BLUE}{status}{Colors.ENDC}"
            
        print(f"  {Colors.BOLD}• [{log.get('event_type')}]{Colors.ENDC} {status_str} : {log.get('details')}")
    print()

def main():
    print(BANNER)
    print(f"{Colors.BLUE}Initializing FurinaOS Core Orchestrator...{Colors.ENDC}")
    
    # Instantiate orchestrator
    try:
        orchestrator = FurinaOrchestrator()
        print(f"{Colors.GREEN}Successfully loaded FurinaOS! Stage is set.{Colors.ENDC}\n")
    except Exception as e:
        print(f"{Colors.FAIL}Failed to initialize orchestrator: {e}{Colors.ENDC}")
        sys.exit(1)

    # Instantiate engines for Wake-Word and STT
    print(f"{Colors.BLUE}Initializing Wake-Word & STT Engines...{Colors.ENDC}")
    try:
        r = sr.Recognizer()
        mic = sr.Microphone()
        stt = STTEngine()
        print(f"{Colors.GREEN}Engines successfully initialized!{Colors.ENDC}\n")
    except Exception as e:
        print(f"{Colors.FAIL}Failed to initialize audio capture/transcription engines: {e}{Colors.ENDC}")
        sys.exit(1)

    # Calibrate Microphone
    try:
        with mic as source:
            print(f"\n{Colors.BLUE}[Audio Pipeline]: Calibrating microphone for ambient room noise... Please remain quiet.{Colors.ENDC}")
            r.adjust_for_ambient_noise(source, duration=2)
            r.energy_threshold = max(r.energy_threshold, 300)
            print(f"{Colors.GREEN}[Audio Pipeline]: Calibration complete. Listening threshold locked at: {r.energy_threshold}{Colors.ENDC}\n")
    except Exception as e:
        print(f"{Colors.WARNING}Calibration failed: {e}. Using default settings.{Colors.ENDC}\n")

    # Proactive Morning Briefing
    print(f"{Colors.CYAN}🎭 Lady Furina (Startup Morning Briefing):{Colors.ENDC}")
    briefing_prompt = (
        "Search the web for the latest cybersecurity and tech news for today. "
        "Give me a theatrical 'Good Morning' greeting, tell me systems are online, "
        "and suggest 3 new tech topics I should learn today based on the news."
    )
    try:
        result = orchestrator.route_and_execute(briefing_prompt)
        print_guardrail_logs(result.get("logs", []))
        response_text = result.get("text", "")
        print(f"{Colors.CYAN}{response_text}{Colors.ENDC}\n")
        play_audio_response()
    except Exception as e:
        print(f"{Colors.FAIL}Failed during startup morning briefing: {e}{Colors.ENDC}\n")

    print(f"{Colors.GREEN}FurinaOS Background Daemon is now active. Speak 'hello' to interact.{Colors.ENDC}\n")

    while True:
        try:
            # Passive wake-word listening loop
            if not listen_for_wake_word(r, mic):
                continue

            # Play activation chime
            play_activation_sound()
            print(f"{Colors.GREEN}{Colors.BOLD}*Speak now! Lady Furina is listening...*{Colors.ENDC}")

            # Actively record command
            prompt = stt.record_and_transcribe(duration=5.0).strip()
            if not prompt:
                print(f"{Colors.WARNING}No command detected or transcription was empty.{Colors.ENDC}\n")
                continue

            print(f"{Colors.WARNING}{Colors.BOLD}Dear Audience > {Colors.ENDC}{prompt}\n")

            if prompt.lower() in ['exit', 'quit', 'bye']:
                print(f"\n{Colors.CYAN}🎭 Lady Furina: \"*waves elegantly* Farewell, my dear audience! Until our next grand performance!\"{Colors.ENDC}")
                break

            # Execute pipeline
            result = orchestrator.route_and_execute(prompt)

            # Output guardrail logs
            print_guardrail_logs(result.get("logs", []))

            # Display response
            response_text = result.get("text", "")
            print(f"{Colors.CYAN}{Colors.BOLD}🎭 Lady Furina:{Colors.ENDC}")
            print(f"{Colors.CYAN}{response_text}{Colors.ENDC}\n")

            # Play audio response
            play_audio_response()

        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}KeyboardInterrupt detected. Continuing daemon loop...{Colors.ENDC}\n")
        except Exception as e:
            print(f"{Colors.FAIL}An error occurred during execution: {e}{Colors.ENDC}\n")
            import time
            time.sleep(1)

if __name__ == "__main__":
    main()
