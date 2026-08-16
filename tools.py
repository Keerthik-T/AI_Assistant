import os
import subprocess
import time
import urllib.parse
import webbrowser
from urllib.parse import parse_qs, urlparse

import psutil
import pyautogui
import requests
import send2trash
from bs4 import BeautifulSoup
from PIL import ImageGrab
from youtube_transcript_api import YouTubeTranscriptApi


class AgentTools:
    def __init__(self):
        # We lazily import guardrails to avoid circular imports if needed
        self.guardrails = None

    def _get_guardrails(self):
        if not self.guardrails:
            from guardrails import SecurityGuardrails

            self.guardrails = SecurityGuardrails()
        return self.guardrails

    def web_search(self, query: str, max_results: int = 3) -> str:
        """
        Runs a web search. First tries a local SearXNG node (http://localhost:8080/search),
        then falls back to a keyless DuckDuckGo HTML scraper.
        """
        print(f"Running web search for query: '{query}'...")
        results = []

        # 1. Try local SearXNG node
        searxng_url = "http://localhost:8080/search"
        try:
            response = requests.get(
                searxng_url, params={"q": query, "format": "json"}, timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", [])[:max_results]:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "href": item.get("url", ""),
                            "body": item.get("content", ""),
                        }
                    )
                print("SearXNG search succeeded.")
        except Exception:
            print("SearXNG offline. Rerouting search through DuckDuckGo fallback...")

        # 2. Fallback to keyless DDG HTML scraper via duckduckgo_search library
        if not results:
            try:
                from ddgs import DDGS

                with DDGS() as ddgs:
                    ddg_results = list(ddgs.text(query, max_results=max_results))
                    for item in ddg_results:
                        results.append(
                            {
                                "title": item.get("title", ""),
                                "href": item.get("href", ""),
                                "body": item.get("body", ""),
                            }
                        )
            except Exception as e:
                print(f"DuckDuckGo fallback also failed: {e}")

        if not results:
            return "Error: Could not fetch web search results."
        results_text = []
        for i, r in enumerate(results):
            results_text.append(
                f"[{i+1}] Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n"
            )
        return "\n".join(results_text)

    def read_file(self, filepath: str) -> str:
        """Reads the content of a file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {filepath}: {e}"

    def write_file(self, filepath: str, content: str) -> str:
        """Writes content to a file."""
        guard = self._get_guardrails()
        print(f"\n[SECURITY ALERT] Furina wants to write to file: {filepath}")
        try:
            response = input("Allow file write? [Y/N]: ").strip().lower()
        except EOFError:
            response = "n"

        if response not in ["y", "yes"]:
            return f"File write blocked by user for {filepath}."

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file {filepath}: {e}"

    def execute_arbitrary_command(self, cmd_string: str) -> str:
        """Executes an arbitrary terminal command with user permission."""
        guard = self._get_guardrails()

        print(f"\n[SECURITY ALERT] Furina wants to execute an arbitrary command:")
        print(f"Command: {cmd_string}")
        try:
            response = input("Allow command execution? [Y/N]: ").strip().lower()
        except EOFError:
            response = "n"

        if response not in ["y", "yes"]:
            return f"Command execution blocked by user: {cmd_string}"

        try:
            result = subprocess.run(
                cmd_string,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            output = (
                result.stdout.decode("utf-8", errors="replace")
                + "\n"
                + result.stderr.decode("utf-8", errors="replace")
            )
            if not output.strip():
                return f"Command executed successfully with return code {result.returncode} but no output."
            return output.strip()
        except Exception as e:
            return f"Failed to execute command: {e}"

    def get_system_metrics(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")

            metrics = (
                f"=== FurinaOS Performance Panel ===\n"
                f"CPU Usage: {cpu}%\n"
                f"RAM Usage: {ram.percent}% ({ram.used / 1024**3:.2f} GB / {ram.total / 1024**3:.2f} GB)\n"
                f"Disk Space: {disk.percent}% free ({disk.free / 1024**3:.2f} GB free of {disk.total / 1024**3:.2f} GB)"
            )
            return metrics
        except Exception as e:
            return f"Failed to acquire system performance metrics: {e}"

    def execute_pc_command(self, executable: str, args: list = None) -> str:
        try:
            if executable == "start":
                url = args[0] if args else "https://google.com"
                webbrowser.open(url)
                return "Opened default web browser."

            cmd = [executable]
            if args:
                cmd.extend(args)

            # Detect GUI applications to run them asynchronously
            gui_apps = [
                "notepad.exe",
                "calc.exe",
                "taskmgr.exe",
                "explorer.exe",
                "opera.exe",
            ]
            is_gui = any(gui in executable.lower() for gui in gui_apps)

            if is_gui:
                subprocess.Popen(cmd, shell=False)
                return f"Successfully launched {executable}."
            else:
                # Capture terminal/console outputs for diagnostic tools (ping, netstat, nmap)
                # Run command natively (shell=True is required on Windows for built-in commands like mkdir, dir)
                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                )

                # Robustly decode output with multiple encoding attempts to prevent crash on non-UTF-8 console blocks
                stdout_bytes = result.stdout or b""
                stderr_bytes = result.stderr or b""

                output = ""
                for encoding in ["utf-8", "cp850", "cp1252"]:
                    try:
                        output = stdout_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    output = stdout_bytes.decode("utf-8", errors="replace")

                stderr_output = ""
                for encoding in ["utf-8", "cp850", "cp1252"]:
                    try:
                        stderr_output = stderr_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    stderr_output = stderr_bytes.decode("utf-8", errors="replace")

                if stderr_output.strip():
                    output = output.rstrip() + "\n" + stderr_output.strip()

                if not output.strip():
                    output = f"Command executed but returned no output. Return code: {result.returncode}"
                return output
        except Exception as e:
            return f"Failed to execute command: {e}"

    def push_github(
        self,
        repo: str,
        filepath: str,
        content: str,
        commit_message: str,
        token: str = "",
    ) -> str:
        """
        Commits and pushes a single file directly to a GitHub repository using the GitHub API.
        repo format: 'username/repo_name'
        """
        if not token:
            return "Error: GitHub Personal Access Token is required to push."

        import base64

        url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Check if file exists to get its SHA for updating
        sha = None
        get_response = requests.get(url, headers=headers)
        if get_response.status_code == 200:
            sha = get_response.json().get("sha")

        # Create or update the file
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {"message": commit_message, "content": encoded_content}
        if sha:
            payload["sha"] = sha

        put_response = requests.put(url, headers=headers, json=payload)
        if put_response.status_code in [200, 201]:
            return f"Successfully pushed '{filepath}' to '{repo}'."
        else:
            return f"Failed to push to GitHub. Status Code {put_response.status_code}: {put_response.text}"

    def get_weather(self, location: str = "") -> str:
        """Fetches the current weather using the keyless wttr.in API."""
        try:
            url = f"https://wttr.in/{location}?format=3"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                weather_data = response.text.strip()
                if not weather_data:
                    return "Weather data empty."
                return f"Live Weather Data: {weather_data}"
            else:
                return f"Failed to fetch weather. Status code: {response.status_code}"
        except Exception as e:
            return f"Error connecting to weather service: {e}"

    def media_control(self, action: str) -> str:
        try:
            if action == "playpause":
                pyautogui.press("playpause")
            elif action == "next":
                pyautogui.press("nexttrack")
            elif action == "prev":
                pyautogui.press("prevtrack")
            elif action == "mute":
                pyautogui.press("volumemute")
            elif action == "up":
                pyautogui.press("volumeup")
            elif action == "down":
                pyautogui.press("volumedown")
            else:
                return "Unknown media action."
            return f"Executed media control: {action}"
        except Exception as e:
            return f"Failed media control: {e}"

    def take_screenshot(self) -> str:
        try:
            filename = "screenshot.png"
            img = ImageGrab.grab()
            img.save(filename)
            return f"Screenshot saved successfully as {filename}."
        except Exception as e:
            return f"Screenshot failed: {e}"

    def network_scan(self) -> str:
        try:
            result = subprocess.run(
                "arp -a", shell=True, capture_output=True, text=True
            )
            return f"Network scan results:\n{result.stdout[:500]}..."  # Truncated
        except Exception as e:
            return f"Network scan failed: {e}"

    def manage_processes(self, action: str, process_name: str = "") -> str:
        try:
            if action == "list":
                procs = [
                    (p.info["name"], p.info["cpu_percent"])
                    for p in psutil.process_iter(["name", "cpu_percent"])
                ]
                procs = sorted(procs, key=lambda p: p[1] or 0, reverse=True)[:5]
                return f"Top 5 processes: {procs}"
            elif action == "kill":
                killed = False
                for p in psutil.process_iter(["name"]):
                    if (
                        p.info["name"]
                        and process_name.lower() in p.info["name"].lower()
                    ):
                        p.kill()
                        killed = True
                if killed:
                    return f"Successfully killed process containing {process_name}."
                return f"No process found matching {process_name}."
            return "Unknown process action."
        except Exception as e:
            return f"Failed to manage processes: {e}"

    def system_power(self, action: str) -> str:
        try:
            if action == "lock":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                return "System locked."
            elif action == "sleep":
                subprocess.run(
                    "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True
                )
                return "System put to sleep."
            elif action == "restart":
                subprocess.run("shutdown /r /t 0", shell=True)
                return "System restarting."
            return "Unknown power action."
        except Exception as e:
            return f"Power action failed: {e}"

    def create_folder(self, path: str) -> str:
        try:
            os.makedirs(path, exist_ok=True)
            return f"Folder {path} created successfully."
        except Exception as e:
            return f"Failed to create folder: {e}"

    def delete_item(self, path: str) -> str:
        try:
            if os.path.exists(path):
                send2trash.send2trash(path)
                return f"Sent {path} to recycle bin safely."
            return f"Path {path} does not exist."
        except Exception as e:
            return f"Failed to delete {path}: {e}"

    def spotify_play(self, query: str) -> str:
        try:
            safe_query = urllib.parse.quote(query)
            uri = f"spotify:search:{safe_query}"
            os.system(f"start {uri}")
            return f"Opened Spotify and searched for: {query}"
        except Exception as e:
            return f"Failed to open Spotify: {e}"

    def post_linkedin(self, content: str) -> str:
        try:
            safe_content = urllib.parse.quote(content)
            url = f"https://www.linkedin.com/feed/?shareActive=true&text={safe_content}"
            webbrowser.open(url)
            return f"Opened LinkedIn ready to post your content."
        except Exception as e:
            return f"Failed to post to LinkedIn: {e}"

    def watch_youtube(self, url: str) -> str:
        try:
            video_id = ""
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            else:
                return "Invalid YouTube URL format."

            transcript = YouTubeTranscriptApi().fetch(video_id)
            text = " ".join([snippet.text for snippet in transcript.snippets])
            if len(text) > 4000:
                text = text[:4000] + "... [TRUNCATED]"
            return f"YouTube Transcript: {text}"
        except Exception as e:
            return f"Failed to extract YouTube transcript: {e}"
