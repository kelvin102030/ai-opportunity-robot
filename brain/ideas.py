from brain.opportunities import generate_candidates
from brain.research import collect_research


SOLUTION_TEMPLATES = {
    "customer_service": {
        "target_customer": "Small and medium-sized businesses that handle frequent customer questions and complaints.",
        "solution": "An AI customer-service assistant that handles common questions, complaints, and follow-ups.",
    },
    "telecom_problems": {
        "target_customer": "Consumers and small businesses that depend heavily on reliable telecom services.",
        "solution": "A telecom support and monitoring service that helps customers track billing, data usage, and service problems.",
    },
    "small_business_operations": {
        "target_customer": "Small businesses that struggle with visibility, payroll, and recruitment.",
        "solution": "A lightweight business operations platform that combines visibility, payroll support, and recruitment workflows.",
    },
    "infrastructure": {
        "target_customer": "Businesses whose operations are affected by infrastructure and operating conditions.",
        "solution": "A business resilience service that helps companies monitor operational risks and plan around infrastructure disruptions.",
    },
    "business_costs": {
        "target_customer": "Small businesses under pressure from rising operating costs.",
        "solution": "A cost-monitoring and optimization tool that helps businesses identify unnecessary expenses and protect margins.",
    },
}


def generate_idea(candidate):
    signal = candidate["signal"]

    template = SOLUTION_TEMPLATES.get(
        signal,
        {
            "target_customer": "Customers affected by this problem.",
            "solution": "A focused service designed to reduce this problem.",
        },
    )

    return {
        "signal": signal,
        "problem": candidate["problem"],
        "target_customer": template["target_customer"],
        "solution": template["solution"],
        "opportunity_score": candidate["opportunity_score"],
        "evidence_count": candidate["evidence_count"],
        "source_diversity": candidate["source_diversity"],
        "source_independence": candidate["source_independence"],
        "confidence": candidate["confidence"],
        "impact_score": candidate["impact_score"],
        "solution_potential": candidate["solution_potential"],
        "matched_keywords": candidate["matched_keywords"],
    }


if __name__ == "__main__":
    research = collect_research()
    candidates = generate_candidates(research)

    if not candidates:
        print("No business opportunities found.")
        raise SystemExit(0)

    top_candidate = candidates[0]
    idea = generate_idea(top_candidate)

    print("BUSINESS OPPORTUNITY")
    print("====================")
    print(f"Opportunity: {idea['signal']}")
    print(f"Score: {idea['opportunity_score']}")
    print()
    print(f"Problem: {idea['problem']}")
    print()
    print(f"Target customer: {idea['target_customer']}")
    print()
    print(f"Potential solution: {idea['solution']}")
    print()
    print("Evidence")
    print("--------")
    print(f"Research items: {idea['evidence_count']}")
    print(f"Source diversity: {idea['source_diversity']}")
    print(f"Source independence: {idea['source_independence']:.2f}")
    print(f"Confidence: {idea['confidence']}")
    print(f"Impact: {idea['impact_score']}/5")
    print(f"Solution potential: {idea['solution_potential']}/5")
    print(f"Signals: {', '.join(idea['matched_keywords'])}")
