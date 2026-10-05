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


def _title_from_signal(signal):
    words = signal.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def _infer_customer(candidate):
    signal = candidate["signal"]
    keywords = set(candidate["matched_keywords"])

    if signal == "telecom_problems":
        return "Nigerian telecom customers"

    if signal == "small_business_operations":
        return "Nigerian small businesses"

    if signal == "infrastructure":
        if "road" in keywords:
            return "Businesses, residents, commuters, and local organizations"
        if "energy" in keywords:
            return "Businesses, households, and local organizations"
        if "security" in keywords:
            return "Businesses, residents, and local organizations"
        return "Businesses, residents, and local organizations"

    if signal == "customer_service":
        return "Customers and businesses that handle customer support"

    return "People and businesses affected by the problem"


def _infer_solution(candidate):
    signal = candidate["signal"]
    keywords = set(candidate["matched_keywords"])

    if signal == "telecom_problems":
        if "billing" in keywords and "data" in keywords:
            return (
                "A simple service that helps telecom customers document "
                "billing and data problems, track complaints, and prepare "
                "clear escalation requests."
            )

        if "network" in keywords or "airtime" in keywords:
            return (
                "A service that helps telecom customers record, track, "
                "and resolve recurring network, airtime, and service problems."
            )

        return (
            "A service that helps telecom customers record, track, "
            "and resolve recurring service problems."
        )

    if signal == "small_business_operations":
        if "payroll" in keywords and "recruitment" in keywords:
            return (
                "An affordable small-business operations platform that "
                "combines payroll, recruitment, and basic staff-management "
                "tools in one place."
            )

        return (
            "An affordable small-business operations platform focused on "
            "the specific operational problems identified by the research."
        )

    if signal == "infrastructure":
        if "road" in keywords:
            return (
                "A local reporting and tracking service that helps residents "
                "and businesses document road problems, report them clearly, "
                "and follow progress toward resolution."
            )

        if "energy" in keywords:
            return (
                "A local service that helps businesses and households "
                "document energy problems, compare alternatives, and track "
                "resolution or service reliability."
            )

        if "security" in keywords:
            return (
                "A local reporting and coordination service that helps "
                "businesses and residents document security problems and "
                "coordinate appropriate responses."
            )

        return (
            "A local reporting and tracking service that helps residents "
            "and businesses document infrastructure problems and follow "
            "their progress toward resolution."
        )

    if signal == "customer_service":
        if "complaint" in keywords and "satisfaction" in keywords:
            return (
                "A customer-support service that helps businesses organize "
                "complaints, identify recurring satisfaction problems, "
                "answer common questions, and track unresolved issues."
            )

        return (
            "A customer-support service that helps businesses organize "
            "complaints, answer common questions, and track unresolved "
            "customer problems."
        )

    return (
        "A focused service designed to reduce the identified problem "
        "for the people experiencing it."
    )


def _infer_revenue(candidate):
    signal = candidate["signal"]
    keywords = set(candidate["matched_keywords"])

    if signal == "telecom_problems":
        return (
            "Freemium customer service, with paid premium features, "
            "and possible partnerships with consumer-support organizations."
        )

    if signal == "small_business_operations":
        if "payroll" in keywords:
            return "Monthly subscription from small businesses, with paid payroll features."
        return "Monthly subscription from small businesses."

    if signal == "infrastructure":
        if "road" in keywords:
            return (
                "Service contracts, organizational subscriptions, "
                "or sponsored infrastructure-reporting programs."
            )
        if "energy" in keywords:
            return (
                "Business subscriptions, service contracts, "
                "or partnerships with energy-service providers."
            )
        return (
            "Service contracts, organizational subscriptions, "
            "or sponsored reporting programs."
        )

    if signal == "customer_service":
        return "Monthly subscription from businesses, with optional premium support features."

    return "Subscription, service fees, or business partnerships."

def _calculate_confidence(candidate):
    evidence = candidate["evidence_count"]
    independence = candidate["source_independence"]
    impact = candidate["impact_score"]
    solution_potential = candidate["solution_potential"]

    evidence_score = min(evidence / 5, 1.0)

    confidence = (
        evidence_score * 0.35
        + independence * 0.20
        + (impact / 5) * 0.20
        + (solution_potential / 5) * 0.25
    )

    return round(min(confidence, 1.0), 2)


def _calculate_opportunity_score(candidate):
    evidence = min(candidate["evidence_count"], 5)
    independence = candidate["source_independence"]
    impact = candidate["impact_score"]
    solution_potential = candidate["solution_potential"]

    score = (
        evidence * 4
        + independence * 10
        + impact * 5
        + solution_potential * 5
    )

    return round(score)


def analyze_candidate(candidate):
    signal = candidate["signal"]
    problem = candidate["problem"]
    matched_keywords = candidate["matched_keywords"]

    target_customer = _infer_customer(candidate)
    solution = _infer_solution(candidate)
    revenue_model = _infer_revenue(candidate)

    confidence = _calculate_confidence(candidate)
    opportunity_score = _calculate_opportunity_score(candidate)

    return OpportunityAnalysis(
        title=f"Opportunity: {_title_from_signal(signal)}",
        problem=problem,
        target_customer=target_customer,
        solution=solution,
        revenue_model=revenue_model,
        confidence=confidence,
        opportunity_score=opportunity_score,
        next_test=(
            "Interview people affected by this problem. Confirm how often "
            "it happens, how painful it is, what they currently use, "
            "what is missing from existing solutions, and whether they "
            "would pay for a better solution."
        ),
        evidence_count=candidate["evidence_count"],
        matched_keywords=matched_keywords,
    )


if __name__ == "__main__":
    test_candidate = {
        "signal": "customer_service",
        "evidence_count": 7,
        "source_independence": 1.0,
        "impact_score": 2,
        "solution_potential": 5,
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
    print("Opportunity score:", result.opportunity_score)
    print("Next test:", result.next_test)
