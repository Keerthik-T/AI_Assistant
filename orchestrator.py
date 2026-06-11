# orchestrator.py - UPDATED CLASS
import os
import re
from guardrails import SecurityGuardrails
from tools import AgentTools
from llm_engine import LLMEngine
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
        Cleans the response by removing physical action notations in asterisks
        and hardcodes Kokoro synthesis to explicitly use the 'af_bella' voice profile.
        """
        # Strip all physical action notations (text within asterisks) before compilation
        clean_text = re.sub(r"\*.*?\*", "", text, flags=re.DOTALL)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        if not clean_text:
            clean_text = text  # fallback if everything was stripped
        
        self.guardrails.log_event("TTS_ENGINE", "SYNTHESIS_START", "Synthesizing vocal response using voice: af_bella")
        # Hardcode the voice profile argument explicitly to 'af_bella'
        return self.tts.synthesize(clean_text, self.audio_output_path, voice="af_bella", speed=speed)

    def route_and_execute(self, prompt: str) -> dict:
        self.guardrails.security_logs = []
        self.guardrails.log_event("PIPELINE", "START", f"Processing user query: '{prompt}'")

        # Fetch active personality metadata
        from personalities import get_personality
        personality = get_personality("furina")

        prompt_lower = prompt.lower().strip()
        wake_pattern = r"\b(hello[,\s]*(archon|arkon)?|hey[,\s]*(furina|farina|forina|verena|marina|arena)?|wake[,\s]*up)\b"
        wake_match = re.search(wake_pattern, prompt_lower)

        if self.is_sleeping:
            if wake_match:
                self.is_sleeping = False
                self.guardrails.log_event("PIPELINE", "UPDATE", "Wake word detected. Furina has awakened!")
                prompt = re.sub(wake_pattern, "", prompt, flags=re.IGNORECASE).strip()
                prompt = re.sub(r"^[,\s:\-\?!]+", "", prompt).strip()
                if not prompt: prompt = "Hello"
            else:
                self.guardrails.log_event("PIPELINE", "BLOCKED", "Input ignored. Furina is currently sleeping.")
                canned_response = "*mumbles sleepily* Zzz... Address me as 'hey furina' to wake me..."
                self._synthesize_clean(canned_response)
                return {"route": "sleeping", "text": canned_response, "audio_path": "/" + self.audio_output_path.replace("\\", "/"), "logs": self.guardrails.security_logs, "risk_score": 0}
        else:
            sleep_pattern = r"\b(go[,\s]*to[,\s]*sleep|sleep[,\s]*now|good[,\s]*night)\b"
            if re.search(sleep_pattern, prompt_lower):
                self.is_sleeping = True
                canned_response = "*yawns elegantly* Good night, my dear audience! I shall retire... Zzz..."
                self._synthesize_clean(canned_response)
                return {"route": "sleeping", "text": canned_response, "audio_path": "/" + self.audio_output_path.replace("\\", "/"), "logs": self.guardrails.security_logs, "risk_score": 0}

        # 1. Run Input Guardrails
        input_result = self.guardrails.process_input(prompt)
        processed_prompt = input_result["processed_text"]
        risk_score = input_result["risk_score"]
        
        if input_result["is_blocked"]:
            canned_response = "*gasps dramatically* Access denied! You cannot bypass my grand tribunal!"
            self._synthesize_clean(canned_response)
            return {"route": "blocked", "text": canned_response, "audio_path": "/" + self.audio_output_path.replace("\\", "/"), "logs": self.guardrails.security_logs, "risk_score": risk_score}

        # 2. Intent Routing
        prompt_lower = processed_prompt.lower()
        route = "chat"
        tool_output = ""

        # Pre-compute command execution matching (for GUI apps and network tools)
        is_cmd = False
        app_to_launch = None
        args = None
        
        # Check whitelisted GUI apps
        if any(kw in prompt_lower for kw in ["open", "launch", "start", "run"]):
            for app_key in ["notepad", "calculator", "calc", "taskmgr", "explorer", "operagx"]:
                if app_key in prompt_lower:
                    app_to_launch = app_key
                    is_cmd = True
                    break
            if not is_cmd and "browser" in prompt_lower:
                app_to_launch = "browser"
                is_cmd = True

        # Check diagnostic/networking tools
        if not is_cmd:
            for tool in ["ping", "netstat", "nmap"]:
                if re.search(r'\b' + re.escape(tool) + r'\b', prompt_lower):
                    app_to_launch = tool
                    is_cmd = True
                    break

        if any(kw in prompt_lower for kw in ["system metrics", "system stats", "pc performance", "hardware"]):
            route = "pc_metrics"
            tool_output = self.tools.get_system_metrics()

        elif is_cmd:
            route = "pc_control"
            # Extract arguments
            if app_to_launch in ["browser", "operagx"]:
                url = "https://google.com"
                url_match = re.search(r"(https?://\S+|www\.\S+|\S+\.(?:com|org|net)\S*)", prompt_lower)
                if url_match:
                    url = url_match.group(1)
                    if not url.startswith("http"): url = "https://" + url
                args = [url]
            elif app_to_launch in ["ping", "netstat", "nmap"]:
                match = re.search(r'\b' + re.escape(app_to_launch) + r'\b', prompt_lower)
                if match:
                    args_str = processed_prompt[match.end():].strip()
                    args = [a for a in args_str.split() if a] if args_str else None

            cmd_validation = self.guardrails.process_command(app_to_launch, args)
            if cmd_validation["is_allowed"]:
                tool_output = self.tools.execute_pc_command(cmd_validation["executable"], cmd_validation.get("args"))
            else:
                tool_output = f"Command execution blocked: {cmd_validation['reason']}"

        elif any(kw in prompt_lower for kw in ["search web for", "search for", "duckduckgo", "news on", "news about", "what is", "who is", "research"]):
            query = processed_prompt
            fillers = ["search web for", "search for", "duckduckgo", "bring me the news on", "bring me news about", "what is the news on", "news on", "news about", "who is", "what is", "research"]
            
            for kw in fillers:
                match = re.search(r'\b' + re.escape(kw) + r'\b', query, re.IGNORECASE)
                if match:
                    parts = re.split(re.escape(match.group(0)), query, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        query = parts[1]
                        break
            
            query = query.strip().strip(",.?!:;- ")
            if not query: 
                query = processed_prompt.strip()
            
            route = "web_search"
            self.guardrails.log_event("INTENT_ROUTER", "ROUTE_MATCH", f"Matched Intent: Web Search for '{query}'")
            tool_output = self.tools.web_search(query)

        # 3. Format Response via LLM
        if route == "pc_metrics":
            llm_prompt = f"System command output: {tool_output}. Present these metrics dramatically like the Oratrice mechanics!"
        elif route == "pc_control":
            llm_prompt = f"System command output: {tool_output}. Confirm application execution proudly as if by magic!"
        elif route == "web_search":
            llm_prompt = f"Web search results: {tool_output}. Please synthesize this search information theatrically. Question: {processed_prompt}"
        else:
            llm_prompt = processed_prompt

        raw_response = self.llm.query(llm_prompt)
        output_result = self.guardrails.process_output(raw_response)
        final_response = output_result["processed_response"]

        # 4. Run TTS Synthesis
        success = self._synthesize_clean(final_response, speed=1.05)
        
        self.guardrails.log_event("PIPELINE", "COMPLETE", "Transaction completed successfully.")
        return {"route": route, "text": final_response, "audio_path": "/" + self.audio_output_path.replace("\\", "/"), "logs": self.guardrails.security_logs, "risk_score": risk_score}
