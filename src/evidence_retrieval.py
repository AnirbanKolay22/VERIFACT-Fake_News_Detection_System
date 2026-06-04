# ret_prod01.py

import os
import re
import csv
import requests
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup

# -----------------------------------------------
# optional embedding
# -----------------------------------------------
try:
    from sentence_transformers import SentenceTransformer, util
    MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    EMBED = True
except:
    EMBED = False


# -----------------------------------------------
# CONSTANTS
# -----------------------------------------------

NEWSIO_KEY = "YOUR_NEWSDATA_IO_API_KEY"
GNEWS_KEY  = "YOUR_GNEWS_API_KEY"
GOOGLE_FACT_KEY = "YOUR_GOOGLE_FACT_CHECK_API_KEY"

HEADERS = {"User-Agent":"Mozilla/5.0 fact-checker"}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOCAL_CSV = os.path.join(BASE_DIR,"local_evidence.csv")


STOPWORDS = {
    "is","are","was","were","a","an","the","to","in","on","by",
    "of","and","for","from","with","it","this","that","has",
}


EVENT_PATTERNS = [
    "died","dead","killed","visit","visited","arrived","landed",
    "tour","attack","explosion","concert","came to","event",
    "announced","declared","appeared","met","presented"
]


# -----------------------------------------------
# util functions
# -----------------------------------------------

def extract_keywords(claim):
    words=re.findall(r"[A-Za-z]+",claim.lower())
    return [w for w in words if w not in STOPWORDS][:4]


def classify_claim(claim):
    t=claim.lower()
    if any(p in t for p in EVENT_PATTERNS):
        return "event"
    return "fact"


# -----------------------------------------------
# save local archive
# -----------------------------------------------

def update_local_csv(claim,ev):
    exists=os.path.exists(LOCAL_CSV)
    with open(LOCAL_CSV,"a",newline="",encoding="utf8") as f:
        w=csv.writer(f)
        if not exists:
            w.writerow(["timestamp","claim","source","text","trust"])
        w.writerow([
            datetime.utcnow().isoformat(),
            claim,
            ev["source"],
            ev["text"],
            ev["trust"],
        ])


# -----------------------------------------------
# EVENT SEARCH – NEWSDATA.IO
# -----------------------------------------------

def search_newsio(claim):

    evidences=[]
    q="+".join(extract_keywords(claim))

    url=f"https://newsdata.io/api/1/latest?apikey={NEWSIO_KEY}&q={q}&language=en"

    try:
        r=requests.get(url,headers=HEADERS,timeout=8)
        js=r.json()

        for art in js.get("results",[])[:10]:
            txt=(art.get("title","")+" "+art.get("description",""))
            evidences.append({
                "source":art.get("source_id","newsio"),
                "text":txt,
                "trust":0.70
            })
    except:
        pass

    return evidences



# -----------------------------------------------
# EVENT SEARCH – GNEWS
# -----------------------------------------------

def search_gnews(claim):

    evidences=[]
    q=" ".join(extract_keywords(claim))

    params={
        "q":q,
        "lang":"en",
        "max":10,
        "token":GNEWS_KEY
    }

    try:
        r=requests.get("https://gnews.io/api/v4/search",
                       headers=HEADERS,params=params,timeout=8)

        for art in r.json().get("articles",[]):
            txt=(art.get("description","")+" "+art.get("content",""))
            evidences.append({
                "source":art.get("source",{}).get("name","gnews"),
                "text":txt,
                "trust":0.85
            })
    except:
        pass

    return evidences



# -----------------------------------------------
# FACT SOURCE – GOOGLE FACT CHECK
# -----------------------------------------------

def search_google_factcheck(claim):

    evidences=[]
    q=urllib.parse.quote(claim)

    url=f"https://factchecktools.googleapis.com/v1alpha1/claims:search?key={GOOGLE_FACT_KEY}&query={q}"

    try:
        r=requests.get(url,timeout=8)
        js=r.json()

        for c in js.get("claims",[])[:8]:
            txt=c.get("text","")+" "+c.get("claimReview",[{}])[0].get("title","")
            evidences.append({
                "source":"google_fact_check",
                "text":txt,
                "trust":0.90
            })
    except:
        pass

    return evidences



# -----------------------------------------------
# FACT SOURCE – WIKIPEDIA
# -----------------------------------------------

def search_wiki(claim):

    evidences=[]
    params={
        "action":"query",
        "list":"search",
        "srsearch":claim,
        "format":"json"
    }

    try:
        r=requests.get("https://en.wikipedia.org/w/api.php",
                       params=params,headers=HEADERS,timeout=8)

        for hit in r.json().get("query",{}).get("search",[])[:6]:
            title = hit["title"]

            page=requests.get(
                f"https://en.wikipedia.org/wiki/{title.replace(' ','_')}",
                headers=HEADERS,timeout=8
            )
            soup=BeautifulSoup(page.text,"html.parser")
            content_div = soup.find("div", {"id": "mw-content-text"})
            if not content_div:
                continue

            # Remove tables, navboxes, references
            for tag in content_div.find_all(["table","sup","span"]):
                tag.decompose()

            text = content_div.get_text(" ", strip=True)

            # ❌ Ignore navigation garbage
            if "Jump to content" in text or len(text) < 300:
                continue

            evidences.append({
                "source":"wikipedia.org",
                "text":text[:1500],
                "trust":0.75
            })
    except:
        pass

    return evidences



# -----------------------------------------------
# RANK BY SEMANTIC SIMILARITY
# -----------------------------------------------

def rank_evidence(claim,evidences,k=10):

    if not EMBED:
        return evidences[:k]

    claim_vec = MODEL.encode(claim,convert_to_tensor=True)

    ranked=[]

    for ev in evidences:
        try:
            vec = MODEL.encode(ev["text"],convert_to_tensor=True)
            sim = util.cos_sim(claim_vec,vec).item()
            ranked.append((sim,ev))
        except:
            continue

    ranked=sorted(ranked,key=lambda x:x[0],reverse=True)
    return [ev for sim,ev in ranked[:k]]



# -----------------------------------------------
# MAIN ENTRYPOINT
# -----------------------------------------------

def retrieve_evidence(claim,k=10):

    claim_type = classify_claim(claim)

    evidences=[]

    if claim_type=="event":
        evidences+=search_newsio(claim)
        evidences+=search_gnews(claim)
    else:
        evidences+=search_google_factcheck(claim)
        evidences+=search_wiki(claim)

    if not evidences:
        return [], claim_type

    best = rank_evidence(claim,evidences,k)

    for ev in best:
        update_local_csv(claim,ev)

    return best, claim_type
