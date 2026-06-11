import subprocess
import psutil
import webbrowser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

class AgentTools:
    def __init__(self):
        pass

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
                searxng_url, 
                params={"q": query, "format": "json"}, 
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", [])[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("url", ""),
                        "body": item.get("content", "")
                    })
                print("SearXNG search succeeded.")
        except Exception as e:
            print(f"SearXNG search failed/offline: {e}. Falling back to DuckDuckGo HTML...")

        # 2. Fallback to keyless DDG HTML scraper
        if not results:
            ddg_url = "https://html.duckduckgo.com/html/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            try:
                response = requests.get(
                    ddg_url, 
                    params={"q": query}, 
                    headers=headers, 
                    timeout=8
                )
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for result_div in soup.find_all("div", class_="result"):
                        if len(results) >= max_results:
                            break
                        title_tag = result_div.find("a", class_="result__url")
                        snippet_tag = result_div.find("a", class_="result__snippet")
                        if title_tag:
                            title = title_tag.get_text(strip=True)
                            href = title_tag.get("href")
                            
                            # Parse DDG redirect links
                            if href and "uddg=" in href:
                                parsed = urlparse(href)
                                qs = parse_qs(parsed.query)
                                if "uddg" in qs:
                                    href = qs["uddg"][0]
                                    
                            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                            results.append({
                                "title": title,
                                "href": href,
                                "body": snippet
                            })
                    print(f"DuckDuckGo HTML scraper fetched {len(results)} results.")
            except Exception as e:
                print(f"DuckDuckGo HTML scraper failed: {e}")

        # Format results
        if not results:
            return "No search results found."
            
        results_text = []
        for i, r in enumerate(results):
            results_text.append(
                f"[{i+1}] Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n"
            )
        return "\n".join(results_text)

    def get_system_metrics(self) -> str:
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
        try:
            if executable == "start":
                url = args[0] if args else "https://google.com"
                webbrowser.open(url)
                return "Opened default web browser."

            cmd = [executable]
            if args:
                cmd.extend(args)

            # Detect GUI applications to run them asynchronously
            gui_apps = ["notepad.exe", "calc.exe", "taskmgr.exe", "explorer.exe", "opera.exe"]
            is_gui = any(gui in executable.lower() for gui in gui_apps)

            if is_gui:
                subprocess.Popen(cmd, shell=False)
                return f"Successfully launched {executable}."
            else:
                # Capture terminal/console outputs for diagnostic tools (ping, netstat, nmap)
                # Run command natively with shell=False for security and parameter safety
                result = subprocess.run(
                    cmd,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
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
