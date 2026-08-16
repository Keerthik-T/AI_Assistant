# orchestrator.py - UPDATED CLASS
import os
import re

from guardrails import SecurityGuardrails
from llm_engine import LLMEngine
from tools import AgentTools
from tts_engine import TTSEngine


class FurinaOrchestrator:
    def __init__(self, tts_model_ready=False):
        self.guardrails = SecurityGuardrails()
        self.tools = AgentTools()
        self.llm = LLMEngine()
        self.tts = TTSEngine()
        self.audio_output_path = os.path.join("static", "response.wav")
        self.is_sleeping = False  # FIXED: Awake by default for smoother local testing

    def _synthesize_clean(self, text: str, speed: float = 1.0) -> bool:
        """
        Cleans the response by removing physical action notations in asterisks,
        removing all URLs, and stripping parenthetical/bracketed snippets
        to ensure smooth and natural vocal streaming. Hardcodes Kokoro
        synthesis to explicitly use the 'af_bella' voice profile.
        """
        # 1. Strip all physical action notations (text within asterisks)
        clean_text = re.sub(r"\*.*?\*", "", text, flags=re.DOTALL)

        # 2. Strip parenthetical and bracketed content (e.g. (Introducing...) or [details])
        clean_text = re.sub(r"\(.*?\)", "", clean_text, flags=re.DOTALL)
        clean_text = re.sub(r"\[.*?\]", "", clean_text, flags=re.DOTALL)

        # 3. Strip all URLs (including http, https, www, and common domain extensions with paths)
        url_pattern = (
            r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s'\"()]*)*)"
        )
        clean_text = re.sub(url_pattern, "", clean_text)

        # 4. Clean up quotes, slashes, and punctuation leftovers
        clean_text = re.sub(r"['\"`]+", "", clean_text)  # remove leftover quotes
        clean_text = re.sub(
            r"\s*/+\s*", " ", clean_text
        )  # replace leftover slashes with spaces
        clean_text = re.sub(
            r"\s*;\s*", " ", clean_text
        )  # replace semicolons with spaces
        clean_text = re.sub(r"\s*:\s*", " ", clean_text)  # replace colons with spaces

        # 5. Clean up duplicate spaces and trim punctuation
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # 6. Normalize punctuation spacing and duplicate punctuation
        clean_text = re.sub(r"\s*([.,?!])", r"\1", clean_text)
        clean_text = re.sub(r"([.,?!])\1+", r"\1", clean_text)

        # Strip trailing punctuation and make sure it ends with a single clean period if needed
        clean_text = clean_text.strip().strip(",.?! ")
        if clean_text:
            clean_text += "."
        else:
            clean_text = "I have fetched the information for you."  # fallback

        self.guardrails.log_event(
            "TTS_ENGINE",
            "SYNTHESIS_START",
            f"Synthesizing clean vocal response: '{clean_text}' using voice: af_bella",
        )
        # Hardcode the voice profile argument explicitly to 'af_bella'
        return self.tts.synthesize(
            clean_text, self.audio_output_path, voice="af_bella", speed=speed
        )

    def route_and_execute(self, prompt: str) -> dict:
        self.guardrails.security_logs = []
        self.guardrails.log_event(
            "PIPELINE", "START", f"Processing user query: '{prompt}'"
        )

        # Active personality is hardcoded in the system prompt now.

        prompt_lower = prompt.lower().strip()
        wake_pattern = r"\b(hello[,\s]*(archon|arkon)?|hey[,\s]*(furina|farina|forina|verena|marina|arena)?|wake[,\s]*up)\b"
        wake_match = re.search(wake_pattern, prompt_lower)

        if self.is_sleeping:
            if wake_match:
                self.is_sleeping = False
                self.guardrails.log_event(
                    "PIPELINE", "UPDATE", "Wake word detected. Furina has awakened!"
                )
                prompt = re.sub(wake_pattern, "", prompt, flags=re.IGNORECASE).strip()
                prompt = re.sub(r"^[,\s:\-\?!]+", "", prompt).strip()
                if not prompt:
                    prompt = "Hello"
            else:
                self.guardrails.log_event(
                    "PIPELINE",
                    "BLOCKED",
                    "Input ignored. Furina is currently sleeping.",
                )
                canned_response = (
                    "*mumbles sleepily* Zzz... Address me as 'hey furina' to wake me..."
                )
                self._synthesize_clean(canned_response)
                return {
                    "route": "sleeping",
                    "text": canned_response,
                    "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                    "logs": self.guardrails.security_logs,
                    "risk_score": 0,
                }
        else:
            sleep_pattern = (
                r"\b(go[,\s]*to[,\s]*sleep|sleep[,\s]*now|good[,\s]*night)\b"
            )
            if re.search(sleep_pattern, prompt_lower):
                self.is_sleeping = True
                canned_response = "*yawns elegantly* Good night, my dear audience! I shall retire... Zzz..."
                self._synthesize_clean(canned_response)
                return {
                    "route": "sleeping",
                    "text": canned_response,
                    "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                    "logs": self.guardrails.security_logs,
                    "risk_score": 0,
                }

        # 1. Run Input Guardrails
        input_result = self.guardrails.process_input(prompt)
        processed_prompt = input_result["processed_text"]
        risk_score = input_result["risk_score"]

        if input_result["is_blocked"]:
            canned_response = "*gasps dramatically* Access denied! You cannot bypass my grand tribunal!"
            self._synthesize_clean(canned_response)
            return {
                "route": "blocked",
                "text": canned_response,
                "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                "logs": self.guardrails.security_logs,
                "risk_score": risk_score,
            }

        # 2. Agentic Reasoning Loop (Jarvis Mode)
        # We pass the prompt to the LLM first to see if it needs a tool.
        agent_system_prompt = f"""
You are Furina de Fontaine, a theatrical AI agent.
You have access to the following tools:
1. web_search(query) - Search the internet for live info (e.g. news).
2. get_system_metrics() - Get CPU, RAM, Disk usage.
3. execute(command) - Run an arbitrary PC terminal command.
4. weather(location) - Fetch live weather for a given location (or empty for default).
5. read_file(filepath) - Read contents of a local file.
6. write_file(filepath, content) - Write code/text to a local file.
7. push_github(repo, filepath, content, commit_msg, token) - Push a file directly to a GitHub repo.
8. media_control(action) - Actions: playpause, next, prev, mute, up, down.
9. take_screenshot() - Save a screenshot.
10. network_scan() - Scan local network.
11. manage_processes(action, name) - Actions: list, kill <name>.
12. system_power(action) - Actions: lock, sleep, restart.
13. create_folder(path) - Create a folder.
14. delete_item(path) - Move a file or folder to recycle bin.
15. spotify_play(query) - Search and play on Spotify.
16. post_linkedin(content) - Open a LinkedIn post draft.
17. watch_youtube(url) - Read a YouTube transcript.

To use a tool, output EXACTLY one of these formats:
<TOOL: web_search>your query</TOOL>
<TOOL: metrics>none</TOOL>
<TOOL: execute>your command</TOOL>
<TOOL: weather>city name</TOOL>
<TOOL: read_file>C:\\path\\to\\file.py</TOOL>
<TOOL: write_file>C:\\path\\to\\file.py | file content here</TOOL>
<TOOL: push_github>username/repo | file.py | content | commit message | ghp_token</TOOL>
<TOOL: media>action</TOOL>
<TOOL: screenshot>none</TOOL>
<TOOL: network>none</TOOL>
<TOOL: process>action | name</TOOL>
<TOOL: power>action</TOOL>
<TOOL: create_folder>C:\\path\\to\\folder</TOOL>
<TOOL: delete_item>C:\\path\\to\\item</TOOL>
<TOOL: spotify>query</TOOL>
<TOOL: linkedin>content</TOOL>
<TOOL: youtube>url</TOOL>

If you do NOT need a tool, just answer the user normally inside <ANSWER>your theatrical response</ANSWER>.
IMPORTANT: You MUST respond ONLY with a valid <TOOL> tag or <ANSWER> tag. Do NOT apologize. Do NOT say you are an AI model.
User Query: {processed_prompt}
"""

        # We bypass the standard chat history for the initial tool decision to keep it clean
        raw_decision = (
            self.llm.jarvis.ask(agent_system_prompt, context=False)
            if self.llm.jarvis
            else "<ANSWER>I cannot think, my brain is offline!</ANSWER>"
        )

        route = "chat"
        tool_output = ""
        final_response = ""

        # Parse tool use
        tool_match = re.search(
            r"<TOOL:\s*(.*?)\s*>(.*?)</TOOL>", raw_decision, re.DOTALL | re.IGNORECASE
        )
        answer_match = re.search(
            r"<ANSWER>\s*(.*?)\s*</ANSWER>", raw_decision, re.DOTALL | re.IGNORECASE
        )

        if tool_match:
            tool_name = tool_match.group(1).strip().lower()
            tool_arg = tool_match.group(2).strip()

            self.guardrails.log_event(
                "AGENT_LOOP",
                "TOOL_CALL",
                f"LLM requested tool: {tool_name} with arg: {tool_arg}",
            )

            if tool_name == "web_search":
                route = "web_search"
                tool_output = self.tools.web_search(tool_arg)
            elif tool_name == "metrics":
                route = "pc_metrics"
                tool_output = self.tools.get_system_metrics()
            elif tool_name == "read_file":
                route = "read_file"
                tool_output = self.tools.read_file(tool_arg)
            elif tool_name == "write_file":
                route = "write_file"
                try:
                    filepath, content = [x.strip() for x in tool_arg.split("|", 1)]
                    tool_output = self.tools.write_file(filepath, content)
                except:
                    tool_output = "Error parsing write_file arguments."
            elif tool_name == "push_github":
                route = "push_github"
                try:
                    parts = [x.strip() for x in tool_arg.split("|", 4)]
                    if len(parts) == 5:
                        tool_output = self.tools.push_github(
                            parts[0], parts[1], parts[2], parts[3], parts[4]
                        )
                    else:
                        tool_output = (
                            "Error: Invalid number of arguments for push_github."
                        )
                except Exception as e:
                    tool_output = f"Error pushing to github: {e}"
            elif tool_name == "weather":
                route = "weather"
                tool_output = self.tools.get_weather(tool_arg)
            elif tool_name == "media":
                route = "media"
                tool_output = self.tools.media_control(tool_arg)
            elif tool_name == "screenshot":
                route = "screenshot"
                tool_output = self.tools.take_screenshot()
            elif tool_name == "network":
                route = "network"
                tool_output = self.tools.network_scan()
            elif tool_name == "process":
                route = "process"
                parts = [x.strip() for x in tool_arg.split("|")]
                action = parts[0]
                name = parts[1] if len(parts) > 1 else ""
                tool_output = self.tools.manage_processes(action, name)
            elif tool_name == "power":
                route = "power"
                tool_output = self.tools.system_power(tool_arg)
            elif tool_name == "create_folder":
                route = "os"
                tool_output = self.tools.create_folder(tool_arg)
            elif tool_name == "delete_item":
                route = "os"
                tool_output = self.tools.delete_item(tool_arg)
            elif tool_name == "spotify":
                route = "spotify"
                tool_output = self.tools.spotify_play(tool_arg)
            elif tool_name == "linkedin":
                route = "linkedin"
                tool_output = self.tools.post_linkedin(tool_arg)
            elif tool_name == "youtube":
                route = "youtube"
                tool_output = self.tools.watch_youtube(tool_arg)
            elif tool_name == "execute":
                route = "pc_control"
                # Check whitelist via guardrails first; if not in whitelist, guardrails will ask for Y/N
                cmd_parts = tool_arg.split(" ")
                cmd_name = cmd_parts[0]
                args = cmd_parts[1:] if len(cmd_parts) > 1 else None
                cmd_validation = self.guardrails.process_command(cmd_name, args)

                if cmd_validation["is_allowed"]:
                    executable = cmd_validation["executable"]
                    safe_args = cmd_validation.get("args", [])
                    reconstructed_cmd = f"{executable} {' '.join(safe_args) if safe_args else ''}".strip()
                    tool_output = self.tools.execute_arbitrary_command(
                        reconstructed_cmd
                    )
                else:
                    tool_output = (
                        f"Command execution blocked: {cmd_validation['reason']}"
                    )
            else:
                tool_output = "Error: Invalid tool requested."

            # 3. Format Response via LLM (Second Pass)
            if route == "pc_metrics":
                llm_prompt = f"The user asked: '{processed_prompt}'. System metrics are: {tool_output}. Present these metrics dramatically!"
            elif route == "weather":
                llm_prompt = f"The user asked for weather: '{processed_prompt}'. Live data: {tool_output}. Present this weather dramatically as the Hydro Archon!"
            elif route == "pc_control":
                llm_prompt = f"The user asked: '{processed_prompt}'. Command output: {tool_output}. Confirm the execution proudly as if by magic!"
            elif route == "web_search":
                llm_prompt = f"The user asked: '{processed_prompt}'. Web search results: {tool_output}. Synthesize this theatrically!"
            elif route in [
                "media",
                "screenshot",
                "network",
                "process",
                "power",
                "os",
                "spotify",
                "linkedin",
            ]:
                llm_prompt = f"The user asked: '{processed_prompt}'. Tool result: {tool_output}. Explain what you did dramatically!"
            elif route == "youtube":
                llm_prompt = f"The user shared a YouTube video: '{processed_prompt}'. Transcript: {tool_output}. Discuss this video theatrically!"
            elif route in ["read_file", "write_file", "push_github"]:
                llm_prompt = f"The user asked: '{processed_prompt}'. Tool result: {tool_output}. Explain what you did dramatically!"
            else:
                llm_prompt = processed_prompt

            raw_response = self.llm.query(llm_prompt)
            output_result = self.guardrails.process_output(raw_response)
            final_response = output_result["processed_response"]

        elif answer_match:
            # No tool needed, LLM already generated the answer
            raw_response = answer_match.group(1).strip()
            # History is managed automatically by OpenJarvis when context=True
            output_result = self.guardrails.process_output(raw_response)
            final_response = output_result["processed_response"]
        else:
            # Fallback if LLM didn't use XML tags correctly
            raw_response = self.llm.query(processed_prompt)
            output_result = self.guardrails.process_output(raw_response)
            final_response = output_result["processed_response"]

        # Print text to console immediately so the user can read it while the stream plays
        print(f"\n\033[96m🎭 Lady Furina: {final_response}\033[0m\n")

        # 4. Run TTS Synthesis
        success = self._synthesize_clean(final_response, speed=1.05)

        self.guardrails.log_event(
            "PIPELINE", "COMPLETE", "Transaction completed successfully."
        )
        return {
            "route": route,
            "text": final_response,
            "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
            "logs": self.guardrails.security_logs,
            "risk_score": risk_score,
        }
