def _is_generic_research_lead(analysis):
    title = str(getattr(analysis, "title", "")).strip().lower()
    problem = str(getattr(analysis, "problem", "")).strip().lower()
    return title.startswith(("research lead:", "unvalidated research lead", "emerging market")) or any(
        phrase in problem for phrase in (
            "an emerging business opportunity",
            "a changing market or behavior pattern",
            "an unmet need or market opportunity",
        )
    )


def rank_opportunities(analyses):
    return sorted(
        analyses,
        key=lambda item: (
            not _is_generic_research_lead(item),
            getattr(item, "evidence_count", 0),
            getattr(item, "opportunity_score", 0),
            getattr(item, "confidence", 0),
        ),
        reverse=True,
    )


def explain_ranking(analysis):
    generic = _is_generic_research_lead(analysis)
    reason = (
        "Broad research lead only; gather evidence of a specific customer problem, demand, willingness to pay, pricing, and competition before investing."
        if generic else
        "Ranked by specificity, evidence count, opportunity score, and confidence. These signals prioritize research but do not prove profitability."
    )
    return {"confidence": analysis.confidence, "reason": reason}


def best_opportunity(analyses):
    ranked = rank_opportunities(analyses)
    return ranked[0] if ranked else None


if __name__ == "__main__":
    print("Opportunity ranking module ready.")
