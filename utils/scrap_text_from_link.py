import requests
from bs4 import BeautifulSoup

def fetch_article_text(url: str) -> str:
    """
    Fetches main readable text from a given webpage URL.
    Returns extracted text as a single clean string, or None on failure.
    """
    print(f"Fetching article text from URL: {url}")
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts/styles and other non-content tags
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'footer', 'header', 'nav']):
            tag.decompose()

        # Try common article containers first
        targets = [
            ("article", None, None),
            ("div", "post-content", "class"),
            ("div", "entry-content", "class"),
            ("div", "article-content", "class"),
            ("div", "blog-content", "class"),
            ("div", "main-content", "id"),
        ]

        article_text = ""
        for tag, value, attr in targets:
            if attr == "class":
                container = soup.find(tag, class_=value)
            elif attr == "id":
                container = soup.find(tag, id=value)
            else:
                container = soup.find(tag)

            if container:
                article_text = container.get_text(separator="\n", strip=True)
                break

        # If nothing matched, try picking the largest text block on the page
        if not article_text:
            candidates = []
            for el in soup.find_all(['article', 'div', 'section']):
                txt = el.get_text(separator="\n", strip=True)
                # keep only candidates with some minimal content
                if len(txt) > 200:
                    candidates.append((len(txt), txt))
            if candidates:
                # choose the largest block
                candidates.sort(reverse=True)
                article_text = candidates[0][1]

        # Final fallback: entire page text
        if not article_text:
            article_text = soup.get_text(separator="\n", strip=True)

        # Cleanup: remove very short lines, but be more permissive
        cleaned = []
        for line in article_text.split("\n"):
            line = line.strip()
            if len(line) >= 40:      # less aggressive filter
                cleaned.append(line)

        result = "\n".join(cleaned).strip()

        # If still empty, return None to signal failure
        if not result:
            print("Warning: extracted text is empty after cleanup")
            return None

        return result

    except Exception as e:
        print(f"Exception while fetching article: {e}")
        return None

if __name__ == "__main__":
    test_url = "https://www.district.in/events/messi-2025-india-tour-ticket-booking"

    text = fetch_article_text(test_url)

    print("\n===== SCRAPED ARTICLE TEXT =====\n")
    print(text)
    print("\n===== END =====\n")
