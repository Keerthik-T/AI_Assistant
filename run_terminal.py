import os
import re
import sys
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

from orchestrator import FurinaOrchestrator
from stt_engine import STTEngine

# Global lock for audio playback to prevent overlapping speech
audio_lock = threading.Lock()

# Reconfigure stdout and stderr to use utf-8 to print emojis and unicode characters on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Enable ANSI escape sequences on Windows consoles natively
if sys.platform == "win32":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


# ANSI Styling Classes
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    PURPLE = "\033[35m"


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
    Deprecated: Audio is now streamed directly during synthesis by tts_engine.py.
    """
    pass


def proactive_daemon_loop(orchestrator):
    """
    A lightweight background thread that wakes up periodically (e.g., every 5 minutes)
    to check the weather/news API and proactively speak.
    """
    check_weather = True
    while True:
        # Sleep for 5 minutes
        time.sleep(300)
        print(
            f"\n{Colors.PURPLE}[Daemon] Waking up to perform proactive checks...{Colors.ENDC}"
        )
        try:
            if check_weather:
                prompt = "Proactively check the live weather for Salem, Tamil Nadu and announce it to me theatrically. Say 'Pardon the interruption, but I have a weather update!'"
            else:
                prompt = "Proactively perform a web search for the latest breaking news in technology and announce it to me theatrically. Say 'Pardon the interruption, but I have a news update!'"
            check_weather = not check_weather
            result = orchestrator.route_and_execute(prompt)
            print_guardrail_logs(result.get("logs", []))
            response_text = result.get("text", "")

            with audio_lock:
                pass
                # TTS streams live, so no need to call play_audio_response
        except Exception as e:
            print(f"{Colors.FAIL}[Daemon] Error in background task: {e}{Colors.ENDC}")


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
            text = recognizer.recognize_faster_whisper(audio).lower()
            print(f'{Colors.BLUE}[Speech Heard]: "{text}"{Colors.ENDC}')
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
        status = log.get("status", "")
        if status == "PASS":
            status_str = f"{Colors.GREEN}PASS{Colors.ENDC}"
        elif status in ["BLOCKED", "HALTED"]:
            status_str = f"{Colors.FAIL}!!! {status} !!!{Colors.ENDC}"
        elif status == "ALERT" or status == "SANITIZED":
            status_str = f"{Colors.WARNING}{status}{Colors.ENDC}"
        else:
            status_str = f"{Colors.BLUE}{status}{Colors.ENDC}"

        print(
            f"  {Colors.BOLD}• [{log.get('event_type')}]{Colors.ENDC} {status_str} : {log.get('details')}"
        )
    print()


def main():
    print(BANNER)
    print(f"{Colors.BLUE}Initializing FurinaOS Core Orchestrator...{Colors.ENDC}")

    # Instantiate orchestrator
    try:
        orchestrator = FurinaOrchestrator()
        print(
            f"{Colors.GREEN}Successfully loaded FurinaOS! Stage is set.{Colors.ENDC}\n"
        )
    except Exception as e:
        print(f"{Colors.FAIL}Failed to initialize orchestrator: {e}{Colors.ENDC}")
        sys.exit(1)

    # Instantiate engines for Wake-Word and STT
    print(f"{Colors.BLUE}Initializing Wake-Word & STT Engines...{Colors.ENDC}")
    mic_available = False
    try:
        r = sr.Recognizer()
        mic = sr.Microphone()
        stt = STTEngine()
        mic_available = True
        print(
            f"{Colors.GREEN}Engines successfully initialized for Voice Mode!{Colors.ENDC}\n"
        )
    except Exception as e:
        print(
            f"{Colors.WARNING}Microphone not found or audio engine failed: {e}{Colors.ENDC}"
        )
        print(f"{Colors.GREEN}Falling back to Text-Only Mode.{Colors.ENDC}\n")

    if mic_available:
        # Calibrate Microphone
        try:
            with mic as source:
                print(
                    f"\n{Colors.BLUE}[Audio Pipeline]: Calibrating microphone for ambient room noise... Please remain quiet.{Colors.ENDC}"
                )
                r.adjust_for_ambient_noise(source, duration=2)
                r.energy_threshold = max(r.energy_threshold, 300)
                print(
                    f"{Colors.GREEN}[Audio Pipeline]: Calibration complete. Listening threshold locked at: {r.energy_threshold}{Colors.ENDC}\n"
                )
        except Exception as e:
            print(
                f"{Colors.WARNING}Calibration failed: {e}. Using default settings.{Colors.ENDC}\n"
            )

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
        # TTS streams live, no need to play_audio_response
    except Exception as e:
        print(
            f"{Colors.FAIL}Failed during startup morning briefing: {e}{Colors.ENDC}\n"
        )

    if mic_available:
        print(
            f"{Colors.GREEN}FurinaOS Background Daemon is now active in VOICE mode. Speak 'hello' to interact.{Colors.ENDC}\n"
        )
    else:
        print(
            f"{Colors.GREEN}FurinaOS Background Daemon is now active in TEXT mode. Type your commands below.{Colors.ENDC}\n"
        )

    # Start the proactive background thread
    daemon_thread = threading.Thread(
        target=proactive_daemon_loop, args=(orchestrator,), daemon=True
    )
    daemon_thread.start()
    print(
        f"{Colors.PURPLE}Proactive Background Thread started successfully. It will check APIs every 5 minutes.{Colors.ENDC}\n"
    )

    while True:
        try:
            if mic_available:
                # Passive wake-word listening loop
                if not listen_for_wake_word(r, mic):
                    continue

                # Play activation chime
                play_activation_sound()
                print(
                    f"{Colors.GREEN}{Colors.BOLD}*Speak now! Lady Furina is listening...*{Colors.ENDC}"
                )

                # Actively record command
                prompt = stt.record_and_transcribe(duration=5.0).strip()
                if not prompt:
                    print(
                        f"{Colors.WARNING}No command detected or transcription was empty.{Colors.ENDC}\n"
                    )
                    continue

                print(
                    f"{Colors.WARNING}{Colors.BOLD}Dear Audience > {Colors.ENDC}{prompt}\n"
                )
            else:
                prompt = input(
                    f"{Colors.WARNING}{Colors.BOLD}Dear Audience > {Colors.ENDC}"
                ).strip()
                if not prompt:
                    continue

            if prompt.lower() in ["exit", "quit", "bye"]:
                print(
                    f'\n{Colors.CYAN}🎭 Lady Furina: "*waves elegantly* Farewell, my dear audience! Until our next grand performance!"{Colors.ENDC}'
                )
                break

            # Execute pipeline
            result = orchestrator.route_and_execute(prompt)

            # Output guardrail logs
            print_guardrail_logs(result.get("logs", []))

            # Display response
            # Play audio response
            play_audio_response()

        except KeyboardInterrupt:
            print(
                f"\n\n{Colors.WARNING}KeyboardInterrupt detected. Continuing daemon loop...{Colors.ENDC}\n"
            )
        except Exception as e:
            print(
                f"{Colors.FAIL}An error occurred during execution: {e}{Colors.ENDC}\n"
            )
            import time

            time.sleep(1)


if __name__ == "__main__":
    main()
