import unittest

from brain.opportunities import generate_concrete_opportunities
from brain.reasoning import analyze_candidate


class ResearchSpecificTitleTests(unittest.TestCase):
    def setUp(self):
        self.research = [
            {
                "title": "Small retailers struggle with inventory tracking",
                "description": "Shop owners report stock errors and missing products.",
                "source": "Retail News",
                "query": "retail inventory problems",
                "link": "https://example.com/retail1",
            },
            {
                "title": "Retail shop owners seek better stock management tools",
                "description": (
                    "Manual inventory records lead to frequent stock discrepancies."
                ),
                "source": "Business News",
                "query": "retail stock management",
                "link": "https://example.com/retail2",
            },
            {
                "title": "Nigerian clinics face delays due to staff shortages",
                "description": (
                    "Patients experience long waits at understaffed healthcare facilities."
                ),
                "source": "Health News",
                "query": "clinic waiting times",
                "link": "https://example.com/health1",
            },
            {
                "title": "Hospitals investigate ways to reduce patient waiting times",
                "description": (
                    "Healthcare providers examine appointment scheduling and staffing."
                ),
                "source": "Medical News",
                "query": "hospital appointment delays",
                "link": "https://example.com/health2",
            },
        ]
        self.results = [
            analyze_candidate(candidate)
            for candidate in generate_concrete_opportunities(self.research)
        ]

    def test_inventory_research_gets_specific_title_and_solution(self):
        inventory = next(
            result for result in self.results
            if "inventory" in result.title.lower()
        )
        self.assertEqual(
            inventory.title,
            "Smart Inventory Management for Small Retailers",
        )
        self.assertIn("stock", inventory.solution.lower())
        self.assertIn("retail", inventory.target_customer.lower())

    def test_clinic_research_gets_specific_title_and_solution(self):
        clinic = next(
            result for result in self.results
            if "clinic" in result.title.lower()
        )
        self.assertEqual(
            clinic.title,
            "Clinic Appointment and Queue Management",
        )
        self.assertIn("appointment", clinic.solution.lower())
        self.assertIn("clinic", clinic.target_customer.lower())

    def test_inventory_and_clinic_opportunities_remain_distinct(self):
        titles = {result.title for result in self.results}
        self.assertIn("Smart Inventory Management for Small Retailers", titles)
        self.assertIn("Clinic Appointment and Queue Management", titles)
        self.assertNotEqual(
            self.results[0].solution,
            self.results[1].solution,
        )

    def test_revenue_models_are_hypotheses_not_payment_claims(self):
        for result in self.results:
            self.assertIn("Test", result.revenue_model)
            self.assertIn("subscription", result.revenue_model.lower())


if __name__ == "__main__":
    unittest.main()
