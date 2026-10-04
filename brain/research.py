import requests
import xml.etree.ElementTree as ET


RESEARCH_QUERIES = [
    "problems Nigerians face",
    "business challenges Nigeria",
    "customers complaints Nigeria",
    "problems small businesses Nigeria",
    "services people need Nigeria",
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

        results.append({
            "title": title,
            "source": source,
            "link": item.findtext("link", ""),
            "description": item.findtext("description", ""),
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
