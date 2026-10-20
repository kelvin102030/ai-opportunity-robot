"""Practical, assumption-labelled business planning for discovered opportunities."""


def generate_business_plan(idea):
    signal = str(idea.get("signal", "general_opportunity"))
    problem = str(idea.get("problem", "A customer problem identified by research."))
    customer = str(idea.get("target_customer", "Customers affected by the researched problem."))
    solution = str(idea.get("solution", "A focused service that addresses the identified problem."))

    templates = {
        "telecom_problems": {
            "offer": "A guided telecom issue log and complaint-follow-up service; do not promise operator integrations until confirmed.",
            "mvp": ["Record issue, operator, date and evidence", "Track complaint reference and follow-up dates", "Store data/billing/network incident history", "Export a complaint summary", "Basic customer dashboard"],
            "revenue": ["Free basic issue log", "Optional paid setup or reporting service", "Business subscription only if interviews show willingness to pay"],
            "test": "Interview 15 users with recurring issues and ask them to demonstrate their current workaround; test a paid manual service before building integrations.",
        },
        "small_business_operations": {
            "offer": "A simple stock, sales and expense tracking service for one clearly defined type of small retailer.",
            "mvp": ["Product and stock list", "Daily sales and expense entry", "Low-stock reminders", "Simple weekly profit estimate", "CSV or spreadsheet export"],
            "revenue": ["Free pilot for first users", "Monthly subscription if users repeatedly use it", "Paid setup/onboarding where customers value assistance"],
            "test": "Interview 15 shop owners in one retail segment, observe their current stock records, and ask at least 5 to trial a simple prototype; seek paid commitments rather than verbal praise.",
        },
        "customer_service": {
            "offer": "A customer enquiry and complaint tracking service for a narrow group of local businesses.",
            "mvp": ["Capture customer enquiries", "Assign status and follow-up date", "Reusable response templates", "Basic response-time report", "Export customer history"],
            "revenue": ["Monthly business subscription", "Setup and training fee", "Higher tier for multiple staff only after demand is validated"],
            "test": "Interview 10 businesses that receive regular enquiries and compare the current cost/time of missed follow-ups with a manual pilot.",
        },
        "logistics_mobility": {
            "offer": "A narrow delivery coordination service for one location and customer segment; begin manually before building a marketplace.",
            "mvp": ["Request and track delivery", "Record pickup/drop-off and proof", "Price and delivery status log", "Issue escalation", "Daily reconciliation"],
            "revenue": ["Per-delivery service fee", "Business delivery contract", "Commission only where service responsibility and unit economics are clear"],
            "test": "Speak to 10 frequent senders and 5 delivery operators, run a small manual pilot, and measure on-time completion and cost per delivery.",
        },
    }
    selected = templates.get(signal, {
        "offer": f"A small, testable service addressing this researched problem: {problem}",
        "mvp": ["Define one customer segment and one painful use case", "Deliver the core service manually first", "Record outcomes and customer feedback", "Track costs per customer", "Add only features users repeatedly request"],
        "revenue": ["Test a one-off fee or subscription with real prospects", "Consider commission only if a transaction is actually facilitated", "Do not assume advertising or subscriptions will work without evidence"],
        "test": "Interview 15 target customers, document current alternatives and costs, offer a small pilot, and seek evidence of actual payment before scaling.",
    })

    # Explicit scenarios, not forecasts: users must replace these assumptions with validated data.
    scenarios = [
        {"paying_customers": 10, "monthly_price_ngn": 5000, "gross_monthly_revenue_ngn": 50000},
        {"paying_customers": 50, "monthly_price_ngn": 5000, "gross_monthly_revenue_ngn": 250000},
        {"paying_customers": 100, "monthly_price_ngn": 5000, "gross_monthly_revenue_ngn": 500000},
    ]
    return {
        "idea": idea,
        "business_summary": f"Serve {customer.lower()} with: {solution}",
        "problem": problem,
        "target_customer": customer,
        "offer": selected["offer"],
        "mvp": selected["mvp"],
        "revenue_model": selected["revenue"],
        "financial_assumptions": [
            "Illustration only: ₦5,000 per paying customer per month; not a market-verified price.",
            "Gross revenue excludes hosting, staff, transport, marketing, payment fees, taxes and refunds.",
            "Startup costs and break-even cannot be responsibly estimated until the delivery model and actual supplier costs are confirmed.",
        ],
        "revenue_scenarios": scenarios,
        "first_customers": customer,
        "validation_plan": [
            selected["test"],
            "Record how many people contacted, interviewed, trialled, and actually paid.",
            "Check at least three alternatives/competitors and record their prices and gaps.",
            "Continue only if observed demand and unit economics support the next test.",
        ],
        "risks": [
            "Research coverage may not represent the target customers in the launch location.",
            "Interest is not the same as willingness to pay; obtain paid-pilot evidence.",
            "Price, acquisition cost and operating cost are currently assumptions until measured.",
            "Check applicable Nigerian registration, tax, privacy and sector-specific requirements before launch.",
        ],
        "validation_status": "PRELIMINARY — validate customer demand, pricing, costs and competition before investing.",
    }


def format_business_plan(plan):
    lines = [
        "BUSINESS PLAN", "=============",
        f"Status: {plan['validation_status']}",
        f"Summary: {plan['business_summary']}",
        f"Problem: {plan['problem']}",
        f"Target customer: {plan['target_customer']}",
        f"Proposed offer: {plan['offer']}",
        "", "MVP SCOPE", "----------",
    ]
    lines.extend(f"- {item}" for item in plan["mvp"])
    lines.extend(["", "REVENUE MODEL TO TEST", "---------------------"])
    lines.extend(f"- {item}" for item in plan["revenue_model"])
    lines.extend(["", "ILLUSTRATIVE REVENUE SCENARIOS (NOT FORECASTS)", "----------------------------------------------"])
    for row in plan["revenue_scenarios"]:
        lines.append(f"- {row['paying_customers']} customers × ₦{row['monthly_price_ngn']:,}/month = ₦{row['gross_monthly_revenue_ngn']:,} gross/month")
    lines.extend(["", "FINANCIAL ASSUMPTIONS", "---------------------"])
    lines.extend(f"- {item}" for item in plan["financial_assumptions"])
    lines.extend(["", "FIRST-CUSTOMER VALIDATION PLAN", "------------------------------"])
    lines.extend(f"- {item}" for item in plan["validation_plan"])
    lines.extend(["", "RISKS", "-----"])
    lines.extend(f"- {item}" for item in plan["risks"])
    return "\n".join(lines)
