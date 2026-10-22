"""Regression tests for consistent independent-evidence scoring."""

import unittest

from brain.opportunities import _research_support_score
from brain.reasoning import analyze_candidate


class IndependentEvidenceScoringTests(unittest.TestCase):

    def test_analysis_preserves_precomputed_concept_score(self):
        candidate = {
            "signal": "research_concept",
            "concept": "Customer stock shortage monitoring",
            "problem": "Retailers struggle with repeated stock shortages.",
            "evidence_count": 5,
            "source_independence": 0.2,
            "opportunity_score": _research_support_score(1, 0.2),
            "confidence": "low",
        }

        analysis = analyze_candidate(candidate)

        self.assertEqual(
            analysis.opportunity_score,
            candidate["opportunity_score"],
            "Analysis should preserve the independently calculated score "
            "of a concrete research concept.",
        )
        self.assertEqual(
            analysis.confidence,
            round(candidate["opportunity_score"] / 100.0, 2),
            "Confidence should agree with the independently calculated score.",
        )

    def test_independent_evidence_scores_higher_than_duplicate_coverage(self):
        independent_score = _research_support_score(5, 1.0)
        duplicate_score = _research_support_score(1, 0.2)

        self.assertGreater(independent_score, duplicate_score)

    def test_confidence_calculation_remains_bounded(self):
        from brain.reasoning import _calculate_confidence

        for independence in (-1, 0, 0.5, 1, 2):
            confidence = _calculate_confidence({
                "evidence_count": 5,
                "source_independence": independence,
            })

            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
