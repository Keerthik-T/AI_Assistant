import os
import sys
import re
import sounddevice as sd
import soundfile as sf
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

    print(f"{Colors.CYAN}🎭 Lady Furina:{Colors.ENDC}")
    print(f"{Colors.CYAN}\"*strikes a grand curtsy* Welcome to the grand stage! Speak, my dear audience, and let the performance begin!\"{Colors.ENDC}\n")

    while True:
        try:
            # Capture user keyboard input
            prompt = input(f"{Colors.WARNING}{Colors.BOLD}Dear Audience > {Colors.ENDC}").strip()
            
            if not prompt:
                continue
                
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

            # Stream audio waveform from response.wav using sounddevice and soundfile
            local_audio_path = os.path.join("static", "response.wav")
            if os.path.exists(local_audio_path):
                try:
                    data, fs = sf.read(local_audio_path)
                    sd.play(data, fs)
                    # Block execution until audio completes, supporting interruption
                    try:
                        sd.wait()
                    except KeyboardInterrupt:
                        sd.stop()
                        print(f"\n{Colors.WARNING}*Lady Furina has been politely interrupted*{Colors.ENDC}\n")
                except Exception as audio_err:
                    print(f"{Colors.FAIL}[Audio Engine Error] Failed to stream audio waveform: {audio_err}{Colors.ENDC}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}KeyboardInterrupt detected. Type 'exit' to quit or continue talking.{Colors.ENDC}\n")
        except Exception as e:
            print(f"{Colors.FAIL}An error occurred during execution: {e}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
