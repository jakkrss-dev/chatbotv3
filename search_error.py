from duckduckgo_search import DDGS

try:
    with DDGS() as ddgs:
        results = ddgs.text("models/gemini-1.5-flash is not found for api version v1beta, or is not supported for generatecontent", max_results=3)
        for r in results:
            print(f"TITLE: {r['title']}")
            print(f"BODY: {r['body']}")
            print(f"HREF: {r['href']}")
            print("-" * 40)
except Exception as e:
    print(f"Search failed: {e}")
