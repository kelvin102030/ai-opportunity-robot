from brain.research import collect_research, collect_commercial_research, collect_web_evidence, collect_validation_research
from brain.opportunities import generate_candidates
from brain.reasoning import analyze_candidate
from brain.ranking import best_opportunity, explain_ranking
from brain.memory import initialize_memory, remember_opportunity, remember_evidence, recall_evidence
from brain.business_validation import validate_business_opportunity
from brain.build_plan import create_build_plan
from brain.build_approval import approve_mvp_build
from brain.business_plan import generate_business_plan, format_business_plan


def run_robot():
    initialize_memory()

    print("AI OPPORTUNITY ROBOT")
    print("====================")
    print("Collecting research...")

    research = collect_research()

    print("Research items:", len(research))

    candidates = generate_candidates(research)

    print("Opportunity candidates:", len(candidates))
    print()

    if not candidates:
        print("NO VALIDATED OPPORTUNITY")
        print("=========================")
        print("The research did not produce enough relevant evidence to rank a specific business opportunity.")
        print("No business plan has been presented as validated. Retry research or broaden the research queries.")
        return

    analyses = []

    for candidate in candidates:
        result = analyze_candidate(candidate)
        analyses.append(result)

        opportunity_id = remember_opportunity(
            title=result.title,
            problem=result.problem,
            solution=result.solution,
            target_customer=result.target_customer,
            revenue_potential=result.revenue_model,
            confidence=result.confidence,
            notes=(
                f"Signal: {candidate['signal']}; "
                f"Evidence: {candidate['evidence_count']}; "
                f"Matched keywords: "
                f"{', '.join(candidate['matched_keywords'])}"
            ),
        )

        for evidence in candidate["evidence_items"]:
            remember_evidence(
                opportunity_id=opportunity_id,
                query=evidence["query"],
                title=evidence["title"],
                link=evidence["link"],
                description=evidence["description"],
                published=evidence["published"],
            )

    best = best_opportunity(analyses)
    explanation = explain_ranking(best)

    best_index = analyses.index(best)

    print("Collecting commercial research...")

    commercial_candidate = {
        **best.__dict__,
        "signal": candidates[best_index]["signal"],
    }

    commercial_research = collect_commercial_research(
        commercial_candidate,
    )

    print("Commercial research items:", len(commercial_research))

    print("Collecting publisher web evidence...")
    web_evidence = collect_web_evidence(commercial_research)

    print("Publisher web pages checked:", len(web_evidence))

    if web_evidence:
        print("Accessible publisher pages:")
        for page in web_evidence:
            print(f"  - {page.get('source', '')}: {page.get('url', '')}")
    else:
        print("No accessible publisher pages found.")

    print()

    opportunity_id = remember_opportunity(
        title=best.title,
        problem=best.problem,
        solution=best.solution,
        target_customer=best.target_customer,
        revenue_potential=best.revenue_model,
        confidence=best.confidence,
        notes=(
            f"Signal: {candidates[best_index]['signal']}; "
            f"Evidence: {candidates[best_index]['evidence_count']}; "
            f"Matched keywords: "
            f"{', '.join(candidates[best_index]['matched_keywords'])}"
        ),
    )
    evidence = recall_evidence(opportunity_id)

    print("TOP OPPORTUNITY")
    print("===============")
    print("Title:", best.title)
    print("Problem:", best.problem)
    print("Customer:", best.target_customer)
    print("Solution:", best.solution)
    print("Revenue:", best.revenue_model)
    print("Confidence:", best.confidence)
    print()

    print("WHY IT RANKED FIRST")
    print("--------------------")
    print(explanation["reason"])
    print()

    print("EVIDENCE")
    print("--------")

    if evidence:
        for i, item in enumerate(evidence, 1):
            query, title, link, description, published = item
            print(f"{i}. {title}")
            print(f"   Query: {query}")
            print(f"   Published: {published}")
            print(f"   Link: {link}")
            print()
    else:
        print("No saved evidence found.")

    print("BUSINESS VALIDATION")
    print("--------------------")

    validation_candidate = {
        **best.__dict__,
        "signal": candidates[best_index]["signal"],
    }

    business_validation = validate_business_opportunity(
        validation_candidate,
        candidates[best_index]["evidence_items"],
        commercial_research,
    )

    print("Demand evidence:", f"{business_validation['demand']}/100")
    print("Customer clarity:", f"{business_validation['customer']}/100")
    print("Revenue evidence:", f"{business_validation['revenue']}/100")
    print("Competition evidence:", f"{business_validation['competition']}/100")
    print("Build feasibility:", f"{business_validation['build_feasibility']}/100")
    print("Risk:", f"{business_validation['risk']}/100")
    print("Build readiness:", f"{business_validation['readiness']}/100")
    print("Research status:", business_validation["research_status"])

    breakdown = business_validation["evidence_breakdown"]
    print("Payment evidence:", breakdown["payment_evidence"])
    print("Pricing evidence:", breakdown["pricing_evidence"])
    print("Competition evidence:", breakdown["competition_evidence"])
    print("Unmet-need evidence:", breakdown["unmet_need_evidence"])
    print()
    print("RECOMMENDATION")
    print("--------------")
    print(business_validation["recommendation"])
    print()

    print("NEXT TEST")
    print("---------")
    print(best.next_test)
    print()

    if business_validation["recommendation"] == "RESEARCH MORE BEFORE BUILDING":
        print("TARGETED VALIDATION RESEARCH")
        print("----------------------------")

        targeted_research = collect_validation_research(
            validation_candidate,
            business_validation["validation_gaps"],
            max_queries=8,
            max_results_per_query=5,
        )

        print("Targeted research items:", len(targeted_research))
        print()

        if targeted_research:
            combined_research = (
                candidates[best_index]["evidence_items"]
                + targeted_research
            )

            targeted_commercial_research = [
                item
                for item in targeted_research
                if item.get("validation_type") == "commercial"
            ]

            combined_commercial_research = (
                commercial_research
                + targeted_commercial_research
            )

            business_validation = validate_business_opportunity(
                validation_candidate,
                combined_research,
                combined_commercial_research,
            )

            print("RE-VALIDATION")
            print("------------")
            print("Demand evidence:", f"{business_validation['demand']}/100")
            print("Customer clarity:", f"{business_validation['customer']}/100")
            print("Revenue evidence:", f"{business_validation['revenue']}/100")
            print(
                "Competition evidence:",
                f"{business_validation['competition']}/100",
            )
            print(
                "Build feasibility:",
                f"{business_validation['build_feasibility']}/100",
            )
            print("Risk:", f"{business_validation['risk']}/100")
            print("Build readiness:", f"{business_validation['readiness']}/100")
            print("Research status:", business_validation["research_status"])

            breakdown = business_validation["evidence_breakdown"]
            print("Payment evidence:", breakdown["payment_evidence"])
            print("Pricing evidence:", breakdown["pricing_evidence"])
            print("Competition evidence:", breakdown["competition_evidence"])
            print("Unmet-need evidence:", breakdown["unmet_need_evidence"])
            print()

            print("UPDATED RECOMMENDATION")
            print("----------------------")
            print(business_validation["recommendation"])
            print()
        else:
            print("No targeted research results found.")
            print()

    print("BUSINESS PLAN")
    print("-------------")
    plan_idea = {
        "signal": candidates[best_index]["signal"],
        "problem": best.problem,
        "target_customer": best.target_customer,
        "solution": best.solution,
        "evidence_count": best.evidence_count,
        "confidence": best.confidence,
    }
    business_plan = generate_business_plan(plan_idea)
    print(format_business_plan(business_plan))
    print()

    print("MVP BUILD APPROVAL")
    print("-------------------")

    mvp_build_approval = approve_mvp_build(
        business_validation
    )

    print("Build status:", mvp_build_approval["status"])
    print()

    print("BUILD APPROVAL CHECKS")
    print("---------------------")
    for check, passed in mvp_build_approval["checks"].items():
        print(f"- {check}: {'PASS' if passed else 'FAIL'}")
    print()

    if mvp_build_approval["failed_checks"]:
        print("FAILED BUILD CHECKS")
        print("-------------------")
        for check in mvp_build_approval["failed_checks"]:
            print(f"- {check}")
        print()
    else:
        print("All MVP build approval checks passed.")
        print()

    print("MVP BUILD PLAN")
    print("--------------")

    build_validation = dict(business_validation)

    if mvp_build_approval["approved"]:
        build_validation["recommendation"] = "MVP BUILD APPROVED"

    build_plan = create_build_plan(
        validation_candidate,
        build_validation,
    )

    print("Build eligibility:", build_plan["build_eligibility"])
    print("Product type:", build_plan["product_type"])
    print()

    print("MVP FEATURES")
    print("------------")
    for feature in build_plan["mvp_features"]:
        print(f"- {feature}")
    print()

    print("SCREENS")
    print("-------")
    for screen in build_plan["screens"]:
        print(f"- {screen}")
    print()

    print("USER FLOW")
    print("---------")
    for step in build_plan["user_flow"]:
        print(f"- {step}")
    print()

    print("TECHNOLOGY")
    print("----------")
    for technology in build_plan["technology"]:
        print(f"- {technology}")
    print()

    print("BUILD PHASES")
    print("------------")
    for phase in build_plan["build_phases"]:
        print(f"- {phase}")
    print()

    print("PLAY STORE PREPARATION")
    print("----------------------")
    for item in build_plan["play_store_preparation"]:
        print(f"- {item}")
    print()

    print("NEXT VALIDATION ACTIONS")
    print("-----------------------")
    for gap in business_validation["validation_gaps"]:
        print(f"- {gap}")


if __name__ == "__main__":
    run_robot()
