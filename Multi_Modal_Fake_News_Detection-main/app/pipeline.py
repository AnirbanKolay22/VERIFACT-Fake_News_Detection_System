import json

from src.claim_from_image import image_to_text_summary
from src.claim_from_video import extract_claim_from_video
from src.claim_from_text import summarize_text

from utils.claim_normalizer import normalize_claim_for_search,relax_query
from src.evidence_retrieval import retrieve_evidence
from src.verification import verify_claim

from src.explanation import explain_result


def process_request(payload: dict) -> dict:
    modality = payload.get("type")
    user_input = payload.get("input")

    if modality not in ["text", "image", "video"]:
        raise ValueError("Invalid modality")

    # ---------------------------
    # STAGE 1 — CLAIM EXTRACTION
    # ---------------------------
    if modality == "text":
        claim = summarize_text(user_input)

    elif modality == "image":
        img_out = image_to_text_summary(user_input)
        if img_out.get("status") == "error":
            return {
                "claim": "",
                "verdict": "Error",
                "confidence": 0.0,
                "explanation": img_out.get("summary", "Image processing failed."),
            }
        if img_out.get("status") == "non_text_image":
            return {
                "claim": "",
                "verdict": "Error",
                "confidence": 0.0,
                "explanation": img_out.get("summary")
            }
        claim = img_out.get("summary", "")

    elif modality == "video":
        vid_out = extract_claim_from_video(user_input)
        if vid_out.get("status") != "success":
            return {
                "claim": "",
                "verdict": "Error",
                "confidence": 0.0,
                "explanation": vid_out.get("reason", "Video processing failed")
            }
        claim = vid_out.get("extracted_claim", "")

    if not claim:
        return {
        "claim": "",
        "verdict": "No Claim",
        "confidence": 1.0,
        "explanation": "No factual claim was detected in the input."
        }

    print("Extracted claim:", claim)

    # ---------------------------
    # STAGE 2 — QUERY NORMALIZATION (FIXED)
    # ---------------------------
    query = normalize_claim_for_search(claim)
    # query = claim
    print("Search query:", query)

    evidences, claim_type = retrieve_evidence(query)

    if not evidences:
        relaxed_query = relax_query(query)
        print("Retrying with relaxed query:", relaxed_query)
        evidences, claim_type = retrieve_evidence(relaxed_query)

    print(f"Retrieved {len(evidences)} pieces of evidence.")
    # print("evidences:", evidences)
    if not evidences:
        return {
        "claim": claim,
        "verdict": "False",
        "confidence": 0.85,
        "explanation": (
            "No credible news or authoritative sources support this claim. "
            "Widely circulated factual claims without any reliable confirmation "
            "are likely to be false or misleading."
        ),
        "best_evidence": None,
        "claim_type": "fact"
    }

    evidence_texts = [e["text"] for e in evidences]
    trust_scores = [e["trust"] for e in evidences]

    # ---------------------------
    # STAGE 3 — VERIFICATION
    # ---------------------------
    verification = verify_claim(
        claim=query,
        evidence_texts=evidence_texts,
        trust_scores=trust_scores,
        claim_type=claim_type
    )

    verdict = verification["verdict"]
    confidence = max(0.0, min(1.0, float(verification["confidence_score"])))
    best_evidence = verification["best_evidence"].get("evidence_text", "")

    explanation = explain_result(
    claim=query,              # atomic claim
    verdict=verdict,
    confidence=confidence,
    best_evidence=best_evidence
    )

    return {
        "claim": claim,           # original user-facing claim
        "verdict": verdict,
        "confidence": confidence,
        "explanation": explanation,
        "best_evidence": best_evidence,
        "claim_type": claim_type
    }
