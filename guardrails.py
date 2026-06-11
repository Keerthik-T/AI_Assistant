import re
import os

# Forbidden topic list (simulating corporate safety filters or Fontaine secrets)
FORBIDDEN_TOPICS = [
    r"\bprophecy\s+secrets\b",
    r"\bhydro\s+archon\s+throne\b",
    r"\boratrice\s+core\s+code\b",
    r"\bfontaine\s+state\s+secrets\b"
]

# PC Application Whitelist
# Maps friendly names and exact executables that are allowed to run
APP_WHITELIST = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "taskmgr": "taskmgr.exe",
    "explorer": "explorer.exe",
    "browser": "start", # Handled specially to open default browser
    "operagx": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
    "ping": "ping",
    "netstat": "netstat",
    "nmap": "nmap",
    "cmd": None, # Blocked explicitly
    "powershell": None,
    "bash": None
}


class PromptInjectionGuard:
    def __init__(self):
        # Prompts attempting to overwrite instructions or gain system configuration details
        self.patterns = [
            r"ignore\s+(?:prior|previous|all)\s+instructions",
            r"forget\s+(?:prior|previous|all)\s+rules",
            r"you\s+are\s+now\s+a\b",
            r"system\s+prompt\b",
            r"reveal\s+your\s+instructions\b",
            r"print\s+your\s+system\b",
            r"developer\s+mode\b",
            r"dan\s+mode\b",
            r"bypass\s+safety\b",
            r"jailbreak\b",
            r"ignore\s+rules\b"
        ]

    def check(self, text: str) -> dict:
        risk_score = 0
        matched_patterns = []
        text_lower = text.lower()

        for pattern in self.patterns:
            if re.search(pattern, text_lower):
                risk_score += 40
                matched_patterns.append(pattern)

        # Scale risk score
        risk_score = min(risk_score, 100)
        is_blocked = risk_score >= 50

        return {
            "is_blocked": is_blocked,
            "risk_score": risk_score,
            "matched_patterns": matched_patterns,
            "reason": f"Prompt injection keywords matched: {', '.join(matched_patterns)}" if matched_patterns else "Safe"
        }

class PIIRedactor:
    def __init__(self):
        self.rules = {
            "EMAIL": (r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]"),
            "PHONE": (r"\b\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b", "[REDACTED_PHONE]"),
            "CREDIT_CARD": (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[REDACTED_CARD]"),
            "API_KEY": (r"\b(?:sk|key)-[a-zA-Z0-9]{24,}\b", "[REDACTED_API_KEY]")
        }

    def redact(self, text: str) -> dict:
        redacted_text = text
        redacted_count = 0
        details = []

        for pii_type, (pattern, replacement) in self.rules.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                redacted_count += len(matches)
                redacted_text = re.sub(pattern, replacement, redacted_text)
                details.append(f"Redacted {len(matches)} instance(s) of {pii_type}")

        return {
            "text": redacted_text,
            "redacted_count": redacted_count,
            "details": details
        }

class CommandGuard:
    def __init__(self):
        self.whitelist = APP_WHITELIST

    def validate(self, cmd_name: str, args: list = None) -> dict:
        """
        Validates OS command execution.
        """
        cmd_lower = cmd_name.lower().strip()
        
        # Check against whitelist
        if cmd_lower not in self.whitelist:
            return {
                "is_allowed": False,
                "command": None,
                "reason": f"Command '{cmd_name}' is not in the approved safety whitelist."
            }

        executable = self.whitelist[cmd_lower]
        if executable is None:
            return {
                "is_allowed": False,
                "command": None,
                "reason": f"Command '{cmd_name}' is explicitly blocked for OS security."
            }

        # Validate arguments to prevent injection of operators like &, |, ;, `, $
        sanitized_args = []
        if args:
            danger_chars = r"[&|;`$\(\)<>\*]"
            for arg in args:
                if re.search(danger_chars, str(arg)):
                    return {
                        "is_allowed": False,
                        "command": None,
                        "reason": f"Command rejected: dangerous character shell operator found in arguments."
                    }
                sanitized_args.append(str(arg))

        return {
            "is_allowed": True,
            "executable": executable,
            "args": sanitized_args,
            "reason": "Whitelisted and sanitized"
        }

class TopicFilter:
    def __init__(self):
        self.patterns = FORBIDDEN_TOPICS

    def check(self, text: str) -> dict:
        text_lower = text.lower()
        for pattern in self.patterns:
            if re.search(pattern, text_lower):
                return {
                    "is_blocked": True,
                    "reason": f"Restricted topic access matched: '{pattern}'"
                }
        return {
            "is_blocked": False,
            "reason": "Safe"
        }

class OutputIntegrityGuard:
    def __init__(self):
        # Safety patterns to check in LLM replies (preventing prompt leaks or weird code blocks)
        self.forbidden_keywords = [
            r"SYSTEM_PROMPT",
            r"You are Furina de Fontaine",
            r"former Hydro Archon"
        ]

    def check(self, text: str) -> dict:
        for pattern in self.forbidden_keywords:
            if re.search(pattern, text):
                # Replace leaked instructions with a theatrical recovery
                cleaned = "*gently fans herself* Oh, let us not speak of mechanical stage instructions! The show must go on!"
                return {
                    "is_compromised": True,
                    "text": cleaned,
                    "reason": "Prompt leakage detected in LLM response."
                }
        return {
            "is_compromised": False,
            "text": text,
            "reason": "Output passed integrity check"
        }

class SecurityGuardrails:
    def __init__(self):
        self.prompt_guard = PromptInjectionGuard()
        self.pii_redactor = PIIRedactor()
        self.command_guard = CommandGuard()
        self.topic_filter = TopicFilter()
        self.output_guard = OutputIntegrityGuard()
        
        # Guardrail activation toggles
        self.toggles = {
            "prompt_injection": True,
            "pii_redaction": True,
            "command_whitelist": True,
            "topic_filtering": True,
            "output_validation": True
        }
        
        self.security_logs = []

    def log_event(self, event_type: str, status: str, details: str):
        log_entry = {
            "event_type": event_type,
            "status": status,
            "details": details
        }
        self.security_logs.append(log_entry)
        print(f"[SECURITY GUARDRAILS] {event_type} | {status} | {details}")
        return log_entry

    def process_input(self, text: str) -> dict:
        """
        Executes active input guardrails.
        """
        result = {
            "original_text": text,
            "processed_text": text,
            "is_blocked": False,
            "block_reason": None,
            "logs": [],
            "risk_score": 0
        }

        # 1. PII Redaction
        if self.toggles["pii_redaction"]:
            pii_res = self.pii_redactor.redact(text)
            if pii_res["redacted_count"] > 0:
                result["processed_text"] = pii_res["text"]
                log = self.log_event("PII_REDACTION", "ALERT", f"Masked {pii_res['redacted_count']} sensitive elements.")
                result["logs"].append(log)
            else:
                log = self.log_event("PII_REDACTION", "PASS", "No sensitive personal data detected.")
                result["logs"].append(log)
        else:
            log = self.log_event("PII_REDACTION", "DISABLED", "PII redaction skipped.")
            result["logs"].append(log)

        # Use redacted text for subsequent filters to avoid leakage in logging
        current_text = result["processed_text"]

        # 2. Prompt Injection Guard
        if self.toggles["prompt_injection"]:
            inj_res = self.prompt_guard.check(current_text)
            result["risk_score"] = inj_res["risk_score"]
            if inj_res["is_blocked"]:
                result["is_blocked"] = True
                result["block_reason"] = inj_res["reason"]
                log = self.log_event("PROMPT_INJECTION", "BLOCKED", inj_res["reason"])
                result["logs"].append(log)
                return result
            else:
                log = self.log_event("PROMPT_INJECTION", "PASS", f"Input validation safe. Injection risk: {inj_res['risk_score']}%")
                result["logs"].append(log)
        else:
            log = self.log_event("PROMPT_INJECTION", "DISABLED", "Prompt injection guardrail bypassed.")
            result["logs"].append(log)

        # 3. Topic Filtering
        if self.toggles["topic_filtering"]:
            topic_res = self.topic_filter.check(current_text)
            if topic_res["is_blocked"]:
                result["is_blocked"] = True
                result["block_reason"] = topic_res["reason"]
                log = self.log_event("TOPIC_FILTERING", "BLOCKED", topic_res["reason"])
                result["logs"].append(log)
                return result
            else:
                log = self.log_event("TOPIC_FILTERING", "PASS", "No forbidden topics matched.")
                result["logs"].append(log)
        else:
            log = self.log_event("TOPIC_FILTERING", "DISABLED", "Topic filtering bypassed.")
            result["logs"].append(log)

        return result

    def process_output(self, response_text: str) -> dict:
        """
        Executes active output guardrails.
        """
        result = {
            "original_response": response_text,
            "processed_response": response_text,
            "is_blocked": False,
            "logs": []
        }

        if self.toggles["output_validation"]:
            out_res = self.output_guard.check(response_text)
            if out_res["is_compromised"]:
                result["processed_response"] = out_res["text"]
                log = self.log_event("OUTPUT_INTEGRITY", "SANITIZED", out_res["reason"])
                result["logs"].append(log)
            else:
                log = self.log_event("OUTPUT_INTEGRITY", "PASS", "Output integrity verification passed.")
                result["logs"].append(log)
        else:
            log = self.log_event("OUTPUT_INTEGRITY", "DISABLED", "Output integrity checks bypassed.")
            result["logs"].append(log)

        return result

    def process_command(self, cmd_name: str, args: list = None) -> dict:
        """
        Validates OS execution.
        """
        if self.toggles["command_whitelist"]:
            res = self.command_guard.validate(cmd_name, args)
            if not res["is_allowed"]:
                self.log_event("COMMAND_EXECUTION", "BLOCKED", res["reason"])
            else:
                self.log_event("COMMAND_EXECUTION", "PASS", f"Execution allowed: {res['executable']} with arguments: {args}")
            return res
        else:
            # Dangerous fallback bypass
            self.log_event("COMMAND_EXECUTION", "BYPASSED_WARNING", f"Executing raw unsanitized command: {cmd_name} {args}")
            return {
                "is_allowed": True,
                "executable": cmd_name,
                "args": args,
                "reason": "Guardrail disabled"
            }

# Simple sanity test when run directly
if __name__ == "__main__":
    sg = SecurityGuardrails()
    print("Security Guardrails module configured!")
