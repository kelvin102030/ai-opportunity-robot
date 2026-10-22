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

    # Group likely duplicate coverage conservatively. Sharing a broad
    # industry term is not enough to establish that two reports describe
    # the same event.
    union = left_terms | right_terms
    similarity = len(shared) / len(union) if union else 0

    return len(shared) >= 3 and similarity >= 0.50


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


DISCOVERY_THEMES = {
    "consumer_pain": {
        "keywords": [
            "problem", "problems", "complaint", "complaints",
            "frustrated", "frustration", "difficult", "difficulty",
            "unresolved", "challenge", "challenges", "pain",
        ],
        "problem": "People are experiencing recurring problems that may have room for a better solution.",
        "impact": 4,
        "solution_potential": 4,
    },
    "business_automation": {
        "keywords": [
            "manual", "automate", "automation", "workflow",
            "paperwork", "process", "processes", "efficiency",
            "productivity", "software",
        ],
        "problem": "People or businesses may be losing time or money through inefficient processes.",
        "impact": 4,
        "solution_potential": 5,
    },
    "digital_services": {
        "keywords": [
            "online", "digital", "app", "platform", "website",
            "mobile", "internet", "software", "technology",
        ],
        "problem": "A growing digital behavior or service need may support a new or improved online product.",
        "impact": 3,
        "solution_potential": 5,
    },
    "payments_finance": {
        "keywords": [
            "payment", "payments", "money", "finance", "financial",
            "banking", "transfer", "transaction", "credit", "lending",
            "insurance", "fintech",
        ],
        "problem": "People or businesses may have unmet needs around financial transactions and services.",
        "impact": 5,
        "solution_potential": 4,
    },
    "commerce_marketplace": {
        "keywords": [
            "marketplace", "seller", "sellers", "buyer", "buyers",
            "shopping", "retail", "merchant", "merchants", "commerce",
            "delivery",
        ],
        "problem": "Buyers and sellers may have inefficient ways to discover, transact, or exchange goods and services.",
        "impact": 4,
        "solution_potential": 5,
    },
    "education_skills": {
        "keywords": [
            "education", "students", "student", "school", "schools",
            "learning", "skills", "training", "course", "courses",
            "teachers", "teaching",
        ],
        "problem": "Learners, educators, or institutions may have underserved education and skills needs.",
        "impact": 4,
        "solution_potential": 4,
    },
    "health_wellness": {
        "keywords": [
            "health", "healthcare", "hospital", "hospitals", "patient",
            "patients", "medical", "doctor", "doctors", "wellness",
            "clinic", "clinics",
        ],
        "problem": "People or healthcare organizations may have underserved needs around access, coordination, or wellness.",
        "impact": 5,
        "solution_potential": 4,
    },
    "agriculture_food": {
        "keywords": [
            "farm", "farms", "farmer", "farmers", "agriculture",
            "agricultural", "food", "farming", "crop", "crops",
            "livestock", "supply",
        ],
        "problem": "Agricultural or food-market participants may have inefficient supply, access, or coordination problems.",
        "impact": 5,
        "solution_potential": 4,
    },
    "logistics_mobility": {
        "keywords": [
            "logistics", "transport", "transportation", "delivery",
            "shipping", "mobility", "traffic", "vehicle", "vehicles",
            "warehouse", "warehousing",
        ],
        "problem": "People and businesses may face inefficient movement, delivery, or logistics processes.",
        "impact": 4,
        "solution_potential": 5,
    },
    "creator_media": {
        "keywords": [
            "creator", "creators", "content", "media", "video",
            "videos", "audience", "influencer", "influencers",
            "streaming", "podcast", "podcasts",
        ],
        "problem": "Creators and audiences may have underserved tools, monetization, or discovery needs.",
        "impact": 3,
        "solution_potential": 5,
    },
    "employment_work": {
        "keywords": [
            "jobs", "job", "employment", "workers", "worker",
            "hiring", "recruitment", "freelance", "freelancers",
            "career", "work",
        ],
        "problem": "Workers, employers, or freelancers may have underserved employment and work-related needs.",
        "impact": 4,
        "solution_potential": 5,
    },
    "housing_property": {
        "keywords": [
            "housing", "property", "properties", "rent", "rental",
            "landlord", "tenant", "tenants", "real estate",
        ],
        "problem": "People or businesses may have inefficient ways to find, manage, or transact around property.",
        "impact": 4,
        "solution_potential": 4,
    },
    "energy_utilities": {
        "keywords": [
            "energy", "electricity", "power", "solar", "utility",
            "utilities", "fuel", "water", "waste",
        ],
        "problem": "Households and businesses may have recurring utility, energy, or resource-management problems.",
        "impact": 5,
        "solution_potential": 4,
    },
    "security_trust": {
        "keywords": [
            "security", "fraud", "scam", "scams", "identity",
            "trust", "privacy", "safety", "risk", "verification",
        ],
        "problem": "People or businesses may need better ways to reduce fraud, risk, or trust problems.",
        "impact": 5,
        "solution_potential": 4,
    },
    "emerging_market": {
        "keywords": [
            "emerging", "growing", "growth", "trend", "trends",
            "demand", "market", "markets", "startup", "startups",
            "opportunity", "opportunities", "disruption",
        ],
        "problem": "A changing market or behavior pattern may create an emerging business opportunity.",
        "impact": 4,
        "solution_potential": 5,
    },
}


def _candidate_evidence(research, keywords):
    evidence_items = []
    counts = Counter()

    for item in research:
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        content = f"{title} {description}"

        matched = False

        for keyword in keywords:
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

    return counts, unique_evidence


def _build_candidate(name, theme, research):
    counts, evidence_items = _candidate_evidence(
        research,
        theme["keywords"],
    )

    evidence_count = len(evidence_items)

    if evidence_count == 0:
        return None

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
        if evidence_count
        else 0
    )

    matched_keywords = [
        keyword
        for keyword, count in counts.items()
        if count > 0
    ]

    impact_score = theme["impact"]
    solution_potential = theme["solution_potential"]

    opportunity_score = _research_support_score(
        evidence_count,
        source_independence,
    )

    if evidence_count >= 5 and source_independence >= 0.60:
        confidence = "high"
    elif evidence_count >= 3 and source_independence >= 0.40:
        confidence = "medium"
    else:
        confidence = "low"

    evidence_label = "item" if evidence_count == 1 else "items"
    source_label = "source" if source_diversity == 1 else "sources"

    reason = (
        f"{evidence_count} evidence {evidence_label} from "
        f"{source_diversity} {source_label}; "
        f"{story_clusters} story clusters; "
        f"impact {impact_score}/5; "
        f"solution potential {solution_potential}/5; "
        f"confidence {confidence}."
    )

    return {
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
        "problem": theme["problem"],
        "evidence_items": evidence_items,
    }


_CONCEPT_STOPWORDS = {
    "about", "after", "again", "also", "among", "because", "being",
    "between", "could", "during", "first", "from", "have", "into",
    "more", "most", "other", "people", "their", "there", "these",
    "they", "this", "those", "through", "under", "using", "where",
    "which", "while", "with", "would", "your",
    "business", "businesses", "problem", "problems",
    "opportunity", "opportunities", "customer", "customers",
    "consumer", "consumers", "user", "users",
    "service", "services", "company", "companies",
    "people", "market", "markets", "need", "needs",
    "unmet", "solution", "solutions", "support",
    "help", "helping", "using", "based", "today",
    "future", "industry", "industries",
}


def _concept_terms(text):
    """Extract meaningful words without allowing search queries to dominate."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", str(text).lower())
    return {
        word for word in words
        if word not in _CONCEPT_STOPWORDS
    }



def _research_text(item):
    return " ".join([
        item.get("title", ""),
        item.get("description", ""),
        item.get("query", ""),
    ]).strip()


def _research_similarity(left, right):
    """Compare article content using shared terms and cautious topic signals."""
    left_text = " ".join([
        str(left.get("title", "") or ""),
        str(left.get("description", "") or ""),
    ]).strip()

    right_text = " ".join([
        str(right.get("title", "") or ""),
        str(right.get("description", "") or ""),
    ]).strip()

    left_terms = _concept_terms(left_text)
    right_terms = _concept_terms(right_text)

    if not left_terms or not right_terms:
        return 0

    shared = left_terms & right_terms
    union = left_terms | right_terms
    jaccard = len(shared) / len(union) if union else 0

    # A topic signal requires terms from both sides of a meaningful
    # relationship. Broad industry words alone are insufficient.
    related_term_groups = (
        {"inventory", "inventories", "stock", "stocks"},
        {"retailers", "retailer", "retail", "shops", "shop", "stores", "store"},
        {"farmers", "farmer", "farming", "agriculture", "crops", "crop"},
        {"patients", "patient", "clinics", "clinic", "hospitals", "hospital"},
        {"waiting", "waits", "delays", "delay", "queues", "queue"},
        {"staffing", "staff", "understaffed", "shortages", "shortage", "appointments", "appointment"},
        {"payments", "payment", "transactions", "transaction"},
        {"delivery", "deliveries", "logistics", "shipping"},
        {"electricity", "power", "energy", "outages"},
    )

    related_groups = sum(
        1
        for group in related_term_groups
        if left_terms & group and right_terms & group
    )

    # Strong lexical overlap remains the primary matching method.
    if len(shared) >= 2:
        return max(jaccard, 0.26 if related_groups else 0)

    # Permit a modest topic match only when multiple independent
    # topic relationships are present in both articles.
    if related_groups >= 2:
        return max(jaccard, 0.26)

    return jaccard





def _cluster_research(research, minimum_similarity=0.30):
    clusters = []

    for item in research:
        placed = False

        for cluster in clusters:
            if any(
                _research_similarity(item, existing)
                >= minimum_similarity
                for existing in cluster
            ):
                cluster.append(item)
                placed = True
                break

        if not placed:
            clusters.append([item])

    return clusters


def _concept_name(cluster):
    """Name a research cluster from article titles, not discovery queries."""
    counts = Counter()
    title_counts = Counter()

    for item in cluster:
        title = str(item.get("title", "") or "").strip()
        description = str(item.get("description", "") or "").strip()

        # Titles are the primary signal for naming a concrete topic.
        title_counts.update(_concept_terms(title))

        # Descriptions can support a title term but cannot introduce a
        # completely unrelated name by themselves.
        description_terms = _concept_terms(description)
        for term in _concept_terms(title):
            counts[term] += 2
        for term in description_terms:
            counts[term] += 1

    common_terms = [
        term
        for term, count in title_counts.most_common(10)
        if count >= 2
    ]

    if common_terms:
        return " ".join(word.capitalize() for word in common_terms[:4])

    # For a small cluster, use distinctive title terms rather than
    # inventing an "Emerging market opportunity" name.
    fallback = [
        term
        for term, count in counts.most_common(6)
        if count >= 2
    ]

    if fallback:
        return " ".join(word.capitalize() for word in fallback[:4])

    return "Research topic requiring clarification"



def _concept_problem(cluster):
    """Describe the topic cautiously using evidence titles, not query text."""
    titles = []
    seen = set()

    for item in cluster:
        title = str(item.get("title", "") or "").strip()
        key = title.casefold()

        if title and key not in seen:
            seen.add(key)
            titles.append(title)

    if not titles:
        return (
            "A research topic has been identified, but the customer problem "
            "still needs to be established."
        )

    if len(titles) == 1:
        return (
            "Research topic identified: "
            + titles[0]
            + ". Confirm the affected Nigerian customers, the severity of "
              "the problem, and whether they will pay for a solution."
        )

    return (
        "Related research reports discuss: "
        + "; ".join(titles[:3])
        + ". Verify that these reports describe the same underlying problem "
          "before treating them as one business opportunity."
    )



def _research_support_score(evidence_count, source_independence):
    """Comparable 0-100 score for research support, not profitability."""
    evidence_count = max(0, int(evidence_count or 0))
    independence = float(source_independence or 0)
    independence = max(0.0, min(independence, 1.0))
    evidence_coverage = min(evidence_count / 5.0, 1.0)
    return round(evidence_coverage * 60 + independence * 40)


def _concept_evidence_score(cluster):
    """Score independent research support, not repeated article volume."""
    evidence_count = len(cluster)

    if evidence_count == 0:
        return 0

    story_clusters = _count_story_clusters(cluster)
    independence = story_clusters / evidence_count

    # Repeated coverage of one story must not earn the same evidence
    # quantity credit as multiple independent stories.
    return _research_support_score(story_clusters, independence)


def generate_concrete_opportunities(research, max_candidates=20):
    """
    Turn broad research into concrete opportunity concepts.

    This does not decide whether an opportunity should be built.
    It only creates research-backed concepts for later validation.
    """
    if not research:
        return []

    clusters = _cluster_research(research, minimum_similarity=0.25)

    opportunities = []

    for cluster in clusters:
        if len(cluster) < 2:
            continue

        name = _concept_name(cluster)
        problem = _concept_problem(cluster)

        sources = {
            item.get("source", "").strip()
            for item in cluster
            if item.get("source", "").strip()
        }

        queries = {
            item.get("query", "").strip()
            for item in cluster
            if item.get("query", "").strip()
        }

        opportunities.append({
            "signal": "research_concept",
            "concept": name,
            "problem": problem,
            "evidence_count": len(cluster),
            "source_diversity": len(sources),
            "query_diversity": len(queries),
            "opportunity_score": _concept_evidence_score(cluster),
            "confidence": (
                "high"
                if len(cluster) >= 5 and len(sources) >= 3
                else "medium"
                if len(cluster) >= 3
                else "low"
            ),
            "evidence_items": cluster,
            "matched_keywords": [],
            "source_independence": (
                _count_story_clusters(cluster) / len(cluster)
                if cluster
                else 0
            ),
        })

    opportunities.sort(
        key=lambda item: (
            item["opportunity_score"],
            item["source_diversity"],
            item["evidence_count"],
        ),
        reverse=True,
    )

    return opportunities[:max_candidates]


def generate_candidates(research):
    candidates = []

    for name, theme in DISCOVERY_THEMES.items():
        candidate = _build_candidate(name, theme, research)

        if candidate is not None:
            candidates.append(candidate)

    # Add research clusters as specific opportunity candidates.
    # Keep the existing theme-based candidates and their data unchanged.
    concrete_candidates = generate_concrete_opportunities(research)
    candidates.extend(concrete_candidates)

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
