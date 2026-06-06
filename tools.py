import subprocess
import psutil
import webbrowser
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests

class AgentTools:
    def __init__(self):
        pass

    def web_search(self, query: str, max_results: int = 3) -> str:
        """
        Runs a web search using DuckDuckGo.
        """
        print(f"Running web search for query: '{query}'...")
        try:
            results_text = []
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                for i, r in enumerate(results):
                    results_text.append(
                        f"[{i+1}] Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n"
                    )
            
            if not results_text:
                return "No search results found."
            return "\n".join(results_text)
        except Exception as e:
            print(f"Search failed: {e}")
            return f"Alas! The search theater encountered an error: {e}"

    def get_system_metrics(self) -> str:
        """
        Gathers system hardware stats.
        """
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            
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
        """
        Launches an application safely.
        """
        try:
            # Handle special launcher commands
            if executable == "start":
                # Default browser open
                url = args[0] if args else "https://google.com"
                webbrowser.open(url)
                return "Opened default web browser."

            # Build command list
            cmd = [executable]
            if args:
                cmd.extend(args)

            # Start process in background (non-blocking)
            subprocess.Popen(cmd, shell=False)
            return f"Successfully launched {executable}."
        except Exception as e:
            return f"Failed to execute command: {e}"

# Simple sanity test when run directly
if __name__ == "__main__":
    tools = AgentTools()
    print("Agent Tools configured!")
    print(tools.get_system_metrics())
