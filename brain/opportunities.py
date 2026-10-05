from collections import Counter
import re

from brain.research import collect_research


def _story_numbers(title):
    numbers = set()

    for match in re.findall(r"\b\d[\d,]{3,}\b", title):
        number = match.replace(",", "")

        if number.startswith(("19", "20")):
            continue

        numbers.add(number)

    return numbers


_STORY_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for",
    "among", "this", "that", "with", "as", "by", "from", "most",
    "first", "half", "year", "h1", "nigeria", "nigerian",
    "receives", "tops", "hit", "issues", "persist",
    "news", "week", "times",
}


def _story_terms(title):
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", title.lower())

    return {
        word
        for word in words
        if word not in _STORY_STOPWORDS
    }


def _stories_related(left, right):
    left_title = left.get("title", "")
    right_title = right.get("title", "")

    left_numbers = _story_numbers(left_title)
    right_numbers = _story_numbers(right_title)

    if left_numbers & right_numbers:
        return True

    left_terms = _story_terms(left_title)
    right_terms = _story_terms(right_title)

    shared = left_terms & right_terms

    important_terms = {
        "airtel",
        "ncc",
        "fccpc",
        "telecom",
        "telecoms",
        "413587",
    }

    important_shared = shared & important_terms

    return len(important_shared) >= 2


def _count_story_clusters(items):
    clusters = []

    for item in items:
        placed = False

        for cluster in clusters:
            if any(_stories_related(item, existing) for existing in cluster):
                cluster.append(item)
                placed = True
                break

        if not placed:
            clusters.append([item])

    return len(clusters)


PROBLEM_GROUPS = {
    "customer_service": {
        "keywords": ["customer", "complaint", "satisfaction", "trust"],
        "exclude_keywords": [
            "telecom",
            "airtel",
            "data depletion",
            "billing woes",
            "network",
            "airtime",
        ],
        "problem": "Customers are experiencing recurring customer-service problems.",
        "impact": 2,
        "solution_potential": 5,
    },
    "telecom_problems": {
        "keywords": [
            "billing",
            "data",
            "telecom",
            "network",
            "airtime",
            "complaint",
        ],
        "required_keywords": [
            "telecom",
            "airtel",
            "network",
            "airtime",
        ],
        "problem": "Customers may be experiencing telecom billing, data, network, and service problems.",
        "impact": 3,
        "solution_potential": 4,
    },
    "small_business_operations": {
        "keywords": ["visibility", "payroll", "recruitment"],
        "problem": "Small businesses may struggle with visibility, payroll, and recruitment.",
        "impact": 3,
        "solution_potential": 4,
    },
    "infrastructure": {
        "keywords": ["road", "energy", "security"],
        "problem": "Infrastructure and operating conditions create problems for businesses and customers.",
        "impact": 5,
        "solution_potential": 2,
    },
    "business_costs": {
        "keywords": ["inflation"],
        "problem": "Rising costs are putting pressure on businesses.",
        "impact": 4,
        "solution_potential": 4,
    },
}


def generate_candidates(research):
    candidates = []

    for name, group in PROBLEM_GROUPS.items():
        counts = Counter()
        evidence_items = []

        for item in research:
            title = item["title"].lower()
            description = item.get("description", "").lower()
            content = f"{title} {description}"

            matched = False

            excluded = any(
                keyword in content
                for keyword in group.get("exclude_keywords", [])
            )

            if excluded:
                continue

            required_keywords = group.get("required_keywords", [])

            if required_keywords and not any(
                keyword in content
                for keyword in required_keywords
            ):
                continue

            for keyword in group["keywords"]:
                count = content.count(keyword)

                if count > 0:
                    counts[keyword] += count
                    matched = True

            if matched:
                evidence_items.append(item)

        unique_evidence = []
        seen_items = set()

        for item in evidence_items:
            link = item.get("link", "").strip()
            title_key = item.get("title", "").strip().lower()

            key = ("link", link) if link else ("title", title_key)

            if key in seen_items:
                continue

            seen_items.add(key)

            unique_evidence.append(item)

        evidence_items = unique_evidence

        evidence_count = len(evidence_items)

        source_names = set()

        for item in evidence_items:
            source = item.get("source", "").strip()

            if not source:
                source = item.get("title", "").strip()

            source_names.add(source)

        source_diversity = len(source_names)

        story_clusters = _count_story_clusters(evidence_items)

        source_independence = (
            story_clusters / evidence_count
            if evidence_count > 0
            else 0
        )

        if evidence_count == 0:
            continue

        matched_keywords = [
            keyword
            for keyword, count in counts.items()
            if count > 0
        ]

        impact_score = group.get("impact", 1)
        solution_potential = group.get("solution_potential", 1)

        opportunity_score = (
            evidence_count
            + source_diversity
            + len(matched_keywords)
            + impact_score
            + solution_potential
        )

        if evidence_count >= 3 and source_independence >= 0.75:
            confidence = "high"
        elif evidence_count >= 2 and source_independence >= 0.50:
            confidence = "medium"
        else:
            confidence = "low"

        evidence_label = "item" if evidence_count == 1 else "items"
        source_label = "source" if source_diversity == 1 else "sources"

        reason = (
            f"{evidence_count} evidence {evidence_label} from "
            f"{source_diversity} {source_label}; "
            f"impact {impact_score}/5; "
            f"solution potential {solution_potential}/5; "
            f"confidence {confidence}."
        )

        candidates.append({
            "signal": name,
            "evidence_count": evidence_count,
            "source_diversity": source_diversity,
            "story_clusters": story_clusters,
            "source_independence": source_independence,
            "confidence": confidence,
            "matched_keywords": matched_keywords,
            "impact_score": impact_score,
            "solution_potential": solution_potential,
            "opportunity_score": opportunity_score,
            "reason": reason,
            "problem": group["problem"],
            "evidence_items": evidence_items,
        })

    return sorted(
        candidates,
        key=lambda item: item["opportunity_score"],
        reverse=True,
    )


if __name__ == "__main__":
    research = collect_research()

    candidates = generate_candidates(research)

    print("OPPORTUNITY CANDIDATES")
    print("=====================")

    for i, candidate in enumerate(candidates, 1):
        print(f"{i}. {candidate['signal']}")
        print(f"   Opportunity score: {candidate['opportunity_score']}")
        print(f"   Evidence: {candidate['evidence_count']}")
        print(f"   Source diversity: {candidate['source_diversity']}")
        print(f"   Source independence: {candidate['source_independence']:.2f}")
        print(f"   Confidence: {candidate['confidence']}")
        print(f"   Impact score: {candidate['impact_score']}")
        print(f"   Solution potential: {candidate['solution_potential']}")
        print(f"   Why: {candidate['reason']}")
        print(f"   Signals: {', '.join(candidate['matched_keywords'])}")
        print(f"   Problem: {candidate['problem']}")
        print(f"   Research items: {len(candidate['evidence_items'])}")

        print("   Evidence:")
        for item in candidate["evidence_items"]:
            source = item.get("source", "").strip()
            title = item.get("title", "").strip()

            if source:
                print(f"      - {title} [{source}]")
            else:
                print(f"      - {title}")

        print()
