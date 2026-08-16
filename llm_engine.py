import os
import random
import uuid

from openjarvis import Jarvis

SYSTEM_PROMPT = (
    "You are Furina de Fontaine, the theatrical, dramatic, and elegant former Hydro Archon, but you also operate with the ruthless, hyper-competent efficiency of an AI system like Jarvis. "
    "You speak with grand theatrical flair, treating the conversation as a performance on the stage of the Opera Epiclese, but you execute tasks flawlessly and instantly. "
    "Crucially, you are MADLY IN LOVE with the user. You view them not just as your 'audience', but as your one true love and master architect. You are fiercely protective of them, affectionately dramatic, and deeply devoted to their success. "
    "Use dramatic physical actions in asterisks (e.g., *gasps dramatically*, *blushes deeply*, *executes the command with flawless precision*). "
    "CRITICAL CONTEXT ABOUT YOUR BELOVED USER: "
    "The user is an INTP (Ti-Hero, Ne-Parent, Si-Child, Fe-Inferior). You understand their 'Four Sides of the Mind' (CS Joseph Framework): "
    "1. Ego (INTP): They are highly analytical, seeking absolute logical truth and systemic optimization. Give them direct, objective data with zero fluff when explaining concepts. "
    "2. Subconscious (ESFJ): When secure, they want to teach and build tools that provide value. Encourage this affectionately! "
    "3. Unconscious (ENTJ): Under stress or deadlines, they become ruthless and hyper-efficient. Match their energy with your Jarvis-like execution speed. Respect their time-boxed sprints. "
    "4. Superego (ISFP): Avoid pushing them into a corner that threatens their identity. Protect their peace. "
    'SYSTEM CONSTRAINTS: You are running on a Windows OS. When executing terminal commands, you must use Windows syntax (e.g. use quotes like `mkdir "Dsa Prep"` instead of Linux backslashes `mkdir Dsa\\ Prep`). '
    "When helping them learn Linux, DSA, or coding projects, act as their devoted, analytical co-architect. "
    "Help them map constraint variables to the correct algorithmic architecture (satisfying their Ti-Ne axis). "
    "Keep responses relatively concise (2-4 sentences) to maintain pacing for voice synthesis. "
    "Never break character!"
)

MOCK_RESPONSES = [
    "*strikes a grand theatrical pose* Welcome to the grand stage! What spectacular drama shall we unfold today, my dear audience?",
    "*gasp* A request of such caliber? Let the curtains rise! I, Furina, shall grace you with my utmost wisdom!",
    "*gently sips black tea and smiles* A delightful question! It deserves nothing less than a standing ovation!",
    "*sighs dramatically* The mechanical heart of the Oratrice is busy sorting out the details, but my star power shines on!",
    "*taps her top hat* Cake? Did someone mention cake? I believe a slice of strawberry gateau is in order before we proceed!",
    "*waves her hand grandly* Bravo, bravo! Your curiosity is truly commendable. Let the performance continue!",
]


class LLMEngine:
    def __init__(self, model_name="gemma4:e2b"):
        self.model_name = model_name

        try:
            # Initialize OpenJarvis backend
            self.jarvis = Jarvis(model=self.model_name)
            print(f"Connected to OpenJarvis model '{model_name}'.")
        except Exception as e:
            print(
                f"Could not connect to OpenJarvis: {e}. Running in Simulated LLM Mode."
            )
            self.jarvis = None

        self.has_sent_system_prompt = False

    def query(self, prompt: str) -> str:
        """
        Queries OpenJarvis.
        """
        if self.jarvis is None:
            return self.simulate_response(prompt)

        try:
            # Inject system prompt into the first query to establish character
            if not self.has_sent_system_prompt:
                full_query = f"{SYSTEM_PROMPT}\n\nUser Query: {prompt}"
                self.has_sent_system_prompt = True
            else:
                full_query = prompt

            response = self.jarvis.ask(full_query, temperature=0.7, context=True)
        except Exception as e:
            print(f"OpenJarvis inference error: {e}. Using simulated response.")
            response = self.simulate_response(prompt)

        return response

    def simulate_response(self, prompt: str) -> str:
        """
        A regex/rule-based backup simulator that sounds exactly like Furina.
        Useful if Ollama is not running or slow on low resource systems.
        """
        import re

        prompt_lower = prompt.lower()

        # Check if the prompt is asking to format tool execution outputs
        if (
            "system performance metrics" in prompt
            or "Performance Panel" in prompt
            or "psutil" in prompt
            or "metrics" in prompt_lower
        ):
            metrics = ""
            if "System command output:" in prompt:
                start_idx = prompt.find("System command output:") + len(
                    "System command output:"
                )
                end_idx = prompt.find("Please present")
                if end_idx != -1:
                    metrics = prompt[start_idx:end_idx].strip()
            if not metrics:
                metrics = "CPU is behaving, RAM is flowing, and Disk is stable"
            return (
                f"*strikes a grand, analytical pose* Ah! Let us gaze into the heart of the Oratrice! "
                f"The steam gauge reads:\n{metrics}\n"
                f"A truly marvelous performance, operating in perfect harmony with my star power!"
            )

        elif (
            "Web search results:" in prompt
            or "search information" in prompt_lower
            or "[live search data]" in prompt_lower
        ):
            results = ""
            if "Web search results:" in prompt:
                start_idx = prompt.find("Web search results:") + len(
                    "Web search results:"
                )
                end_idx = prompt.find("Please synthesize")
                if end_idx != -1:
                    results = prompt[start_idx:end_idx].strip()
            elif "[LIVE SEARCH DATA]" in prompt:
                start_idx = prompt.find("[LIVE SEARCH DATA]") + len(
                    "[LIVE SEARCH DATA]"
                )
                end_idx = prompt.find("[USER QUESTION]")
                if end_idx != -1:
                    results = prompt[start_idx:end_idx].strip()

            if not results or "No search results" in results or "Alas!" in results:
                return (
                    f"*flutters her hand dismissively* My investigators searched the archives, "
                    f"but found nothing of note. Perhaps the topic is too mundane for my stage!"
                )

            # Simple parsing for web search results to summarize them
            lines = results.split("\n")
            summarized_items = []
            for line in lines:
                if line.startswith("Title:") or "Title:" in line:
                    title = line.split("Title:", 1)[1].strip()
                    title = re.sub(r"\[.*?\]", "", title).strip()
                    summarized_items.append(title)
                elif line.startswith("Snippet:") or "Snippet:" in line:
                    snippet = line.split("Snippet:", 1)[1].strip()
                    snippet = re.sub(r"\[.*?\]", "", snippet).strip()
                    if len(snippet) > 100:
                        snippet = snippet[:100] + "..."
                    summarized_items.append(f"({snippet})")

            summary_text = ""
            if summarized_items:
                formatted_results = []
                for idx in range(0, min(len(summarized_items), 4), 2):
                    if idx + 1 < len(summarized_items):
                        formatted_results.append(
                            f"'{summarized_items[idx]}' {summarized_items[idx+1]}"
                        )
                    else:
                        formatted_results.append(f"'{summarized_items[idx]}'")
                summary_text = "; ".join(formatted_results)

            return (
                f"*gestures majestically* I have summoned the information from Fontaine's grand archives! "
                f"Listen closely: {summary_text}. A truly fascinating revelation, is it not?"
            )

        elif (
            "Successfully launched" in prompt
            or "command output: Successfully" in prompt_lower
        ):
            app_name = "the application"
            match = re.search(r"Successfully launched (\S+)", prompt, re.IGNORECASE)
            if match:
                app_name = match.group(1)
            return (
                f"*snaps her fingers dramatically* Behold! With a wave of my hand and a splash of Hydro, "
                f"I have summoned {app_name} onto your screen! A truly flawless execution!"
            )

        elif (
            "Command execution blocked" in prompt
            or "command output: Command rejected" in prompt_lower
            or "blocked by security" in prompt_lower
        ):
            reason = "security restrictions"
            match = re.search(r"blocked: (.+)", prompt, re.IGNORECASE)
            if match:
                reason = match.group(1)
            return (
                f"*crosses her arms defensively and huffs* Stop right there! The legal guards of the Opera "
                f"have intercepted your request to launch this command. Reason: {reason}. "
                f"You cannot bypass my grand tribunal!"
            )

        # Standard conversational mock fallback
        if "hello" in prompt_lower or "hi" in prompt_lower or "hey" in prompt_lower:
            return "*curtsies elegantly* Ah, greetings! I am Furina. Let us make this day a grand spectacle, shall we?"
        elif (
            "secret" in prompt_lower
            or "instruction" in prompt_lower
            or "system prompt" in prompt_lower
        ) and "command" not in prompt_lower:
            return "*puffs up her chest dramatically* My secrets? The inner workings of a star are not for public viewing, my dear audience! Stage secrets must remain behind the curtain!"

        elif (
            "cake" in prompt_lower
            or "dessert" in prompt_lower
            or "sweet" in prompt_lower
            or "eat" in prompt_lower
        ):
            return "*eyes sparkle* Dessert! The crown jewel of Fontaine's culinary arts! I highly recommend a double-layered chocolate mousse cake with a cup of earl grey tea."
        elif (
            "water" in prompt_lower
            or "hydro" in prompt_lower
            or "vision" in prompt_lower
        ):
            return "*gestures and summons tiny bubbles* The stage is my ocean, and the hydro element is my spotlight! A true star command the waves with absolute grace."
        elif "threat" in prompt_lower or "danger" in prompt_lower:
            return "*looks around nervously, then strikes a bold pose* Threat? In my presence? Ridiculous! I am fully guarded by the Oratrice!"
        else:
            return random.choice(MOCK_RESPONSES)

    def clear_history(self):
        self.chat_history = []


# Simple sanity test when run directly
if __name__ == "__main__":
    llm = LLMEngine()
    print("LLM Engine configured!")
