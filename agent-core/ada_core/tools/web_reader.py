"""
Web Page Reader Tool for ADA.
Downloads HTML from a given URL and extracts clean, readable text.
"""
import requests
from bs4 import BeautifulSoup

def read_webpage(url: str, max_chars: int = 5000) -> str:
    """
    Downloads a webpage and extracts text using BeautifulSoup.
    Limits the return size (max_chars) to avoid flooding LLM context and prevent overload.
    Fase 3: limit scraping — callers should also limit number of pages and add delays.
    """
    if not url or not url.startswith("http"):
        return "Error: Invalid URL."

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove noisy elements
        for script_or_style in soup(["script", "style", "nav", "footer", "aside", "header"]):
            script_or_style.decompose()

        # Extract text and collapse multiple newlines
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        # Truncate text to avoid blowing out OLLAMA memory bounds
        if len(clean_text) > max_chars:
            return clean_text[:max_chars] + "... [Trunced due to token limit]"
            
        return clean_text

    except requests.exceptions.Timeout:
        return "Error: Request to the website timed out."
    except Exception as e:
        return f"Error reading webpage: {str(e)}"
