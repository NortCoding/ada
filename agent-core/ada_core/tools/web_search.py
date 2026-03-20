"""
Web Search Tool for ADA. Fase 3: DuckDuckGo HTML search (no API key required).
"""
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Searches DuckDuckGo via standard HTTP requests and BeautifulSoup.
    Made stealthy to bypass DuckDuckGo's IP rate limiting for live demonstrations.
    Returns a list of dictionaries with 'title' and 'url' keys.
    """
    if not query or not str(query).strip():
        return []

    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # In duckduckgo html, search results typically have class 'result__a'
        for link in soup.select("a.result__url")[:max_results]:
            href = link.get("href")
            
            # DDG somewhat obscures links, usually they start with //duckduckgo.com/l/?uddg=
            if href and href.startswith("//duckduckgo.com"):
                import urllib.parse as urlparse
                parsed = urlparse.parse_qs(urlparse.urlparse(href).query)
                if "uddg" in parsed:
                    href = parsed["uddg"][0]
            elif href and href.startswith("/l/?uddg="):
                import urllib.parse as urlparse
                parsed = urlparse.parse_qs(urlparse.urlparse("https://duckduckgo.com" + href).query)
                if "uddg" in parsed:
                    href = parsed["uddg"][0]
                    
            if href:
                results.append({
                    "title": href.split("://")[-1].split("/")[0], # Fallback title
                    "url": href,
                    "snippet": ""
                })

        return results
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]
