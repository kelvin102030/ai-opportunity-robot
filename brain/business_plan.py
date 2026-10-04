from brain.ideas import generate_idea
from brain.opportunities import generate_candidates
from brain.research import collect_research


def generate_business_plan(idea):
    if idea["signal"] == "telecom_problems":
        return {
            "idea": idea,
            "mvp": [
                "Billing and data-usage monitoring",
                "Telecom complaint tracking",
                "Network and service issue reporting",
                "Alerts for unusual billing or data activity",
                "Simple customer dashboard",
            ],
            "revenue_model": "Monthly subscription for consumers and small businesses, with higher tiers for advanced monitoring and reporting.",
            "first_customers": "Consumers and small businesses that frequently experience telecom billing, data, or network problems.",
            "validation_plan": [
                "Interview 15 telecom users about their most frequent billing, data, and network problems.",
                "Identify the three most painful problems customers would pay to solve.",
                "Build a simple prototype for tracking complaints and telecom issues.",
                "Test whether users would pay for monitoring or faster problem resolution.",
            ],
            "risks": [
                "Telecom operators may already provide some support features.",
                "Access to telecom account and usage data may be limited.",
                "Customers may not pay for a problem they can currently report for free.",
            ],
        }

    return {
        "idea": idea,
        "mvp": [
            "Simple problem-tracking workflow",
            "Customer issue collection",
            "Basic dashboard",
        ],
        "revenue_model": "Monthly subscription based on business size and usage.",
        "first_customers": idea["target_customer"],
        "validation_plan": [
            "Interview potential customers about the problem.",
            "Identify the most painful recurring issue.",
            "Build a simple prototype.",
            "Test whether customers would pay for the solution.",
        ],
        "risks": [
            "Customers may prefer existing alternatives.",
            "The problem may not be painful enough to pay to solve.",
            "The solution may require data or integrations that are difficult to access.",
        ],
    }


if __name__ == "__main__":
    research = collect_research()
    candidates = generate_candidates(research)

    if not candidates:
        print("No business opportunities found.")
        raise SystemExit(0)

    idea = generate_idea(candidates[0])
    plan = generate_business_plan(idea)

    print("BUSINESS PLAN")
    print("=============")
    print()
    print(f"Idea: {idea['solution']}")
    print()
    print(f"Target customer: {idea['target_customer']}")
    print()

    print("MVP")
    print("---")
    for item in plan["mvp"]:
        print(f"- {item}")

    print()
    print("REVENUE MODEL")
    print("-------------")
    print(plan["revenue_model"])

    print()
    print("FIRST CUSTOMERS")
    print("----------------")
    print(plan["first_customers"])

    print()
    print("VALIDATION PLAN")
    print("----------------")
    for step in plan["validation_plan"]:
        print(f"- {step}")

    print()
    print("RISKS")
    print("-----")
    for risk in plan["risks"]:
        print(f"- {risk}")
