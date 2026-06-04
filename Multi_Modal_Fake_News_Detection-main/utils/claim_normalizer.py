import re

STOP_WORDS = {
    "every","all","each","some","many","any",
    "is","are","was","were","the","a","an","of","to","in","on",
    "with","by","for","this","that","these","those","it","its"
}

def normalize_claim_for_search(text, max_chars=95):
    """
    Generic, domain-independent query normalizer.
    Preserves content words and prevents query collapse.
    """

    # 1. Take only the first sentence
    #text = re.split(r"[.;]", text)[0]

    # 2. Normalize punctuation and spacing
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    # 3. Remove stopwords but keep content
    content_words = [
        w for w in words
        if w.lower() not in STOP_WORDS
    ]

    # 4. Safety: if too aggressive, fallback to original words
    if len(content_words) < 3:
        content_words = words[:6]

    query = " ".join(content_words)

    # 5. Enforce API character limit
    if len(query) > max_chars:
        query = query[:max_chars].rsplit(" ", 1)[0]

    return query


def relax_query(query):
    """
    General fallback: removes overly specific action phrases
    while keeping named entities.
    """

    WEAK_ACTIONS = [
        "presents", "presented", "gifted", "hands over",
        "signed", "jersey", "memento", "souvenir"
    ]

    words = query.split()
    relaxed = [w for w in words if w.lower() not in WEAK_ACTIONS]

    relaxed_query = " ".join(relaxed)

    # keep it reasonable length
    if len(relaxed_query) < 20:
        return query  # fallback safety

    return relaxed_query
