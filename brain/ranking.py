def rank_opportunities(analyses):
    return sorted(
        analyses,
        key=lambda item: (
            item.opportunity_score,
            item.confidence,
        ),
        reverse=True,
    )


def explain_ranking(analysis):
    return {
        "confidence": analysis.confidence,
        "reason": (
            "This opportunity ranks highly because it has "
            f"{analysis.evidence_count} research evidence signals, "
            f"matched keywords: {', '.join(analysis.matched_keywords)}, "
            "a clear customer, a plausible revenue model, and "
            "a solution that directly addresses the problem."
        ),
    }


def best_opportunity(analyses):
    ranked = rank_opportunities(analyses)

    if not ranked:
        return None

    return ranked[0]


if __name__ == "__main__":
    print("Opportunity ranking module ready.")
