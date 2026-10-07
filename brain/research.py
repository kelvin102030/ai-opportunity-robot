import re

import requests
import xml.etree.ElementTree as ET


RESEARCH_QUERIES = [
    # Problems and unmet needs
    "problems people are struggling with",
    "unmet needs consumers",
    "unresolved customer problems",
    "common problems businesses face",
    "services people need but cannot find",
    "frustrating everyday problems consumers",
    "underserved customer needs",
    "poorly served markets",
    "problems existing products fail to solve",

    # Emerging trends and behavior changes
    "emerging consumer trends",
    "new consumer behavior trends",
    "rapidly growing online trends",
    "new digital habits consumers",
    "technology trends creating new markets",
    "emerging business opportunities",
    "new markets growing online",
    "industries being disrupted by technology",

    # Business opportunities
    "new business opportunities online",
    "profitable online business opportunities",
    "small business opportunities emerging",
    "software business opportunities",
    "online services people pay for",
    "businesses looking for software solutions",
    "companies spending money on new software",
    "businesses replacing manual processes",

    # Existing solutions and weaknesses
    "popular apps users complain about",
    "software users want improved",
    "customers unhappy with existing apps",
    "alternatives to expensive software",
    "manual processes businesses want automated",
    "market gaps existing companies",
    "customers switching from existing services",

    # Monetization and willingness to pay
    "customers willing to pay for solutions",
    "businesses paying for digital services",
    "subscription software market opportunities",
    "services with recurring revenue",
    "digital products people pay for",
    "businesses spending money to solve problems",

    # Market signals
    "startup ideas based on real customer problems",
    "new startups solving emerging problems",
    "fast growing startups new markets",
    "venture funding emerging industries",
    "consumer demand growing rapidly",
    "products with growing customer demand",

    # Nigeria and African opportunities
    "problems Nigerians face",
    "business challenges Nigeria",
    "services people need Nigeria",
    "digital opportunities Nigeria",
    "online business opportunities Nigeria",
    "Nigerian consumers unmet needs",
    "African consumer problems technology",
    "African startups solving local problems",
]



def search_news(query, max_results=5):
    url = "https://news.google.com/rss/search"

    try:
        response = requests.get(
            url,
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        print(f"Research request failed for '{query}': {exc}")
        return []

    root = ET.fromstring(response.text)

    results = []

    for item in root.findall(".//item")[:max_results]:
        title = item.findtext("title", "")

        source = ""
        if " - " in title:
            source = title.rsplit(" - ", 1)[-1].strip()

        source_element = item.find("source")
        publisher_url = (
            source_element.get("url", "").strip()
            if source_element is not None
            else ""
        )

        raw_description = item.findtext("description", "")
        description = re.sub(
            r"<[^>]+>",
            " ",
            raw_description,
        )
        description = re.sub(
            r"\s+",
            " ",
            description,
        ).strip()

        results.append({
            "title": title,
            "source": source,
            "publisher_url": publisher_url,
            "link": item.findtext("link", ""),
            "description": description,
            "published": item.findtext("pubDate", ""),
        })

    return results


def collect_research(max_results_per_query=5):
    research = []

    for query in RESEARCH_QUERIES:
        results = search_news(
            query,
            max_results=max_results_per_query,
        )

        for result in results:
            research.append({
                "query": query,
                **result,
            })

    return research



def publisher_domain(source):
    source = source.strip().lower()

    known_domains = {
        "zendesk": "zendesk.com",
        "hubspot": "hubspot.com",
        "freshworks": "freshworks.com",
        "salesforce": "salesforce.com",
        "intercom": "intercom.com",
        "shopify": "shopify.com",
    }

    if source in known_domains:
        return known_domains[source]

    if "." in source and " " not in source:
        source = source.removeprefix("www.")
        return source

    return None


def commercial_publisher_domains(research):
    domains = []
    seen = set()

    for item in research:
        domain = publisher_domain(item.get("source", ""))

        if not domain or domain in seen:
            continue

        seen.add(domain)
        domains.append(domain)

    return domains


def search_web_page(url, timeout=15):
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Web page request failed for '{url}': {exc}")
        return None

    text = re.sub(r"<script[^>]*>.*?</script>", " ", response.text, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return {
        "url": url,
        "text": text,
        "status_code": response.status_code,
    }


def collect_web_evidence(research):
    evidence = []
    seen_urls = set()

    for item in research:
        publisher_url = item.get("publisher_url", "").strip()

        if not publisher_url or publisher_url in seen_urls:
            continue

        seen_urls.add(publisher_url)

        page = search_web_page(publisher_url)

        if not page:
            continue

        evidence.append({
            "domain": publisher_url,
            "url": page["url"],
            "text": page["text"],
            "status_code": page["status_code"],
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "publisher_url": publisher_url,
        })

    return evidence


def commercial_customer_phrase(customer):
    text = customer.lower()

    mappings = [
        ("customer support", "customer support businesses"),
        ("telecom", "telecom customers"),
        ("small businesses", "small businesses"),
        ("retailers", "retail businesses"),
        ("farmers", "farmers"),
        ("students", "students"),
        ("schools", "schools"),
        ("hospitals", "hospitals"),
        ("businesses", "businesses"),
        ("customers", "customers"),
    ]

    for keyword, phrase in mappings:
        if keyword in text:
            return phrase

    words = [
        word
        for word in re.findall(r"[a-zA-Z]+", text)
        if len(word) >= 5
    ]

    return " ".join(words[:4]) if words else "customers"


def collect_commercial_research(candidate, max_results_per_query=5):
    research = []

    customer = candidate.get("target_customer", "").strip()
    customer_phrase = commercial_customer_phrase(customer)
    solution = candidate.get("solution", "").strip()
    problem = candidate.get("problem", "").strip()

    queries = [
        # Existing solutions and competitors
        f'"{customer}" Nigeria software company',
        f'"{customer}" Nigeria customer service platform',
        f'"{customer}" Nigeria complaint management',
        f'"{problem}" Nigeria existing solution',
        f'"{problem}" Nigeria competitor',
        f'"{solution}" Nigeria competitor',

        # Real products and vendors
        "customer service software Nigeria company",
        "customer support software Nigeria company",
        "customer experience software Nigeria company",
        "CRM customer service Nigeria company",
        "customer complaint management Nigeria company",
        "customer feedback software Nigeria company",

        # Pricing evidence
        "customer service software Nigeria pricing",
        "customer support software Nigeria pricing",
        "customer experience software Nigeria pricing",
        "CRM software Nigeria pricing",
        "customer complaint software Nigeria pricing",
        "customer service outsourcing Nigeria rates",
        "customer support outsourcing Nigeria rates",

        # Paying customers
        "customer service software Nigeria customers pay",
        "customer support software Nigeria paying customers",
        "CRM Nigeria paying customers",
        "customer experience platform Nigeria customers",
        "customer service company Nigeria clients",
        "customer support company Nigeria clients",

        # Purchases and contracts
        "Nigeria company purchased CRM software",
        "Nigeria company purchased customer service software",
        "Nigeria company signed customer service contract",
        "Nigeria customer service software contract",
        "Nigeria CRM contract awarded",
        "Nigeria customer support contract awarded",
        "Nigeria customer service outsourcing contract",

        # Procurement and spending
        "Nigeria customer service software procurement",
        "Nigeria CRM software procurement",
        "Nigeria customer support procurement",
        "Nigeria customer experience procurement",
        "Nigeria call center procurement",
        "Nigeria customer service tender",

        # Market demand / unmet need
        "Nigeria customer service complaints businesses",
        "Nigeria customers frustrated customer service",
        "Nigeria unresolved customer complaints",
        "Nigeria poor customer service business losses",
        "Nigeria customer service problems companies",
        "Nigeria customer support problems businesses",

        # Candidate-specific commercial evidence
        f'"{customer_phrase}" Nigeria pricing',
        f'"{customer_phrase}" Nigeria customers pay',
        f'"{customer_phrase}" Nigeria contract',
        f'"{customer_phrase}" Nigeria procurement',
        f'"{customer_phrase}" Nigeria complaints',
    ]

    for query in queries:
        results = search_news(
            query,
            max_results=max_results_per_query,
        )

        for result in results:
            research.append({
                "query": query,
                **result,
            })

    return research


def validation_query_type(query):
    """Classify a targeted validation query by the evidence it seeks."""
    text = query.lower()

    if any(term in text for term in (
        "pay",
        "paying",
        "pricing",
        "price",
        "cost",
        "subscription",
        "contract",
        "fee",
        "procurement",
    )):
        return "commercial"

    if any(term in text for term in (
        "competitor",
        "competitors",
        "alternative",
        "alternatives",
        "rival",
        "rivals",
        "existing platform",
    )):
        return "commercial"

    if any(term in text for term in (
        "buyer",
        "decision maker",
        "decision-maker",
        "business owner",
    )):
        return "customer"

    if any(term in text for term in (
        "demand",
        "frequency",
        "workload",
        "losses",
        "problems",
        "complaints",
        "unresolved",
        "poor customer service",
        "customer support problems",
    )):
        return "demand"

    return "general"


def collect_validation_research(
    candidate,
    validation_gaps,
    max_queries=8,
    max_results_per_query=5,
):
    """Collect a bounded research pass targeted at validation gaps."""
    queries = generate_validation_queries(candidate, validation_gaps)

    research = []
    seen = set()

    for query in queries[:max_queries]:
        query_type = validation_query_type(query)

        try:
            results = search_news(
                query,
                max_results=max_results_per_query,
            )
        except Exception:
            continue

        for item in results:
            key = item.get("link", "").strip().lower()

            if not key:
                key = item.get("title", "").strip().lower()

            if key in seen:
                continue

            seen.add(key)

            research.append({
                **item,
                "query": query,
                "validation_type": query_type,
            })

    return research


def generate_validation_queries(candidate, validation_gaps):
    """Generate targeted research queries from business-validation gaps."""
    customer = candidate.get("target_customer", "").strip()
    problem = candidate.get("problem", "").strip()
    solution = candidate.get("solution", "").strip()

    queries = []

    gap_text = " ".join(validation_gaps).lower()

    if "demand" in gap_text:
        queries.extend([
            "Nigeria recurring customer service problems businesses",
            "Nigeria frequency of customer complaints businesses",
            "Nigeria businesses unresolved customer complaints",
            "Nigeria customer support workload businesses",
            "Nigeria business losses poor customer service",
        ])

        if problem:
            queries.extend([
                f'"{problem}" Nigeria demand',
                f'"{problem}" Nigeria businesses',
            ])

    if "customer" in gap_text or "buyer" in gap_text:
        queries.extend([
            "Nigeria customer service software buyer",
            "Nigeria customer service software decision maker",
            "Nigeria customer support software business owner",
            "Nigeria customer service software procurement manager",
            "Nigeria businesses paying for customer service software",
        ])

        if customer:
            queries.extend([
                f'"{customer}" Nigeria software buyer',
                f'"{customer}" Nigeria decision maker',
                f'"{customer}" Nigeria software procurement',
            ])

    if "revenue" in gap_text or "pay" in gap_text:
        queries.extend([
            "Nigeria customer service software customers pay",
            "Nigeria customer support software pricing customers",
            "Nigeria businesses paying for customer support software",
        ])

    if "competition" in gap_text or "competitor" in gap_text:
        queries.extend([
            "Nigeria customer service software competitors",
            "Nigeria customer support software alternatives",
            "Nigeria customer complaint management software companies",
        ])

    if "unmet" in gap_text or "problem" in gap_text:
        queries.extend([
            "Nigeria unresolved customer complaints businesses",
            "Nigeria poor customer service business problems",
            "Nigeria customer support problems companies",
        ])

    if solution and "solution" in gap_text:
        queries.append(f'"{solution}" Nigeria')

    # Preserve order while removing duplicates.
    unique_queries = []
    seen = set()

    for query in queries:
        normalized = query.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_queries.append(query.strip())

    return unique_queries


if __name__ == "__main__":
    print("AI OPPORTUNITY RESEARCH")
    print("=======================")

    research = collect_research()

    print("Research items collected:", len(research))
    print()

    for i, item in enumerate(research, 1):
        print(f"{i}. [{item['query']}]")
        print(f"   {item['title']}")
        print()
