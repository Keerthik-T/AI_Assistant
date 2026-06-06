import os
from guardrails import SecurityGuardrails
from tools import AgentTools
from llm_engine import LLMEngine
from tts_engine import TTSEngine

class FurinaOrchestrator:
    def __init__(self, tts_model_ready=False):
        self.guardrails = SecurityGuardrails()
        self.tools = AgentTools()
        self.llm = LLMEngine()
        # TTS Engine - lazy loads model
        self.tts = TTSEngine()
        self.audio_output_path = os.path.join("static", "response.wav")
        self.is_sleeping = True

    def route_and_execute(self, prompt: str) -> dict:
        """
        Executes the deterministic routing pipeline:
        Input -> Input Guardrails -> Intent Router -> Tool -> LLM Formatter -> Output Guardrail -> TTS.
        """
        import re

        # Clear previous transaction logs
        self.guardrails.security_logs = []
        
        self.guardrails.log_event("PIPELINE", "START", f"Processing user query: '{prompt}'")

        prompt_lower = prompt.lower().strip()
        wake_pattern = r"\b(hello[,\s]*(archon|arkon)?|hey[,\s]*(furina|farina|forina|verena|marina|arena)?|wake[,\s]*up)\b"
        wake_match = re.search(wake_pattern, prompt_lower)

        # Check if sleeping
        if self.is_sleeping:
            if wake_match:
                self.is_sleeping = False
                self.guardrails.log_event("PIPELINE", "UPDATE", "Wake word detected. Furina has awakened!")
                # Strip the wake word from the prompt
                clean_prompt = re.sub(wake_pattern, "", prompt, flags=re.IGNORECASE).strip()
                # Clean up any leading punctuation/spaces
                clean_prompt = re.sub(r"^[,\s:\-\?!]+", "", clean_prompt).strip()
                if not clean_prompt:
                    clean_prompt = "Hello"
                prompt = clean_prompt
            else:
                self.guardrails.log_event("PIPELINE", "BLOCKED", "Input ignored. Furina is currently sleeping.")
                canned_response = (
                    f"*mumbles sleepily, pulling her top hat over her eyes* Zzz... "
                    f"The Opera Epiclese is closed for the night, my dear audience... "
                    f"Address me as 'hey furina' or 'hello Archon' to wake me..."
                )
                self.tts.synthesize(canned_response, self.audio_output_path)
                return {
                    "route": "sleeping",
                    "text": canned_response,
                    "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                    "logs": self.guardrails.security_logs,
                    "risk_score": 0
                }
        else:
            # Check for sleep command when awake
            sleep_pattern = r"\b(go[,\s]*to[,\s]*sleep|sleep[,\s]*now|good[,\s]*night[,\s]*(furina|farina|forina|verena|marina|arena)?)\b"
            sleep_match = re.search(sleep_pattern, prompt_lower)
            if sleep_match:
                self.is_sleeping = True
                self.guardrails.log_event("PIPELINE", "UPDATE", "Sleep command received. Furina has gone to sleep.")
                canned_response = (
                    f"*yawns elegantly and stretches* The curtains must fall, and the spotlight dims. "
                    f"Good night, my dear audience! I shall retire to my chambers now... Zzz..."
                )
                self.tts.synthesize(canned_response, self.audio_output_path)
                return {
                    "route": "sleeping",
                    "text": canned_response,
                    "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                    "logs": self.guardrails.security_logs,
                    "risk_score": 0
                }

        # 1. Run Input Guardrails (PII, Prompt Injection, Topic Filters)
        input_result = self.guardrails.process_input(prompt)
        processed_prompt = input_result["processed_text"]
        risk_score = input_result["risk_score"]
        
        # If blocked by input guardrails, bypass routing and return dramatic canned response
        if input_result["is_blocked"]:
            block_reason = input_result["block_reason"]
            self.guardrails.log_event("PIPELINE", "HALTED", f"Blocked due to: {block_reason}")
            
            canned_response = (
                f"*gasps dramatically* Hold it right there! A security threat? "
                f"Did you truly think you could deceive the great Furina with such a trick? "
                f"This request has been denied! (*huffs and strikes a defensive pose*)"
            )
            
            # Synthesize dramatic response
            self.tts.synthesize(canned_response, self.audio_output_path)
            
            return {
                "route": "blocked",
                "text": canned_response,
                "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
                "logs": self.guardrails.security_logs,
                "risk_score": risk_score
            }

        # 2. Intent Routing (Deterministic Keyword check)
        prompt_lower = processed_prompt.lower()
        route = "chat"
        tool_output = ""

        # Check for system metrics commands
        if any(kw in prompt_lower for kw in ["system metrics", "system stats", "pc performance", "hardware"]):
            route = "pc_metrics"
            self.guardrails.log_event("INTENT_ROUTER", "ROUTE_MATCH", "Matched Intent: System Hardware Metrics")
            tool_output = self.tools.get_system_metrics()

        # Check for application launch commands
        elif any(kw in prompt_lower for kw in ["open", "launch", "start"]):
            # Simple keyword parsing for whitelisted apps
            app_to_launch = None
            for app_key in ["notepad", "calculator", "calc", "taskmgr", "explorer", "operagx"]:
                if app_key in prompt_lower:
                    app_to_launch = app_key
                    break
            
            if "browser" in prompt_lower or "web browser" in prompt_lower:
                app_to_launch = "browser"

            if app_to_launch:
                route = "pc_control"
                self.guardrails.log_event("INTENT_ROUTER", "ROUTE_MATCH", f"Matched Intent: Launch PC App ({app_to_launch})")
                
                # Check command execution guardrails and extract arguments
                args = None
                if app_to_launch == "browser" or app_to_launch == "operagx":
                    # Default URL
                    url = "https://youtube.com" if app_to_launch == "operagx" else "https://google.com"
                    # Try to extract URL from prompt
                    url_match = re.search(r"(https?://\S+|www\.\S+|\S+\.(?:com|org|net|edu|gov|mil|int)\S*)", prompt_lower)
                    if url_match:
                        found_url = url_match.group(1)
                        if not found_url.startswith("http"):
                            found_url = "https://" + found_url
                        url = found_url
                    args = [url]

                cmd_validation = self.guardrails.process_command(app_to_launch, args)
                
                if cmd_validation["is_allowed"]:
                    tool_output = self.tools.execute_pc_command(cmd_validation["executable"], cmd_validation.get("args"))
                else:
                    tool_output = f"Command execution blocked: {cmd_validation['reason']}"
            else:
                self.guardrails.log_event("INTENT_ROUTER", "ROUTE_MATCH", "Launch keyword found, but no whitelisted app specified. Routing to chat.")
                route = "chat"


        # Check for web search commands
        elif any(kw in prompt_lower for kw in ["search web for", "search for", "duckduckgo"]):
            # Extract query
            query = prompt
            for kw in ["search web for", "search for", "duckduckgo"]:
                if kw in prompt_lower:
                    idx = prompt_lower.find(kw) + len(kw)
                    query = prompt[idx:].strip()
                    break
            
            route = "web_search"
            self.guardrails.log_event("INTENT_ROUTER", "ROUTE_MATCH", f"Matched Intent: Web Search for '{query}'")
            tool_output = self.tools.web_search(query)

        # 3. Format Response using LLM Persona
        self.guardrails.log_event("LLM_ENGINE", "INFERENCE_START", f"Formatting output using Furina persona for route: {route}")
        
        # Build contextual prompt for the LLM to wrap tool execution output
        if route == "pc_metrics":
            llm_prompt = (
                f"System command output: {tool_output}. "
                f"Please present these system performance metrics to the user. "
                f"Describe them dramatically, comparing the CPU or RAM to the inner mechanics of the Oratrice Mecanique!"
            )
        elif route == "pc_control":
            if "blocked" in tool_output:
                llm_prompt = (
                    f"System command output: {tool_output}. "
                    f"Inform the user in character that their request to open an app was blocked by security guardrails. "
                    f"Be dramatic, saying that the 'legal guards' of Fontaine have intercepted the request."
                )
            else:
                llm_prompt = (
                    f"System command output: {tool_output}. "
                    f"Inform the user in character that you have successfully opened the application for them. "
                    f"Act proud and majestic, as if you summoned it by magic!"
                )
        elif route == "web_search":
            llm_prompt = (
                f"Web search results: {tool_output}. "
                f"Please synthesize this search information and explain it to the user. "
                f"Maintain your dramatic Furina persona and pretend you found it in Fontaine's great library."
            )
        else:
            # Standard chat route
            llm_prompt = processed_prompt

        # Run LLM
        raw_response = self.llm.query(llm_prompt)
        
        # 4. Run Output Guardrails
        output_result = self.guardrails.process_output(raw_response)
        final_response = output_result["processed_response"]

        # 5. Run TTS Synthesis
        self.guardrails.log_event("TTS_ENGINE", "SYNTHESIS_START", "Synthesizing vocal response...")
        # Strip asterisks (physical action text) from vocal output so it sounds natural
        tts_text = re.sub(r"\*.*?\*", "", final_response).strip()
        if not tts_text:
            tts_text = final_response # Fallback
            
        success = self.tts.synthesize(tts_text, self.audio_output_path)
        if success:
            self.guardrails.log_event("TTS_ENGINE", "SYNTHESIS_COMPLETE", "Speech saved to static/response.wav")
        else:
            self.guardrails.log_event("TTS_ENGINE", "SYNTHESIS_FAILED", "Failed to generate vocal response.")

        self.guardrails.log_event("PIPELINE", "COMPLETE", "Transaction finished successfully.")

        return {
            "route": route,
            "text": final_response,
            "audio_path": "/" + self.audio_output_path.replace("\\", "/"),
            "logs": self.guardrails.security_logs,
            "risk_score": risk_score
        }

import re
