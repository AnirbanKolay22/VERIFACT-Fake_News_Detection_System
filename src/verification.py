# verification_advanced.py

from sentence_transformers import SentenceTransformer, util
import re
import torch

print("Loading semantic model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------------------------------
# NEGATION AND CONTRADICTION SIGNALS
# ----------------------------------------------------

NEGATION_TERMS = [
    "not true","false","fake","no evidence","hoax",
    "denied","refuted","misleading","fabricated”"
]

# NEW death related signals
CLAIM_DEATH_TERMS = [
    "died","dead","killed","assassinated",
    "passed away","murdered","shot dead",
]

EVIDENCE_DEATH_TERMS = [
    "died","dead","death","killed","passed away",
    "body found","postmortem","funeral","cremated",
    "shot dead","murder","stabbed",
]

# signals indicating person is alive
ALIVE_TERMS=[
   "appeared","attended","addressed","visited","met",
   "spoke","leads","will lead","announced",
   "took charge","appointed","interviewed",
   "campaign","speech","will hold meeting",
]

MONTHS = [
    "january","february","march","april","may","june",
    "july","august","september","october","november","december"
]

# ----------------------------------------------------
def extract_date(text):
    text=text.lower()
    year=re.search(r"(19|20)\d{2}",text)
    month=None
    for m in MONTHS:
        if m in text:
            month=m
            break
    return (month, year.group() if year else None)

def extract_locations(text):
    return set(re.findall(r"\b[A-Z][a-z]+\b",text))

def extract_entities(text):
    return set(re.findall(r"\b[A-Z][a-z]+\b",text))

def detect_negation(text):
    return any(n in text.lower() for n in NEGATION_TERMS)


# ----------------------------------------------------
# verification engine
# ----------------------------------------------------

def verify_claim(claim,evidence_texts,trust_scores,claim_type):

    claim_vec = model.encode(claim,convert_to_tensor=True)

    claim_date = extract_date(claim)
    claim_locs = extract_locations(claim)
    claim_ent = extract_entities(claim)

    death_claim = any(t in claim.lower() for t in CLAIM_DEATH_TERMS)

    results=[]

    for i,text in enumerate(evidence_texts):

        trust=trust_scores[i]

        ev_vec=model.encode(text,convert_to_tensor=True)
        sim=util.cos_sim(claim_vec,ev_vec).item()

        ev_date=extract_date(text)
        ev_locs=extract_locations(text)
        ev_ent=extract_entities(text)

        neg=detect_negation(text)

        # -------------------------------
        # location match score
        loc_s = len(claim_locs.intersection(ev_locs))/len(claim_locs) if claim_locs else 0

        # entity overlap
        ent_s = 1 if claim_ent.intersection(ev_ent) else 0

        # -------------------------------
        # 🟥 provenance / contradiction score
        contradiction = 0
        prov = 0

        # evidence contains death info
        death_ev = any(t in text.lower() for t in EVIDENCE_DEATH_TERMS)

        if death_claim:
            if death_ev:
                prov = 1   # supporting
            else:
                contradiction = 1  # should mention death, but it doesn't

        # alive behaviour contradicts death
        if death_claim and any(t in text.lower() for t in ALIVE_TERMS):
            contradiction = 1

        # negation flag count
        if neg:
            contradiction = 1

        # -------------------------------
        # FINAL score combination
        final = (
            0.40*sim +
            0.20*trust +
            0.10*loc_s +
            0.10*ent_s +
            0.20*prov -
            0.45*contradiction
        )

        results.append({
            "evidence_text":text[:300],
            "similarity":round(sim,3),
            "trust":trust,
            "location_score":round(loc_s,3),
            "entity_score":ent_s,
            "provenance_score":prov,
            "contradiction":contradiction,
            "final_effective_score":round(final,3)
        })

    best = max(results,key=lambda x:x["final_effective_score"])
    score = best["final_effective_score"]

    # -------------------------------
    # VERDICT LOGIC
    # -------------------------------

    if best["contradiction"]==1 and score <=0.60:
        verdict="False"
    elif score>=0.65:
        verdict="True"
    else:
        verdict="Uncertain"

    return {
        "verdict":verdict,
        "confidence_score":round(score,3),
        "best_evidence":best,
        "all_scores":results
    }
