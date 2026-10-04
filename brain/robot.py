from brain.research import collect_research
from brain.opportunities import generate_candidates
from brain.reasoning import analyze_candidate
from brain.ranking import best_opportunity, explain_ranking
from brain.memory import initialize_memory, remember_opportunity, remember_evidence, recall_evidence


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
        print("No opportunity candidates found.")
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

    print("NEXT TEST")
    print("---------")
    print(best.next_test)


if __name__ == "__main__":
    run_robot()
