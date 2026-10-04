from dataclasses import dataclass


@dataclass
class OpportunityAnalysis:
    title: str
    problem: str
    target_customer: str
    solution: str
    revenue_model: str
    confidence: float
    opportunity_score: int
    next_test: str
    evidence_count: int
    matched_keywords: list


def analyze_candidate(candidate):
    signal = candidate["signal"]
    problem = candidate["problem"]
    evidence = candidate["evidence_count"]
    matched_keywords = candidate["matched_keywords"]
    opportunity_score = candidate["opportunity_score"]

    opportunity_map = {
        "customer_service": (
            "Customer service assistant for Nigerian businesses",
            "Businesses and their customers",
            "An AI customer-service assistant that handles common questions, complaints, and support requests",
            "Monthly subscription from businesses",
            0.9,
            0.9,
            0.9,
        ),
        "infrastructure": (
            "Local infrastructure problem reporting service",
            "Businesses, residents, and local organizations",
            "A service for reporting, tracking, and organizing local infrastructure problems",
            "Subscription or service contracts",
            0.7,
            0.6,
            0.7,
        ),
        "small_business_operations": (
            "Small business operations assistant",
            "Nigerian small businesses",
            "An affordable tool that helps small businesses manage visibility, payroll, and recruitment",
            "Monthly subscription",
            0.8,
            0.8,
            0.8,
        ),
        "telecom_problems": (
            "Telecom complaint and billing assistant",
            "Nigerian telecom customers",
            "A service that helps customers track billing and data problems and prepare complaints",
            "Subscription or business partnership",
            0.8,
            0.5,
            0.7,
        ),
    }

    (
        title,
        target_customer,
        solution,
        revenue_model,
        customer_score,
        monetization_score,
        solution_fit_score,
    ) = opportunity_map.get(
        signal,
        (
            f"Solution for {signal}",
            "People affected by the problem",
            "A service designed to reduce the problem",
            "Subscription or service fee",
            0.5,
            0.5,
            0.5,
        ),
    )

    evidence_score = min(evidence / 10, 1.0)

    confidence = (
        (evidence_score * 0.30)
        + (customer_score * 0.20)
        + (monetization_score * 0.25)
        + (solution_fit_score * 0.25)
    )

    confidence = round(confidence, 2)

    return OpportunityAnalysis(
        title=title,
        problem=problem,
        target_customer=target_customer,
        solution=solution,
        revenue_model=revenue_model,
        confidence=confidence,
        opportunity_score=opportunity_score,
        next_test=(
            "Talk to potential customers and determine "
            "whether the problem is frequent, painful, "
            "and worth paying to solve."
        ),
        evidence_count=evidence,
        matched_keywords=matched_keywords,
    )


if __name__ == "__main__":
    test_candidate = {
        "signal": "customer_service",
        "evidence_count": 7,
        "matched_keywords": ["customer", "complaint"],
        "problem": (
            "Customers are experiencing recurring "
            "customer-service problems."
        ),
    }

    result = analyze_candidate(test_candidate)

    print("OPPORTUNITY ANALYSIS")
    print("--------------------")
    print("Title:", result.title)
    print("Problem:", result.problem)
    print("Customer:", result.target_customer)
    print("Solution:", result.solution)
    print("Revenue:", result.revenue_model)
    print("Evidence:", result.evidence_count)
    print("Keywords:", ", ".join(result.matched_keywords))
    print("Confidence:", result.confidence)
    print("Next test:", result.next_test)
