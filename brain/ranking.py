"""Rank opportunities by specificity before comparing research support."""


def _is_generic_research_lead(analysis):
    """Identify broad leads that still lack a clearly defined problem."""
    title = str(getattr(analysis, "title", "") or "").strip().lower()
    problem = str(getattr(analysis, "problem", "") or "").strip().lower()

    generic_title_prefixes = (
        "research lead:",
        "unvalidated research lead",
        "unvalidated opportunity:",
        "unvalidated research-backed opportunity",
        "emerging market",
    )

    if title.startswith(generic_title_prefixes):
        return True

    # Broad categories should not be mistaken for specific customer problems.
    generic_categories = (
        "digital services",
        "digital technology",
        "technology solutions",
        "online services",
        "online platforms",
        "internet services",
        "emerging markets",
        "market opportunities",
        "business opportunities",
        "general software",
        "payments finance",
        "financial services",
        "digital finance",
        "fintech",
        "consumer finance",
        "business finance",
        "banking services",
        "online banking",
        "commerce marketplace",
    )

    if title.startswith("opportunity:"):
        category = title.split(":", 1)[1].strip()
        if any(
            category == term or category.startswith(term + " ")
            for term in generic_categories
        ):
            return True

    generic_problem_phrases = (
        "an emerging business opportunity",
        "a changing market or behavior pattern",
        "an unmet need or market opportunity",
        "a growing digital behavior or service need",
        "a new or improved online product",
        "a possible customer problem that requires validation",
    )

    return any(phrase in problem for phrase in generic_problem_phrases)


def rank_opportunities(analyses):
    """Prefer specific opportunities, then compare their research support."""
    return sorted(
        analyses,
        key=lambda item: (
            not _is_generic_research_lead(item),
            getattr(item, "opportunity_score", 0),
            getattr(item, "evidence_count", 0),
            getattr(item, "confidence", 0),
        ),
        reverse=True,
    )


def explain_ranking(analysis):
    generic = _is_generic_research_lead(analysis)

    reason = (
        "This is a broad research lead, not yet a validated business "
        "opportunity. Investigate a specific customer problem, demand, "
        "willingness to pay, pricing, and competition before investing."
        if generic
        else
        "Prioritized as a more specific opportunity, then compared using "
        "research-support score, evidence count, and confidence. These "
        "signals do not prove profitability or customer willingness to pay."
    )

    return {
        "confidence": analysis.confidence,
        "reason": reason,
    }


def best_opportunity(analyses):
    ranked = rank_opportunities(analyses)
    return ranked[0] if ranked else None


if __name__ == "__main__":
    print("Opportunity ranking module ready.")
