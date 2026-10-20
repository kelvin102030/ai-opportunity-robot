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
    signal = candidate.get("signal", "")
    keywords = set(candidate.get("matched_keywords", []))

    customer_map = {
        "consumer_pain": "Consumers experiencing the identified problem",
        "business_automation": "Businesses with inefficient or manual processes",
        "digital_services": "Consumers and businesses adopting digital services",
        "payments_finance": "Consumers and businesses needing financial services",
        "commerce_marketplace": "Buyers, sellers, merchants, and service providers",
        "education_skills": "Students, educators, schools, and training providers",
        "health_wellness": "Patients, healthcare providers, and wellness customers",
        "agriculture_food": "Farmers, food businesses, suppliers, and buyers",
        "logistics_mobility": "Consumers and businesses with transport or delivery needs",
        "creator_media": "Creators, audiences, and media businesses",
        "employment_work": "Workers, employers, and freelancers",
        "housing_property": "Tenants, landlords, buyers, sellers, and property businesses",
        "energy_utilities": "Households and businesses using energy or utility services",
        "security_trust": "Consumers and businesses facing security, fraud, or trust problems",
        "emerging_market": "Customers and businesses entering or affected by the emerging market",
    }

    if signal in customer_map:
        return customer_map[signal]

    if any(word in keywords for word in {
        "business", "businesses", "company", "companies",
        "merchant", "merchants", "enterprise",
    }):
        return "Businesses and organizations affected by the identified opportunity"

    if any(word in keywords for word in {
        "customer", "customers", "consumer", "consumers",
        "users", "people",
    }):
        return "Consumers or users affected by the identified opportunity"

    return "People or businesses affected by the identified opportunity"


def _infer_solution(candidate):
    problem = candidate.get(
        "problem",
        "People or businesses have an unmet need that may support a better solution.",
    )

    signal = candidate.get("signal", "")

    solution_map = {
        "consumer_pain": (
            "A focused product or service that directly reduces the recurring "
            "problem identified in the research."
        ),
        "business_automation": (
            "A practical business tool or service that automates, simplifies, "
            "or improves the inefficient process identified in the research."
        ),
        "digital_services": (
            "A digital product or service that makes the identified task "
            "simpler, faster, cheaper, or more accessible."
        ),
        "payments_finance": (
            "A financial product or infrastructure service that improves the "
            "identified payment, transaction, credit, or financial workflow."
        ),
        "commerce_marketplace": (
            "A marketplace, commerce tool, or transaction service that improves "
            "the way buyers and sellers discover, transact, or exchange value."
        ),
        "education_skills": (
            "A learning, training, assessment, or education service addressing "
            "the specific unmet need identified by the research."
        ),
        "health_wellness": (
            "A healthcare or wellness service that improves access, coordination, "
            "information, monitoring, or another validated need."
        ),
        "agriculture_food": (
            "A product or service that improves an identified agricultural, food, "
            "supply, access, or coordination problem."
        ),
        "logistics_mobility": (
            "A logistics, delivery, transport, or coordination service that "
            "reduces the identified movement or delivery problem."
        ),
        "creator_media": (
            "A creator or media product that improves creation, distribution, "
            "audience growth, discovery, or monetization."
        ),
        "employment_work": (
            "A work, hiring, freelance, or employment service that addresses "
            "the identified gap between workers and opportunities."
        ),
        "housing_property": (
            "A property service that improves discovery, verification, "
            "transactions, management, or coordination."
        ),
        "energy_utilities": (
            "A service that improves access, reliability, management, "
            "distribution, or cost of energy and utility services."
        ),
        "security_trust": (
            "A security, verification, fraud-prevention, or trust service "
            "that reduces the identified risk."
        ),
        "emerging_market": (
            "A product, service, platform, or business infrastructure opportunity "
            "built around the emerging demand or market shift identified by research."
        ),
    }

    return solution_map.get(
        signal,
        "A focused product, service, platform, or business solution designed "
        f"to address this opportunity: {problem}",
    )


def _infer_revenue(candidate):
    signal = candidate.get("signal", "")

    revenue_map = {
        "consumer_pain": "Direct purchases, subscriptions, transaction fees, or premium features.",
        "business_automation": "Monthly or annual business subscriptions, usage fees, or service contracts.",
        "digital_services": "Subscriptions, transaction fees, usage charges, advertising, or premium features.",
        "payments_finance": "Transaction fees, service fees, commissions, interchange, or business subscriptions where legally permitted.",
        "commerce_marketplace": "Transaction commissions, seller fees, listing fees, subscriptions, or service charges.",
        "education_skills": "Course purchases, subscriptions, institutional contracts, or certification fees.",
        "health_wellness": "Subscriptions, service fees, institutional contracts, or partnerships, subject to applicable regulation.",
        "agriculture_food": "Transaction commissions, subscriptions, supply margins, service fees, or business contracts.",
        "logistics_mobility": "Transaction fees, delivery fees, commissions, subscriptions, or business contracts.",
        "creator_media": "Subscriptions, creator fees, commissions, advertising, sponsorships, or premium tools.",
        "employment_work": "Employer fees, recruitment fees, subscriptions, transaction fees, or premium worker services.",
        "housing_property": "Listing fees, transaction commissions, subscriptions, verification fees, or property-management contracts.",
        "energy_utilities": "Service fees, transaction margins, subscriptions, contracts, or partnerships subject to regulation.",
        "security_trust": "Subscriptions, verification fees, transaction fees, enterprise contracts, or service fees.",
        "emerging_market": "The revenue model should be selected from the validated customer, payment, pricing, and competitive evidence.",
    }

    return revenue_map.get(
        signal,
        "Subscription, transaction fees, direct sales, service fees, or business partnerships.",
    )


def _calculate_confidence(candidate):
    evidence = candidate.get("evidence_count", 0)
    independence = candidate.get("source_independence", 0)
    impact = candidate.get("impact_score", 0)
    solution_potential = candidate.get("solution_potential", 0)

    evidence_score = min(evidence / 5, 1.0)

    confidence = (
        evidence_score * 0.35
        + independence * 0.20
        + (impact / 5) * 0.20
        + (solution_potential / 5) * 0.25
    )

    return round(min(confidence, 1.0), 2)


def _calculate_opportunity_score(candidate):
    evidence = min(candidate.get("evidence_count", 0), 5)
    independence = candidate.get("source_independence", 0)
    impact = candidate.get("impact_score", 0)
    solution_potential = candidate.get("solution_potential", 0)

    score = (
        evidence * 4
        + independence * 10
        + impact * 5
        + solution_potential * 5
    )

    return round(score)


def analyze_candidate(candidate):
    signal = candidate.get("signal", "")
    problem = candidate.get(
        "problem",
        "An unmet need or market opportunity has been identified.",
    )
    matched_keywords = candidate.get("matched_keywords", [])

    target_customer = _infer_customer(candidate)
    solution = _infer_solution(candidate)
    revenue_model = _infer_revenue(candidate)

    confidence = _calculate_confidence(candidate)
    opportunity_score = _calculate_opportunity_score(candidate)

    # Avoid presenting a broad catch-all category as if it were a concrete business.
    # Use research-derived language for the display title and make the status explicit.
    if signal == "emerging_market":
        evidence_items = candidate.get("evidence_items", [])
        evidence_titles = [
            str(item.get("title", "")).strip()
            for item in evidence_items
            if str(item.get("title", "")).strip()
        ]
        if evidence_titles:
            title = "Research lead: " + evidence_titles[0][:90]
        else:
            title = "Unvalidated research lead"
    else:
        title = f"Opportunity: {_title_from_signal(signal)}"

    return OpportunityAnalysis(
        title=title,
        problem=problem,
        target_customer=target_customer,
        solution=solution,
        revenue_model=revenue_model,
        confidence=confidence,
        opportunity_score=opportunity_score,
        next_test=(
            "Validate the opportunity with independent evidence. Confirm who "
            "the buyer is, how frequently the problem occurs, what people or "
            "businesses use today, what existing solutions cost, what is missing, "
            "whether customers actually pay, and whether the solution is "
            "technically, operationally, financially, and legally feasible."
        ),
        evidence_count=candidate.get("evidence_count", 0),
        matched_keywords=matched_keywords,
    )


if __name__ == "__main__":
    test_candidate = {
        "signal": "emerging_market",
        "evidence_count": 7,
        "source_independence": 0.8,
        "impact_score": 4,
        "solution_potential": 5,
        "matched_keywords": ["growth", "demand", "market"],
        "problem": (
            "A changing market or behavior pattern may create "
            "an emerging business opportunity."
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
