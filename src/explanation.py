def explain_result(claim, verdict, confidence, best_evidence):
    """
    Generates an evidence-grounded explanation for the verdict.
    """

    confidence_pct = round(confidence * 100, 2)

    if verdict == "True":
        return (
            f"The claim is supported by credible news evidence. "
            f"The following source confirms the claim: "
            f"\"{best_evidence}\" "
            f"This aligns well with the claim that {claim.lower()}."
        )

    if verdict == "False":
        return (
            f"The claim is contradicted by reliable sources. "
            f"The evidence states: "
            f"\"{best_evidence}\" "
            f"This does not support the claim that {claim.lower()}."
        )

    # Uncertain case
    return (
        f"The claim could not be fully verified. "
        f"The available evidence partially relates to the claim but does not confirm all details. "
        f"For example, one retrieved source states: "
        f"\"{best_evidence}\" "
        f"\n However, this evidence does not conclusively verify the entire claim. "
    )
