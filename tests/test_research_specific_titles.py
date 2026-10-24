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



    def test_payment_reconciliation_research_gets_specific_title_and_solution(self):
        candidate = {
            "signal": "research_concept",
            "concept": "Payment Transaction Reconciliation",
            "problem": "Research discusses reconciliation problems.",
            "evidence_count": 2,
            "source_independence": 1.0,
            "opportunity_score": 64,
            "matched_keywords": [],
            "evidence_items": [
                {
                    "title": "Small businesses struggle to reconcile payments with sales records",
                    "description": "Owners manually compare transaction records with daily sales.",
                    "source": "Business News",
                    "query": "payment reconciliation",
                    "link": "https://example.com/pay1",
                },
                {
                    "title": "Retailers report payment mismatches in transaction records",
                    "description": "Unmatched payments make daily sales reconciliation time-consuming.",
                    "source": "Finance News",
                    "query": "transaction mismatch",
                    "link": "https://example.com/pay2",
                },
            ],
        }

        result = analyze_candidate(candidate)
        self.assertEqual(
            result.title,
            "Payment Reconciliation for Small Businesses",
        )
        self.assertIn("reconcil", result.problem.lower())
        self.assertIn("transaction", result.solution.lower())
        self.assertIn("small businesses", result.target_customer.lower())
        self.assertIn("willingness to pay", result.revenue_model.lower())


if __name__ == "__main__":
    unittest.main()
