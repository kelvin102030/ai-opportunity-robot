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


def _research_text(candidate):
    """Combine research evidence into searchable text."""
    parts = [
        str(candidate.get("concept", "")),
        str(candidate.get("problem", "")),
        " ".join(map(str, candidate.get("matched_keywords", []))),
    ]

    for item in candidate.get("evidence_items", []):
        if isinstance(item, dict):
            parts.extend([
                str(item.get("title", "")),
                str(item.get("description", "")),
                str(item.get("text", "")),
            ])

    return " ".join(parts).lower()


def _research_domain(candidate):
    """Identify a narrow problem area from the available research."""
    text = _research_text(candidate)

    reconciliation_terms = (
        "reconcil", "unmatched payment", "payment mismatch",
        "transaction mismatch",
    )
    financial_record_terms = (
        "payment", "mobile money", "transaction",
        "sales record", "invoice", "receipt",
    )
    if (
        any(term in text for term in reconciliation_terms)
        and any(term in text for term in financial_record_terms)
    ):
        return "payment_reconciliation"

    if any(word in text for word in (
        "inventory", "stock management", "stock tracking",
        "stock discrepancy", "stock discrepancies", "missing products",
        "retail shop", "retailers", "shop owners",
    )):
        return "inventory"

    if any(word in text for word in (
        "clinic", "hospital", "patient waiting", "waiting time",
        "waiting times", "appointment scheduling", "appointment delays",
        "staff shortages", "patient queue",
    )):
        return "clinic_waiting"


    if any(word in text for word in (
        "customer complaint", "customer support", "support tickets",
        "complaint tracking",
    )):
        return "customer_support"

    return "general"


def _research_customer(candidate):
    domain = _research_domain(candidate)

    if domain == "inventory":
        return (
            "Owners and managers of small retail shops, provision stores, "
            "and independent merchants who track stock manually."
        )

    if domain == "clinic_waiting":
        return (
            "Managers and administrative staff at private clinics and "
            "small healthcare facilities experiencing appointment or queue delays."
        )

    if domain == "payment_reconciliation":
        return (
            "Owners and finance staff at small businesses that receive "
            "digital payments and need to match transaction records "
            "against sales, invoices, or receipts."
        )

    if domain == "customer_support":
        return (
            "Small and medium-sized businesses that receive customer complaints "
            "and need a reliable way to track and resolve them."
        )

    return None


def _research_solution(candidate):
    domain = _research_domain(candidate)

    if domain == "inventory":
        return (
            "A mobile inventory tool that records stock received and sold, "
            "alerts shop owners when items run low, and flags discrepancies "
            "for manual review. Test a simple stock ledger before adding "
            "automatic integrations."
        )

    if domain == "clinic_waiting":
        return (
            "A clinic appointment and queue-management tool that records "
            "appointments, organizes the waiting list, and gives staff a "
            "clear view of delays. Validate clinic workflows and protect "
            "patient information before handling real patient data."
        )

    if domain == "payment_reconciliation":
        return (
            "A lightweight reconciliation tool that organizes payment and "
            "sales records, highlights unmatched transactions for manual "
            "review, and produces a clear exception list. Validate supported "
            "payment sources before claiming automatic integrations."
        )

    if domain == "customer_support":
        return (
            "A lightweight complaint-tracking tool that records each issue, "
            "assigns responsibility, tracks resolution status, and reminds "
            "staff about overdue responses."
        )

    return None


def _research_revenue(candidate):
    domain = _research_domain(candidate)

    if domain == "inventory":
        return (
            "Test a monthly subscription per shop, with a basic free tier "
            "and paid stock reports or multi-user features if customers "
            "demonstrate willingness to pay."
        )

    if domain == "clinic_waiting":
        return (
            "Test a monthly subscription per clinic, priced according to "
            "staff accounts or facility size. Confirm clinic budgets, "
            "purchasing requirements, and applicable privacy obligations."
        )

    if domain == "payment_reconciliation":
        return (
            "Test a monthly subscription only after interviews establish "
            "reconciliation frequency, current costs, and willingness to pay."
        )

    if domain == "customer_support":
        return (
            "Test monthly business subscriptions with pricing based on "
            "the number of staff members or complaint volume."
        )

    return None


def _refine_research_problem(candidate):
    """Replace a generic research-cluster summary with a specific hypothesis."""
    domain = _research_domain(candidate)

    if domain == "inventory":
        return (
            "Small retailers may lose sales or money when stock records "
            "are inaccurate, products go missing, or replenishment is delayed. "
            "The frequency and financial impact need customer validation."
        )

    if domain == "clinic_waiting":
        return (
            "Clinics may struggle to coordinate appointments and patient "
            "queues when demand exceeds available staff capacity. "
            "The causes and potential benefit of scheduling tools need validation."
        )

    if domain == "payment_reconciliation":
        return (
            "Small businesses may spend time or make errors reconciling "
            "payment transactions against sales, invoices, or receipts. "
            "Confirm how often mismatches occur and the time or money they "
            "cost before treating this as a validated problem."
        )

    if domain == "customer_support":
        return (
            "Businesses may lose customer trust when complaints are not "
            "recorded, assigned, and resolved promptly. The scale and cost "
            "of this problem need validation."
        )

    return candidate.get(
        "problem",
        "Research suggests a possible customer problem that requires validation.",
    )


def _infer_customer(candidate):
    signal = candidate.get("signal", "")

    if signal == "research_concept":
        specific_customer = _research_customer(candidate)
        if specific_customer:
            return specific_customer

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

    if signal == "research_concept":
        specific_solution = _research_solution(candidate)
        if specific_solution:
            return specific_solution

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

    if signal == "research_concept":
        specific_revenue = _research_revenue(candidate)
        if specific_revenue:
            return specific_revenue

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
    """Measure research support, not commercial profitability."""
    score = candidate.get("opportunity_score")

    if (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and 0 <= score <= 100
    ):
        return round(score / 100.0, 2)

    evidence = max(0, int(candidate.get("evidence_count", 0) or 0))
    independence = float(candidate.get("source_independence", 0) or 0)
    independence = max(0.0, min(independence, 1.0))
    evidence_coverage = min(evidence / 5.0, 1.0)
    return round(evidence_coverage * 0.60 + independence * 0.40, 2)



def _calculate_opportunity_score(candidate):
    """Return a comparable 0-100 research-support score."""
    score = candidate.get("opportunity_score")

    if (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and 0 <= score <= 100
    ):
        return round(score)

    evidence = max(0, int(candidate.get("evidence_count", 0) or 0))
    independence = float(candidate.get("source_independence", 0) or 0)
    independence = max(0.0, min(independence, 1.0))
    evidence_coverage = min(evidence / 5.0, 1.0)
    return round(evidence_coverage * 60 + independence * 40)



def analyze_candidate(candidate):
    signal = candidate.get("signal", "")
    problem = candidate.get(
        "problem",
        "An unmet need or market opportunity has been identified.",
    )
    matched_keywords = candidate.get("matched_keywords", [])

    if signal == "research_concept":
        problem = _refine_research_problem(candidate)

    target_customer = _infer_customer(candidate)
    solution = _infer_solution(candidate)
    revenue_model = _infer_revenue(candidate)

    confidence = _calculate_confidence(candidate)
    opportunity_score = _calculate_opportunity_score(candidate)

    # Give research-backed opportunities readable, domain-specific titles.
    # These are hypotheses, not proof that a business will succeed.
    if signal == "research_concept":
        domain = _research_domain(candidate)

        if domain == "inventory":
            title = "Smart Inventory Management for Small Retailers"
        elif domain == "clinic_waiting":
            title = "Clinic Appointment and Queue Management"
        elif domain == "customer_support":
            title = "Customer Complaint Tracking for Small Businesses"
        elif domain == "payment_reconciliation":
            title = "Payment Reconciliation for Small Businesses"
        else:
            concept = str(candidate.get("concept", "")).strip()
            title = (
                f"Unvalidated Opportunity: {concept[:90]}"
                if concept
                else "Unvalidated Research-Backed Opportunity"
            )
    elif signal == "emerging_market":
        evidence_items = candidate.get("evidence_items", [])
        evidence_titles = [
            str(item.get("title", "")).strip()
            for item in evidence_items
            if str(item.get("title", "")).strip()
        ]
        if evidence_titles:
            title = "Research Lead: " + evidence_titles[0][:90]
        else:
            title = "Unvalidated Research Lead"
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
