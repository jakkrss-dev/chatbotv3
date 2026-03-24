from duckduckgo_search import DDGS

def search_web(query: str) -> str:
    """Searches the internet for the given query to find current, up-to-date information, news, or facts outside of the local database."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        
        formatted = []
        for r in results:
            formatted.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nURL: {r.get('href')}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search failed: {str(e)}"
