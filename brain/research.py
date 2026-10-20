from concurrent.futures import ThreadPoolExecutor

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






# Additional Nigeria-focused research across multiple industries.
NIGERIA_RESEARCH_QUERIES = ['Nigeria consumer complaints poor service customer experience', 'Nigeria products services customers complain about', 'Nigeria underserved consumers unmet needs', 'Nigeria consumer protection complaints recurring problems', 'Nigeria small businesses operating costs challenges', 'Nigeria retailers inventory stock losses business problems', 'Nigeria SMEs unpaid invoices cash flow problems', 'Nigeria small businesses customer acquisition sales challenges', 'Nigeria business owners manual processes bookkeeping payroll', 'Nigeria SMEs software adoption willingness to pay', 'Nigeria farmers post harvest losses storage', 'Nigeria agricultural produce distribution market access', 'Nigeria food supply chain spoilage transport costs', 'Nigeria farmers buyers price transparency', 'Nigeria agribusiness processing equipment costs', 'Nigeria businesses payment failures transaction reconciliation', 'Nigeria merchants payment processing fees complaints', 'Nigeria SMEs access to working capital financing costs', 'Nigeria business invoicing collections late payments', 'Nigeria fintech customers fees reliability complaints', 'Nigeria small businesses generator fuel electricity costs', 'Nigeria businesses unreliable electricity productivity losses', 'Nigeria commercial solar energy costs payback Nigeria', 'Nigeria electricity billing complaints businesses', 'Nigeria last mile delivery costs small businesses', 'Nigeria online merchants delivery failures returns', 'Nigeria logistics businesses shipment tracking problems', 'Nigeria cold chain food medicine transport challenges', 'Nigeria employers skills shortages recruitment training', 'Nigeria students affordable exam preparation learning access', 'Nigeria vocational skills training employment demand', 'Nigeria schools administrative technology challenges', 'Nigeria healthcare access waiting times patient administration', 'Nigeria clinics medical inventory supply shortages', 'Nigeria pharmacies medicine availability supply chain', 'Nigeria healthcare providers operating costs digital tools', 'Nigeria housing maintenance repair service reliability', 'Nigeria renters landlords property management problems', 'Nigeria household service provider trust complaints', 'Nigeria businesses paying for software and digital services', 'Nigeria companies procurement contracts recurring services', 'Nigeria startup customers pricing willingness to pay', 'Nigeria business services competitor pricing market demand', 'Nigeria companies outsourcing operational services']


def search_news(query, max_results=5):
    url = "https://news.google.com/rss/search"

    try:
        response = requests.get(
            url,
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
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

    # map() preserves query order while requests run concurrently.
    queries = list(dict.fromkeys(
        RESEARCH_QUERIES + NIGERIA_RESEARCH_QUERIES
    ))

    with ThreadPoolExecutor(max_workers=8) as executor:
        batches = executor.map(
            lambda query: search_news(query, max_results_per_query),
            queries,
        )

        for query, results in zip(queries, batches):
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



def resolve_article_url(url, timeout=8):
    """Resolve a Google News redirect without accepting consent pages."""
    url = (url or "").strip()

    if not url:
        return None

    if not url.startswith(("https://", "http://")):
        return None

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 14) "
                    "AppleWebKit/537.36 Chrome/130.0.0.0 "
                    "Mobile Safari/537.36"
                ),
                "Accept-Language": "en-NG,en;q=0.9",
            },
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )

        final_url = response.url
        response.close()

    except requests.RequestException as exc:
        print(f"Article URL resolution failed for '{url}': {exc}")
        return None

    lowered = final_url.lower()

    if "consent.google.com" in lowered:
        return None

    if "news.google.com/rss/articles/" in lowered:
        return None

    return final_url


def _clean_article_html(fragment):
    """Convert an HTML fragment into readable text."""
    from html import unescape

    text = re.sub(
        r"<!--.*?-->",
        " ",
        fragment,
        flags=re.S,
    )

    text = re.sub(
        r"<(script|style|noscript|svg|nav|footer|header|form)\b"
        r"[^>]*>.*?</\1\s*>",
        " ",
        text,
        flags=re.I | re.S,
    )

    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _extract_article_text(html):
    """Prefer known article containers, then fall back to page text."""
    # Known publisher-specific article containers.
    container_patterns = [
        # Prefer the main story body over the outer article wrapper.
        r'<div\b(?=[^>]*\bid=["\']mvp-content-main["\'])[^>]*>',
        r'<div\b(?=[^>]*\bid=["\']mvp-post-content["\'])[^>]*>',
        r'<div\b(?=[^>]*\bclass=["\'][^"\']*\bentry-content\b)'
        r'[^>]*>',
        r'<div\b(?=[^>]*\bclass=["\'][^"\']*\bpost-content\b)'
        r'[^>]*>',
        r'<div\b(?=[^>]*\bitemprop=["\']articleBody["\'])[^>]*>',
    ]

    for pattern in container_patterns:
        match = re.search(pattern, html, flags=re.I)

        if not match:
            continue

        opening_tag = match.group(0)
        tag_match = re.match(r"<([a-z][a-z0-9]*)\b", opening_tag, re.I)

        if not tag_match:
            continue

        tag = tag_match.group(1)
        token_pattern = re.compile(
            rf"<{tag}\b[^>]*>|</{tag}\s*>",
            flags=re.I,
        )

        depth = 1
        closing_position = None

        for token in token_pattern.finditer(html, match.end()):
            if token.group(0).startswith("</"):
                depth -= 1

                if depth == 0:
                    closing_position = token.start()
                    break
            elif not token.group(0).rstrip().endswith("/>"):
                depth += 1

        if closing_position is None:
            continue

        fragment = html[match.end():closing_position]
        extracted = _clean_article_html(fragment)

        if len(extracted) >= 300:
            return extracted

    # General fallback for publishers with different HTML structures.
    return _clean_article_html(html)


def search_web_page(url, timeout=15):
    """Retrieve readable article text and reject consent/error pages."""
    if not url or not url.startswith(("https://", "http://")):
        return None

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 14) "
                    "AppleWebKit/537.36 Chrome/130.0.0.0 "
                    "Mobile Safari/537.36"
                ),
                "Accept-Language": "en-NG,en;q=0.9",
            },
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        print(f"Web page request failed for '{url}': {exc}")
        return None

    try:
        final_url = response.url
        status_code = response.status_code
        content_type = response.headers.get("Content-Type", "").lower()

        if (
            "text/html" not in content_type
            and "application/xhtml+xml" not in content_type
        ):
            print(f"Rejected non-HTML response: {final_url}")
            return None

        if "consent.google.com" in final_url.lower():
            print(f"Rejected Google consent page: {final_url}")
            return None

        html = response.text
    finally:
        response.close()

    lowered_html = html[:200000].lower()

    consent_markers = (
        "before you continue",
        "we use cookies and data",
        "consent.google.com",
    )

    if any(marker in lowered_html for marker in consent_markers):
        print(f"Rejected consent/interstitial page: {final_url}")
        return None

    text = _extract_article_text(html)

    if len(text) < 300:
        print(
            f"Rejected page with insufficient readable text: {final_url}"
        )
        return None

    return {
        "url": final_url,
        "text": text,
        "status_code": status_code,
    }
def collect_web_evidence(research, max_pages=8):
    """Collect accessible article pages without treating homepages as articles."""
    evidence = []
    seen_urls = set()

    for item in research:
        article_url = (item.get("link") or "").strip()
        publisher_url = (item.get("publisher_url") or "").strip()

        # Never count a publisher homepage as proof of a specific article.
        urls_to_try = []

        if article_url:
            resolved = resolve_article_url(article_url, timeout=8)

            if resolved:
                urls_to_try.append(resolved)

            # A non-Google article URL may still be worth trying directly.
            if (
                "news.google.com" not in article_url.lower()
                and "consent.google.com" not in article_url.lower()
            ):
                urls_to_try.append(article_url)

        accepted = None

        for url in dict.fromkeys(urls_to_try):
            if url in seen_urls:
                continue

            seen_urls.add(url)
            page = search_web_page(url, timeout=10)

            if not page:
                continue

            final_url = page["url"]
            final_lower = final_url.lower()

            # Redirects to homepages or Google consent are not article evidence.
            if "consent.google.com" in final_lower:
                continue

            if "news.google.com" in final_lower:
                continue

            accepted = page
            break

        if not accepted:
            continue

        evidence.append({
            "domain": publisher_domain(item.get("source", "")) or accepted["url"],
            "url": accepted["url"],
            "text": accepted["text"],
            "status_code": accepted["status_code"],
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "publisher_url": publisher_url,
            "article_url": article_url,
            "retrieval_status": "retrieved",
        })

        if len(evidence) >= max_pages:
            break

    return evidence


def commercial_customer_phrase(customer):
    """Return a compact, industry-neutral description of the customer."""
    text = re.sub(r"\s+", " ", str(customer or "")).strip()
    if not text:
        return "customers"
    words = text.split()
    return " ".join(words[:8])


def collect_commercial_research(candidate, max_results_per_query=5):
    """Search for commercial evidence related to this specific opportunity."""
    research = []

    customer = str(candidate.get("target_customer") or "").strip()
    customer_phrase = commercial_customer_phrase(customer)
    solution = str(candidate.get("solution") or "").strip()
    problem = str(candidate.get("problem") or "").strip()

    queries = []

    def add_query(value):
        value = re.sub(r"\s+", " ", str(value or "")).strip()
        if value and value.lower() not in {
            existing.lower() for existing in queries
        }:
            queries.append(value)

    # Customer demand and the problem being solved.
    if problem:
        add_query(f'"{problem}" Nigeria demand')
        add_query(f'"{problem}" Nigeria complaints')
        add_query(f'"{problem}" Nigeria existing solutions')
        add_query(f'"{problem}" Nigeria business costs')

    # Customer, buyer and market evidence.
    if customer_phrase:
        add_query(f'"{customer_phrase}" Nigeria pricing')
        add_query(f'"{customer_phrase}" Nigeria customers pay')
        add_query(f'"{customer_phrase}" Nigeria procurement')
        add_query(f'"{customer_phrase}" Nigeria complaints')

    # Pricing and competition for the proposed solution.
    if solution:
        add_query(f'"{solution}" Nigeria pricing')
        add_query(f'"{solution}" Nigeria competitors')
        add_query(f'"{solution}" Nigeria alternatives')
        add_query(f'"{solution}" Nigeria customers')
        add_query(f'"{solution}" Nigeria contract')

    # General commercial signals remain neutral across industries.
    topic = solution or problem or customer_phrase
    add_query(f'"{topic}" Nigeria market demand')
    add_query(f'"{topic}" Nigeria company')
    add_query(f'"{topic}" Nigeria cost')

    with ThreadPoolExecutor(max_workers=8) as executor:
        batches = executor.map(
            lambda query: search_news(query, max_results_per_query),
            queries,
        )

        for query, results in zip(queries, batches):
            for result in results:
                research.append({
                    "query": query,
                    **result,
                })

    return research


def validation_query_type(query):
    """Classify targeted validation queries by the evidence they seek."""
    text = str(query or "").lower()

    # Explicit problem and demand research takes priority over broad
    # commercial terms that may appear elsewhere in the query.
    if any(term in text for term in (
        "complaint",
        "complaints",
        "unresolved",
        "unmet demand",
        "market demand",
        "frequency",
        "workload",
        "losses",
        "frustration",
        "poor customer service",
        "customer support problems",
    )):
        return "demand"

    # Identify the customer, buyer, or person who controls the budget.
    if any(term in text for term in (
        "decision maker",
        "decision-maker",
        "buyer",
        "business owner",
        "paying customer",
        "target customer",
    )):
        return "customer"

    # Pricing, payments, and existing alternatives are commercial evidence.
    if any(term in text for term in (
        "pricing",
        "price",
        "cost",
        "payment",
        "paying",
        "customers pay",
        "subscription",
        "contract",
        "fee",
        "procurement",
        "competitor",
        "competitors",
        "alternative",
        "alternatives",
        "rival",
        "rivals",
        "existing platform",
        "existing solution",
    )):
        return "commercial"

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
    """Generate industry-neutral queries tailored to the candidate and gaps."""
    customer = str(candidate.get("target_customer") or "").strip()
    problem = str(candidate.get("problem") or "").strip()
    solution = str(candidate.get("solution") or "").strip()

    customer_phrase = commercial_customer_phrase(customer)
    topic = solution or problem or customer_phrase
    gap_text = " ".join(str(gap) for gap in (validation_gaps or [])).lower()

    queries = []

    def add_query(value):
        value = re.sub(r"\s+", " ", str(value or "")).strip()
        if value and value.lower() not in {
            existing.lower() for existing in queries
        }:
            queries.append(value)

    if "demand" in gap_text:
        if problem:
            add_query(f'"{problem}" Nigeria demand')
            add_query(f'"{problem}" Nigeria frequency')
            add_query(f'"{problem}" Nigeria complaints')
        if customer and problem:
            add_query(f'"{customer_phrase}" "{problem}" Nigeria')

    if "customer" in gap_text or "buyer" in gap_text:
        if customer:
            add_query(f'"{customer_phrase}" Nigeria buyer')
            add_query(f'"{customer_phrase}" Nigeria decision maker')
            add_query(f'"{customer_phrase}" Nigeria procurement')

    if "revenue" in gap_text or "pay" in gap_text or "pricing" in gap_text:
        add_query(f'"{topic}" Nigeria pricing')
        add_query(f'"{topic}" Nigeria customers pay')
        add_query(f'"{topic}" Nigeria contract')

    if "competition" in gap_text or "competitor" in gap_text:
        add_query(f'"{topic}" Nigeria competitors')
        add_query(f'"{topic}" Nigeria alternatives')
        if problem:
            add_query(f'"{problem}" Nigeria existing solution')

    if "unmet" in gap_text or "problem" in gap_text:
        if problem:
            add_query(f'"{problem}" Nigeria unresolved problems')
            add_query(f'"{problem}" Nigeria complaints')

    if "solution" in gap_text and solution:
        add_query(f'"{solution}" Nigeria reviews')
        add_query(f'"{solution}" Nigeria customer feedback')

    # Avoid returning an empty query list if the candidate has usable details.
    if not queries and topic:
        add_query(f'"{topic}" Nigeria market demand')
        add_query(f'"{topic}" Nigeria pricing')

    return queries


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
