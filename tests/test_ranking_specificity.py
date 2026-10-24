import unittest
from types import SimpleNamespace

from brain.ranking import (
    _is_generic_research_lead,
    best_opportunity,
    rank_opportunities,
)


class OpportunitySpecificityTests(unittest.TestCase):

    def test_digital_services_is_classified_as_generic(self):
        broad = SimpleNamespace(
            title="Opportunity: Digital Services",
            problem=(
                "A growing digital behavior or service need may support "
                "a new or improved online product."
            ),
            opportunity_score=98,
            evidence_count=20,
            confidence=0.98,
        )

        self.assertTrue(_is_generic_research_lead(broad))

    def test_specific_opportunity_can_outrank_higher_scoring_generic_lead(self):
        broad = SimpleNamespace(
            title="Opportunity: Digital Services",
            problem="A growing digital behavior or service need.",
            opportunity_score=98,
            evidence_count=20,
            confidence=0.98,
        )

        specific = SimpleNamespace(
            title="Smart Inventory Management for Small Retailers",
            problem=(
                "Small retailers may lose money when stock records are "
                "inaccurate. The impact still needs validation."
            ),
            opportunity_score=72,
            evidence_count=5,
            confidence=0.72,
        )

        ranked = rank_opportunities([broad, specific])

        self.assertIs(ranked[0], specific)
        self.assertIs(best_opportunity([broad, specific]), specific)

    def test_specificity_does_not_replace_score_comparison_within_group(self):
        first = SimpleNamespace(
            title="Smart Inventory Management for Small Retailers",
            problem="Retail stock discrepancies need investigation.",
            opportunity_score=72,
            evidence_count=5,
            confidence=0.72,
        )

        second = SimpleNamespace(
            title="Clinic Appointment and Queue Management",
            problem="Clinic appointment delays need investigation.",
            opportunity_score=85,
            evidence_count=4,
            confidence=0.85,
        )

        ranked = rank_opportunities([first, second])

        self.assertIs(ranked[0], second)

    def test_generic_research_lead_is_still_flagged(self):
        lead = SimpleNamespace(
            title="Research Lead: Emerging Market Trend",
            problem="A changing market or behavior pattern.",
            opportunity_score=90,
            evidence_count=10,
            confidence=0.90,
        )

        self.assertTrue(_is_generic_research_lead(lead))


if __name__ == "__main__":
    unittest.main()
