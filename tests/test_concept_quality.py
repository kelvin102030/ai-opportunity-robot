import unittest

from brain.opportunities import (
    _research_similarity,
    _cluster_research,
    generate_concrete_opportunities,
)


class ConceptQualityTests(unittest.TestCase):

    def test_unrelated_articles_are_not_grouped(self):
        research = [
            {
                "title": "Nigerian retailers lose money tracking inventory manually",
                "description": "Small shops struggle to monitor stock and prevent losses.",
                "query": "retail inventory problems Nigeria",
                "source": "Retail News",
                "link": "https://example.com/retail",
            },
            {
                "title": "Cybersecurity researchers discover a software vulnerability",
                "description": "Security teams warn about attacks against computer systems.",
                "query": "software security vulnerabilities",
                "source": "Security News",
                "link": "https://example.com/security",
            },
        ]

        clusters = _cluster_research(research, minimum_similarity=0.25)

        self.assertEqual(
            len(clusters),
            2,
            "Unrelated retail and cybersecurity stories should remain separate.",
        )

    def test_shared_query_words_alone_do_not_create_similarity(self):
        left = {
            "title": "Farmers struggle to store harvested maize",
            "description": "Poor storage causes crop losses.",
            "query": "business opportunities in Nigeria",
        }
        right = {
            "title": "Patients face long waits at urban clinics",
            "description": "Understaffed facilities delay medical treatment.",
            "query": "business opportunities in Nigeria",
        }

        self.assertEqual(
            _research_similarity(left, right),
            0,
            "Identical broad search queries must not make unrelated stories similar.",
        )

    def test_related_inventory_articles_can_be_grouped(self):
        research = [
            {
                "title": "Small retailers struggle with inventory tracking",
                "description": "Shop owners report stock errors and missing products.",
                "query": "retail inventory problems",
                "source": "Retail News",
                "link": "https://example.com/inventory-1",
            },
            {
                "title": "Retail shop owners seek better stock management tools",
                "description": "Manual inventory records lead to frequent stock discrepancies.",
                "query": "retail stock management",
                "source": "Business News",
                "link": "https://example.com/inventory-2",
            },
        ]

        clusters = _cluster_research(research, minimum_similarity=0.25)

        self.assertTrue(
            any(len(cluster) == 2 for cluster in clusters),
            "Stories about the same specific inventory problem should be groupable.",
        )

    def test_healthcare_articles_with_different_wording_can_be_grouped(self):
        research = [
            {
                "title": "Nigerian clinics face delays due to staff shortages",
                "description": "Patients experience long waits at understaffed healthcare facilities.",
                "query": "business opportunities in Nigeria",
                "source": "Health News",
            },
            {
                "title": "Urban hospitals investigate ways to reduce patient waiting times",
                "description": "Healthcare providers examine appointment scheduling and staffing.",
                "query": "business opportunities in Nigeria",
                "source": "Medical News",
            },
        ]

        clusters = _cluster_research(research, minimum_similarity=0.25)

        self.assertTrue(
            any(len(cluster) == 2 for cluster in clusters),
            "Related healthcare-delay reports should be groupable.",
        )

    def test_healthcare_and_inventory_articles_stay_separate(self):
        healthcare = {
            "title": "Nigerian clinics face delays due to staff shortages",
            "description": "Patients experience long waits at understaffed healthcare facilities.",
            "query": "business opportunities in Nigeria",
        }
        inventory = {
            "title": "Small shops adopt inventory management to reduce stock losses",
            "description": "Retailers struggle with manual stock records and inventory errors.",
            "query": "business opportunities in Nigeria",
        }

        self.assertLess(
            _research_similarity(healthcare, inventory),
            0.25,
            "Unrelated healthcare and inventory stories must not be grouped.",
        )

    def test_single_unrelated_articles_do_not_become_opportunities(self):
        research = [
            {
                "title": "Researchers study a rare marine species",
                "description": "Scientists document its migration patterns.",
                "query": "marine research",
                "source": "Science News",
                "link": "https://example.com/marine",
            },
            {
                "title": "Football club announces a new head coach",
                "description": "The club prepares for its next season.",
                "query": "football news",
                "source": "Sports News",
                "link": "https://example.com/football",
            },
        ]

        opportunities = generate_concrete_opportunities(research)

        self.assertEqual(
            opportunities,
            [],
            "Two unrelated singleton stories should not produce a business opportunity.",
        )



    def test_duplicate_coverage_counts_as_one_story(self):
        from brain.opportunities import _count_story_clusters

        reports = [
            {
                "title": "NCC fines Airtel over customer complaints",
            },
            {
                "title": "Airtel fined by NCC over customer complaints",
            },
        ]

        self.assertEqual(
            _count_story_clusters(reports),
            1,
            "Near-duplicate reports about one event should count as one story.",
        )

    def test_distinct_events_in_same_industry_remain_independent(self):
        from brain.opportunities import _count_story_clusters

        reports = [
            {
                "title": "Airtel launches new data plan for students",
            },
            {
                "title": "NCC investigates telecom operators over service quality",
            },
        ]

        self.assertEqual(
            _count_story_clusters(reports),
            2,
            "Different events in the same industry should remain separate.",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
