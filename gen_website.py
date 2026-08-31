"""
Search DuckDuckGo for one or more queries/website names and open the first
result for each in the default web browser.

Usage:
    python duckduckgo_search_open.py "openai, github, python.org"
    python duckduckgo_search_open.py "openai" "github" "python.org"
    (or just run it and type comma-separated names when prompted)

Requires:
    pip install requests beautifulsoup4
"""

import sys
import time
import webbrowser
import requests
from bs4 import BeautifulSoup
from gen_speak import gen_voice_package as vpkg

class gen_web_open:
    def __init__(self, web):
        self.web = web
    
    
    def search_duckduckgo(query: str) -> list[str]:
        HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    
        SEARCH_URL = "https://html.duckduckgo.com/html/"

        """Return a list of result URLs for the given query, in order."""
        params = {"q": query}
        response = requests.post(SEARCH_URL, data=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
    
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
    
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href:
                links.append(href)
    
        return links
    
    
    def open_first_result(query: str, delay: float = 1.5) -> None:
        print(f"Searching DuckDuckGo for: {query!r} ...")
        try:
            results = gen_web_open.search_duckduckgo(query)
        except requests.RequestException as e:
            print(f"  Error searching for {query!r}: {e}")
            return
    
        if not results:
            print(f"  No results found for {query!r}.")
            return
    
        first_url = results[0]
        print(f"  Opening first result: {first_url}")
        webbrowser.open(first_url)
        time.sleep(delay)  # avoid overwhelming DuckDuckGo / the browser
    
    
    def parse_queries(raw_args: list[str]) -> list[str]:
        """
        Turn CLI args or a single input string into a clean list of queries.
        Supports comma-separated input either as one arg or across multiple args.
        """
        joined = " ".join(raw_args)
        # Split on commas; fall back to the whole string if no commas were used
        parts = [p.strip() for p in joined.split(",")]
        return [p for p in parts if p]
    
    
    def main(self):
        if len(sys.argv) > 1:
            queries = gen_web_open.parse_queries(sys.argv[1:])
        else:
            raw = self.web 
            queries = gen_web_open.parse_queries([raw])
    
        if not queries:
            print("No query provided. Exiting.")
            vpkg.gen_jarvis_eng('No query provided. Exiting.')
            return
    
        for query in queries:
            vpkg.gen_jarvis_eng('opening' + query)
            gen_web_open.open_first_result(query)
            vpkg.gen_jarvis_eng('  all sorted as you requested sir')
    
