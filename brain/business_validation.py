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


def _candidate_relevance(item, candidate):
    """Require topic-specific overlap before research affects core scores."""
    text = (
        f"{item.get('title', '')} "
        f"{item.get('description', '')}"
    ).lower()

    candidate_text = " ".join(
        str(candidate.get(field) or "")
        for field in ("problem", "target_customer", "solution")
    ).lower()

    ignored = {
        "about", "after", "again", "based", "being", "caused",
        "could", "from", "have", "into", "more", "other", "their",
        "there", "these", "those", "using", "which", "while",
        "where", "would", "your", "software", "platform", "system",
        "solution", "service", "mobile", "online", "application",
    }

    def normalize(word):
        if len(word) > 4 and word.endswith("s"):
            return word[:-1]
        return word

    candidate_words = {
        normalize(word)
        for word in re.findall(r"[a-zA-Z]+", candidate_text)
        if len(word) >= 5 and word not in ignored
    }
    evidence_words = {
        normalize(word)
        for word in re.findall(r"[a-zA-Z]+", text)
    }

    if not candidate_words:
        return False

    matches = candidate_words & evidence_words

    # A single topic term is acceptable only when the candidate has
    # just one meaningful term; otherwise require two matching terms.
    required_matches = 2 if len(candidate_words) >= 2 else 1
    return len(matches) >= required_matches


def _filter_commercial_research(items, candidate):
    return [
        item
        for item in items
        if _commercial_relevance(item, candidate)
    ]


def _web_evidence_type(page):
    """Classify page text into separate commercial research signals.

    These are text signals, not independent verification of transactions.
    """
    text = str(page.get("text", "") or "").lower()

    evidence = {
        "vendor": False,
        "pricing": False,
        "payment": False,
        "willingness_to_pay": False,
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
        "pricing", "price", "per month", "per year",
        "monthly", "annual", "subscription", "plan",
        "starts at", "from $", "from ₦",
    ]

    # Explicit statements about hypothetical future payment are not
    # evidence that a transaction has occurred.
    willingness_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "might pay",
        "intend to pay",
        "intention to pay",
        "likely to pay",
        "prepared to pay",
        "stated they would pay",
        "said they would pay",
    ]

    # These phrases are claims of existing commercial activity.
    # Their presence still does not independently verify a transaction.
    actual_payment_terms = [
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
        "signed contracts",
        "won a contract",
        "contract awarded",
        "paid subscription",
        "paid subscriptions",
        "paying subscriber",
        "paying subscribers",
        "completed a purchase",
        "completed purchases",
        "generated paid sales",
        "revenue from sales",
        "reported revenue",
    ]

    unmet_need_terms = [
        "complaint", "complaints", "poor service",
        "unresolved", "frustrated", "problem", "problems",
        "challenge", "challenges", "lack of", "dissatisfied",
    ]

    evidence["vendor"] = any(term in text for term in vendor_terms)
    evidence["pricing"] = (
        any(term in text for term in pricing_terms)
        or bool(re.search(r"₦\s?[0-9][0-9,]*(?:\.\d+)?", text))
        or bool(re.search(r"\$\s?[0-9][0-9,]*(?:\.\d+)?", text))
    )
    evidence["willingness_to_pay"] = any(
        term in text for term in willingness_terms
    )
    evidence["payment"] = any(
        term in text for term in actual_payment_terms
    )
    # A vendor page is not automatically evidence of competition.
    # Look for explicit references to competitors or alternatives.
    competition_terms = [
        "competitor",
        "competitors",
        "alternative",
        "alternatives",
        "competing product",
        "competing products",
        "competing platform",
        "competing platforms",
        "rival",
        "rivals",
        "market leader",
        "existing platform",
        "other providers",
        "other provider",
        "similar products",
        "similar services",
    ]

    evidence["competition"] = any(
        term in text for term in competition_terms
    )
    evidence["unmet_need"] = any(
        term in text for term in unmet_need_terms
    )

    return evidence


def _commercial_evidence_breakdown(items):
    """Count distinct research items containing commercial evidence signals.

    Payment evidence means a source claims actual commercial activity.
    It is not proof that the claim is accurate or independently verified.
    """
    actual_payment_terms = [
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
        "signed contracts",
        "won a contract",
        "contract awarded",
        "paid subscription",
        "paid subscriptions",
        "paying subscriber",
        "paying subscribers",
        "completed a purchase",
        "completed purchases",
        "generated paid sales",
        "revenue from sales",
        "reported revenue",
    ]

    willingness_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "might pay",
        "intend to pay",
        "intention to pay",
        "likely to pay",
        "prepared to pay",
        "stated they would pay",
        "said they would pay",
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
        "alternatives",
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
        "willingness_to_pay_evidence": 0,
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

        # Demand-only research must not establish payment or pricing.
        if validation_type == "demand":
            if any(term in text for term in unmet_need_terms):
                breakdown["unmet_need_evidence"] += 1
            continue

        if any(term in text for term in actual_payment_terms):
            breakdown["payment_evidence"] += 1

        if any(term in text for term in willingness_terms):
            breakdown["willingness_to_pay_evidence"] += 1

        if (
            any(term in text for term in pricing_terms)
            or re.search(r"₦\s?[0-9][0-9,]*(?:\.\d+)?", text)
            or re.search(r"\$\s?[0-9][0-9,]*(?:\.\d+)?", text)
        ):
            breakdown["pricing_evidence"] += 1

        if any(term in text for term in competition_terms):
            breakdown["competition_evidence"] += 1

        # Untyped results may include both commercial and problem signals.
        if validation_type not in ("commercial", "customer"):
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
    """Conservative revenue-potential score from textual research signals.

    This is not a profit forecast. Willingness to pay and published prices
    alone cannot establish that customers have actually paid.
    """
    if not items:
        return 0

    actual_payment_terms = [
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
        "signed contracts",
        "won a contract",
        "contract awarded",
        "paid subscription",
        "paid subscriptions",
        "paying subscriber",
        "paying subscribers",
        "completed a purchase",
        "completed purchases",
        "generated paid sales",
        "revenue from sales",
        "reported revenue",
    ]

    willingness_terms = [
        "willing to pay",
        "willingness to pay",
        "would pay",
        "might pay",
        "intend to pay",
        "intention to pay",
        "likely to pay",
        "prepared to pay",
        "stated they would pay",
        "said they would pay",
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

    payment_hits = 0
    willingness_hits = 0
    pricing_hits = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(term in text for term in actual_payment_terms):
            payment_hits += 1

        if any(term in text for term in willingness_terms):
            willingness_hits += 1

        if (
            any(term in text for term in pricing_terms)
            or any(re.search(pattern, text) for pattern in pricing_patterns)
        ):
            pricing_hits += 1

    # Reported commercial activity is a stronger signal, but remains
    # an unverified claim until independently checked.
    if payment_hits >= 3:
        return 75
    if payment_hits == 2:
        return 65
    if payment_hits == 1:
        return 55

    # Surveys and hypothetical intent are weaker than actual purchases.
    if willingness_hits >= 3:
        return 45
    if willingness_hits >= 1:
        return 30

    # Published prices prove that a price is quoted, not that buyers exist.
    if pricing_hits >= 3:
        return 25
    if pricing_hits >= 1:
        return 15

    return 5


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
    """
    Estimate opportunity-specific business risk.

    Generic mentions of words such as "regulation" or "security"
    should not automatically make an opportunity high risk.
    Risk is scored from stronger contextual signals instead.
    """

    high_risk_phrases = [
        "licence required",
        "license required",
        "requires a licence",
        "requires a license",
        "government approval required",
        "government approval is required",
        "regulatory approval required",
        "regulatory approval is required",
        "regulated by",
        "heavily regulated",
        "subject to regulation",
        "subject to regulatory",
        "lawsuit against",
        "legal action against",
        "fraud risk",
        "fraud risks",
        "security breach",
        "data breach",
        "privacy breach",
        "privacy law",
        "data protection law",
        "personal data regulation",
    ]

    medium_risk_phrases = [
        "regulatory requirements",
        "regulatory compliance",
        "compliance requirements",
        "security requirements",
        "privacy requirements",
        "data protection requirements",
        "licensing requirements",
        "legal requirements",
    ]

    high_hits = 0
    medium_hits = 0

    for item in items:
        text = (
            f"{item.get('title', '')} "
            f"{item.get('description', '')}"
        ).lower()

        if any(term in text for term in high_risk_phrases):
            high_hits += 1

        if any(term in text for term in medium_risk_phrases):
            medium_hits += 1

    base_risk = 20

    if high_hits >= 5:
        base_risk = 70
    elif high_hits >= 2:
        base_risk = 50
    elif high_hits >= 1:
        base_risk = 35
    elif medium_hits >= 5:
        base_risk = 35
    elif medium_hits >= 2:
        base_risk = 30

    if candidate.get("signal") == "infrastructure":
        base_risk += 10

    return min(base_risk, 100)



def _article_matches_candidate(page, candidate):
    """Return True when article text contains multiple candidate-specific terms."""
    import re

    text = str(page.get("text", "")).lower()
    if not text:
        return False

    fields = (
        "title",
        "problem",
        "signal",
        "target_customer",
        "solution",
    )

    stop_words = {
        "about", "after", "again", "also", "among", "because",
        "being", "could", "their", "there", "these", "those",
        "through", "under", "using", "where", "which", "while",
        "would", "should", "business", "businesses", "customer",
        "customers", "nigerian", "nigeria", "people", "market",
        "solution", "service", "services", "problem", "problems",
        "reducing", "reduce", "improve", "improving",
    }

    terms = set()

    for field in fields:
        value = candidate.get(field, "")
        if isinstance(value, str):
            terms.update(
                word.lower()
                for word in re.findall(r"[a-zA-Z]{4,}", value)
                if word.lower() not in stop_words
            )

    matches = {
        term for term in terms
        if term in text
    }

    # Require more than a broad market or industry mention.
    return len(matches) >= 2


def _score_article_demand(web_pages, candidate):
    """Estimate problem-signal strength from relevant article text.

    This is a research signal, not proof of market size or profitability.
    Duplicate article URLs count only once.
    """
    import re

    strong_terms = (
        "repeated complaints",
        "customers struggle",
        "businesses struggle",
        "unmet demand",
        "recurring problem",
        "mounting costs",
        "rising costs",
        "high operating costs",
        "unreliable electricity",
        "repeated failures",
    )

    medium_terms = (
        "complaint",
        "complaints",
        "problem",
        "problems",
        "challenge",
        "challenges",
        "difficulty",
        "difficulties",
        "shortage",
        "expensive",
        "unreliable",
        "high cost",
        "high costs",
        "rising prices",
        "operating costs",
        "maintenance costs",
        "struggle",
        "struggling",
        "pressure",
        "unmet need",
    )

    seen = set()
    score = 0

    for page in web_pages or []:
        text = str(page.get("text", "")).lower().strip()

        if len(text) < 300:
            continue

        if not _article_matches_candidate(page, candidate):
            continue

        identity = (
            page.get("url")
            or page.get("link")
            or page.get("title")
            or str(hash(text[:500]))
        )

        if identity in seen:
            continue

        seen.add(identity)

        strong_hits = sum(term in text for term in strong_terms)
        medium_hits = sum(term in text for term in medium_terms)

        if strong_hits:
            score += 20
        elif medium_hits:
            score += 12

    return min(100, score)


def validate_business_opportunity(
    candidate,
    research,
    commercial_research=None,
    web_evidence=None,
):
    items = _unique_research(research)
    relevant_items = [
        item for item in items
        if _candidate_relevance(item, candidate)
    ]

    commercial_raw = commercial_research or []
    commercial_items = _unique_research(commercial_raw)
    commercial_items = _filter_commercial_research(
        commercial_items,
        candidate,
    )

    snippet_demand = _score_demand(relevant_items)
    article_demand = _score_article_demand(
        web_evidence or [],
        candidate,
    )
    demand = max(snippet_demand, article_demand)
    customer = _score_customer(relevant_items, candidate)
    revenue = _score_revenue(commercial_items)
    competition = _score_competition(commercial_items)
    feasibility = _score_build_feasibility(candidate)
    risk = _score_risk(relevant_items + commercial_items, candidate)
    evidence_breakdown = _commercial_evidence_breakdown(
        commercial_items
    )

    # Analyse retrieved article text separately from search snippets.
    # A page can support several categories, but counts only once per
    # category. These are keyword signals, not proof of willingness to pay.
    web_pages = web_evidence or []
    web_evidence_breakdown = {
        "payment_evidence": 0,
        "willingness_to_pay_evidence": 0,
        "pricing_evidence": 0,
        "competition_evidence": 0,
        "unmet_need_evidence": 0,
        "vendor_evidence": 0,
        "pages_analysed": 0,
    }

    for page in web_pages:
        if not page.get("text", "").strip():
            continue

        signals = _web_evidence_type(page)
        web_evidence_breakdown["pages_analysed"] += 1

        # Only use page signals for the opportunity when the page contains
        # sufficient topic overlap. Keyword matches alone are not proof
        # of actual sales, demand, or market success.
        page_relevant = _article_matches_candidate(page, candidate)

        if page_relevant and signals["payment"]:
            web_evidence_breakdown["payment_evidence"] += 1

        if page_relevant and signals["willingness_to_pay"]:
            web_evidence_breakdown["willingness_to_pay_evidence"] += 1

        if page_relevant and signals["pricing"]:
            web_evidence_breakdown["pricing_evidence"] += 1

        if page_relevant and signals["competition"]:
            web_evidence_breakdown["competition_evidence"] += 1

        if page_relevant and signals["unmet_need"]:
            web_evidence_breakdown["unmet_need_evidence"] += 1

        if page_relevant and signals["vendor"]:
            web_evidence_breakdown["vendor_evidence"] += 1

    # Merge each category without adding web counts to search-result counts.
    # Keep the separate web breakdown so every signal remains auditable.
    for key in (
        "payment_evidence",
        "willingness_to_pay_evidence",
        "pricing_evidence",
        "competition_evidence",
        "unmet_need_evidence",
    ):
        evidence_breakdown[key] = max(
            evidence_breakdown[key],
            web_evidence_breakdown[key],
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
            "Find credible reports of actual purchases, paying customers, "
            "or awarded paid contracts. Willingness-to-pay statements and "
            "published prices alone do not establish actual payment."
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

    evidence_breakdown.setdefault("willingness_to_pay_evidence", 0)

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
        "web_evidence_breakdown": web_evidence_breakdown,
        "validation_gaps": validation_gaps,
        "research_status": research_status,
        "research_count": len(items),
        "commercial_research_count": len(commercial_items),
    }
