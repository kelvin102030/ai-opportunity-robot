import re


def _unique_research(items):
    unique = []
    seen = set()

    for item in items:
        link = item.get("link", "").strip()
        title = item.get("title", "").strip().lower()

        key = ("link", link) if link else ("title", title)

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def _text(items):
    return " ".join(
        f"{item.get('title', '')} {item.get('description', '')}".lower()
        for item in items
    )


def _commercial_relevance(item, candidate):
    text = (
        f"{item.get('title', '')} "
        f"{item.get('description', '')}"
    ).lower()

    candidate_text = " ".join(
        [
            candidate.get("problem", ""),
            candidate.get("target_customer", ""),
            candidate.get("solution", ""),
        ]
    ).lower()

    candidate_words = {
        word
        for word in re.findall(r"[a-zA-Z]+", candidate_text)
        if len(word) >= 5
    }

    if not candidate_words:
        return False

    matches = sum(1 for word in candidate_words if word in text)

    commercial_terms = [
        "price",
        "pricing",
        "pay",
        "paid",
        "subscription",
        "customer",
        "business",
        "software",
        "service",
        "competitor",
        "alternative",
        "market",
    ]

    commercial_matches = sum(
        1 for term in commercial_terms if term in text
    )

    return (
        matches >= 2
        or (matches >= 1 and commercial_matches >= 2)
    )


def _filter_commercial_research(items, candidate):
    return [
        item
        for item in items
        if _commercial_relevance(item, candidate)
    ]


def _web_evidence_type(page):
    text = page.get("text", "").lower()

    evidence = {
        "vendor": False,
        "pricing": False,
        "payment": False,
        "competition": False,
        "unmet_need": False,
    }

    vendor_terms = [
        "customer service software",
        "customer support software",
        "customer experience software",
        "crm software",
        "customer service platform",
        "customer support platform",
        "call center",
        "contact center",
        "customer experience platform",
    ]

    pricing_terms = [
        "pricing",
        "price",
        "per month",
        "per year",
        "monthly",
        "annual",
        "subscription",
        "plan",
        "starts at",
        "from $",
        "from ₦",
    ]

    payment_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "paying customers",
        "customers pay for",
        "customers are paying",
        "businesses pay for",
        "businesses are paying",
        "companies pay for",
        "companies are paying",
        "customer purchased",
        "customers purchased",
        "company purchased",
        "companies purchased",
        "signed a contract",
        "won a contract",
        "contract awarded",
        "paid subscription",
        "paying subscriber",
        "paying subscribers",
    ]

    unmet_need_terms = [
        "complaint",
        "complaints",
        "poor service",
        "unresolved",
        "frustrated",
        "problem",
        "problems",
        "challenge",
        "challenges",
        "lack of",
        "dissatisfied",
    ]

    evidence["vendor"] = any(term in text for term in vendor_terms)
    evidence["pricing"] = any(term in text for term in pricing_terms)
    evidence["payment"] = any(term in text for term in payment_terms)
    evidence["competition"] = evidence["vendor"]
    evidence["unmet_need"] = any(
        term in text for term in unmet_need_terms
    )

    return evidence


def _commercial_evidence_breakdown(items):
    payment_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "paying customers",
        "customers pay for",
        "customers are paying",
        "businesses pay for",
        "businesses are paying",
        "companies pay for",
        "companies are paying",
    ]

    pricing_terms = [
        "pricing",
        "subscription price",
        "monthly subscription",
        "annual subscription",
        "per month",
        "per year",
        "monthly fee",
        "annual fee",
        "service fee",
        "contract value",
        "contract worth",
    ]

    competition_terms = [
        "competitor",
        "competitors",
        "alternative",
        "competing",
        "rival",
        "rivals",
        "market leader",
        "existing platform",
    ]

    unmet_need_terms = [
        "poor service",
        "poor customer service",
        "customer complaints",
        "customers complain",
        "customers struggle",
        "customers frustrated",
        "unresolved complaints",
        "unmet demand",
        "underserved",
        "lack of",
        "problem",
        "problems",
        "challenge",
        "challenges",
    ]

    breakdown = {
        "payment_evidence": 0,
        "pricing_evidence": 0,
        "competition_evidence": 0,
        "unmet_need_evidence": 0,
    }

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        validation_type = item.get("validation_type")

        # Typed targeted research gets strict evidence routing.
        if validation_type == "commercial":
            if any(term in text for term in payment_terms):
                breakdown["payment_evidence"] += 1

            if (
                any(term in text for term in pricing_terms)
                or re.search(r"₦\s?[0-9][0-9,]*(?:\.\d+)?", text)
                or re.search(r"\$\s?[0-9][0-9,]*(?:\.\d+)?", text)
            ):
                breakdown["pricing_evidence"] += 1

            if any(term in text for term in competition_terms):
                breakdown["competition_evidence"] += 1

        elif validation_type == "demand":
            if any(term in text for term in unmet_need_terms):
                breakdown["unmet_need_evidence"] += 1

        elif validation_type == "customer":
            # Customer/buyer research can support payment evidence only
            # when the result explicitly mentions actual payment.
            if any(term in text for term in payment_terms):
                breakdown["payment_evidence"] += 1

        else:
            # Preserve compatibility with existing commercial research
            # that predates validation_type metadata.
            if any(term in text for term in payment_terms):
                breakdown["payment_evidence"] += 1

            if (
                any(term in text for term in pricing_terms)
                or re.search(r"₦\s?[0-9][0-9,]*(?:\.\d+)?", text)
                or re.search(r"\$\s?[0-9][0-9,]*(?:\.\d+)?", text)
            ):
                breakdown["pricing_evidence"] += 1

            if any(term in text for term in competition_terms):
                breakdown["competition_evidence"] += 1

            if any(term in text for term in unmet_need_terms):
                breakdown["unmet_need_evidence"] += 1

    return breakdown


def _score_demand(items):
    if not items:
        return 0

    strong_terms = [
        "customers complain",
        "consumer complaints",
        "customer complaints",
        "unmet demand",
        "underserved",
        "customers struggle",
        "people struggle",
        "recurring problem",
        "repeated complaints",
    ]

    medium_terms = [
        "complaints",
        "problem",
        "problems",
        "challenge",
        "challenges",
        "difficulty",
        "difficulties",
    ]

    strong_hits = 0
    medium_hits = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(term in text for term in strong_terms):
            strong_hits += 1

        if any(term in text for term in medium_terms):
            medium_hits += 1

    score = strong_hits * 20 + medium_hits * 5

    return min(100, score)


def _score_customer(items, candidate):
    target = candidate.get("target_customer", "").strip()

    if not target:
        return 20

    target_words = {
        word.lower()
        for word in re.findall(r"[a-zA-Z]+", target)
        if len(word) >= 5
    }

    if not target_words:
        return 20

    matched_items = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(word in text for word in target_words):
            matched_items += 1

    if matched_items >= 5:
        return 80
    if matched_items >= 3:
        return 60
    if matched_items >= 1:
        return 40

    return 20


def _score_revenue(items):
    if not items:
        return 0

    strong_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "paying customers",
        "customers pay for",
        "customers are paying",
        "businesses pay for",
        "businesses are paying",
        "companies pay for",
        "companies are paying",
    ]

    pricing_terms = [
        "pricing",
        "subscription price",
        "monthly subscription",
        "annual subscription",
        "per month",
        "per year",
        "monthly fee",
        "annual fee",
        "service fee",
        "contract value",
        "contract worth",
    ]

    pricing_patterns = [
        r"₦\s?[0-9][0-9,]*(?:\.\d+)?",
        r"\$\s?[0-9][0-9,]*(?:\.\d+)?",
        r"\b[0-9][0-9,]*\s?(?:naira|dollars)\b",
    ]

    strong_hits = 0
    pricing_hits = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(term in text for term in strong_terms):
            strong_hits += 1

        if (
            any(term in text for term in pricing_terms)
            or any(re.search(pattern, text) for pattern in pricing_patterns)
        ):
            pricing_hits += 1

    if strong_hits >= 3:
        return 100
    if strong_hits == 2:
        return 85
    if strong_hits == 1:
        return 70

    if pricing_hits >= 5:
        return 60
    if pricing_hits >= 3:
        return 45
    if pricing_hits >= 1:
        return 30

    return 10

def _score_competition(items):
    if not items:
        return 0

    competition_terms = [
        "competitor",
        "competitors",
        "alternative",
        "competing",
        "rival",
        "rivals",
        "market leader",
        "existing platform",
    ]

    matched_items = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(term in text for term in competition_terms):
            matched_items += 1

    if matched_items >= 5:
        return 80
    if matched_items >= 3:
        return 60
    if matched_items >= 1:
        return 40

    return 10


def _score_build_feasibility(candidate):
    signal = candidate.get("signal", "")

    base_scores = {
        "customer_service": 75,
        "telecom_problems": 70,
        "small_business_operations": 65,
        "infrastructure": 55,
        "business_costs": 70,
    }

    return base_scores.get(signal, 60)


def _score_risk(items, candidate):
    text = _text(items)

    risk_terms = [
        "regulation",
        "regulatory",
        "lawsuit",
        "fraud",
        "security",
        "privacy",
        "licence",
        "license",
        "government approval",
    ]

    matches = sum(text.count(term) for term in risk_terms)

    base_risk = 20

    if matches >= 10:
        base_risk = 70
    elif matches >= 5:
        base_risk = 50
    elif matches >= 2:
        base_risk = 35

    if candidate.get("signal") == "infrastructure":
        base_risk += 10

    return min(base_risk, 100)


def validate_business_opportunity(
    candidate,
    research,
    commercial_research=None,
):
    items = _unique_research(research)

    commercial_raw = commercial_research or []
    commercial_items = _unique_research(commercial_raw)
    commercial_items = _filter_commercial_research(
        commercial_items,
        candidate,
    )

    demand = _score_demand(items)
    customer = _score_customer(items, candidate)
    revenue = _score_revenue(commercial_items)
    competition = _score_competition(commercial_items)
    feasibility = _score_build_feasibility(candidate)
    risk = _score_risk(items + commercial_items, candidate)
    evidence_breakdown = _commercial_evidence_breakdown(
        commercial_items
    )

    readiness = (
        demand * 0.25
        + customer * 0.15
        + revenue * 0.25
        + competition * 0.10
        + feasibility * 0.20
        + (100 - risk) * 0.05
    )

    readiness = round(readiness)

    commercial_research_failed = (
        commercial_research is not None
        and len(commercial_raw) == 0
    )

    general_research_failed = (
        research is not None
        and len(research) == 0
    )

    if commercial_research_failed or general_research_failed:
        recommendation = "RESEARCH INCOMPLETE — RETRY RESEARCH"
        research_status = "incomplete"
    elif (
        demand < 60
        or revenue < 65
        or evidence_breakdown["payment_evidence"] < 1
        or evidence_breakdown["pricing_evidence"] < 1
        or evidence_breakdown["competition_evidence"] < 1
        or evidence_breakdown["unmet_need_evidence"] < 2
    ):
        recommendation = "RESEARCH MORE BEFORE BUILDING"
        research_status = "complete"
    elif readiness >= 75:
        recommendation = "READY FOR MVP VALIDATION"
        research_status = "complete"
    else:
        recommendation = "DO NOT BUILD YET"
        research_status = "complete"

    validation_gaps = []

    if demand < 60:
        validation_gaps.append(
            "Strengthen demand evidence with repeated, specific evidence "
            "that the problem is frequent and painful."
        )

    if customer < 60:
        validation_gaps.append(
            "Clarify the paying customer and identify the specific buyer "
            "who owns the problem and budget."
        )

    if revenue < 65:
        validation_gaps.append(
            "Strengthen revenue evidence by confirming pricing, payment, "
            "or willingness-to-pay evidence."
        )

    if competition < 40:
        validation_gaps.append(
            "Research existing competitors and alternatives serving this need."
        )

    if evidence_breakdown["payment_evidence"] < 1:
        validation_gaps.append(
            "Find direct evidence that customers or businesses are paying "
            "for related solutions."
        )

    if evidence_breakdown["pricing_evidence"] < 1:
        validation_gaps.append(
            "Find concrete pricing, subscription, contract, or service-fee evidence."
        )

    if evidence_breakdown["competition_evidence"] < 1:
        validation_gaps.append(
            "Find at least one documented competitor or existing alternative."
        )

    if evidence_breakdown["unmet_need_evidence"] < 2:
        validation_gaps.append(
            "Find more evidence of unresolved problems, complaints, "
            "frustration, or unmet demand."
        )

    if not validation_gaps:
        validation_gaps.append(
            "No major validation gaps detected; proceed to the next validation stage."
        )

    return {
        "demand": demand,
        "customer": customer,
        "revenue": revenue,
        "competition": competition,
        "build_feasibility": feasibility,
        "risk": risk,
        "readiness": readiness,
        "recommendation": recommendation,
        "evidence_breakdown": evidence_breakdown,
        "validation_gaps": validation_gaps,
        "research_status": research_status,
        "research_count": len(items),
        "commercial_research_count": len(commercial_items),
    }
