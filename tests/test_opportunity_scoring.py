import unittest

from brain.reasoning import analyze_candidate
from brain.ranking import rank_opportunities
from brain.build_approval import approve_mvp_build


class OpportunityScoringTests(unittest.TestCase):

    def setUp(self):
        self.shared = {
            "evidence_count": 4,
            "source_independence": 0.75,
            "matched_keywords": ["customer", "business"],
            "evidence_items": [
                {"title": f"Evidence item {i}"}
                for i in range(1, 5)
            ],
        }

    def test_equivalent_evidence_gets_comparable_scores(self):
        theme = analyze_candidate({
            **self.shared,
            "signal": "customer_service",
            "problem": "Businesses struggle to resolve customer complaints.",
            "impact_score": 4,
            "solution_potential": 4,
        })

        concept = analyze_candidate({
            **self.shared,
            "signal": "research_concept",
            "concept": "Customer Complaint Tracking",
            "problem": "Research points to customer complaint problems.",
        })

        self.assertEqual(
            theme.opportunity_score,
            concept.opportunity_score,
            "Equivalent evidence should not receive different scores "
            "just because one candidate lacks optional heuristic fields.",
        )

    def test_confidence_reflects_evidence_not_missing_heuristics(self):
        theme = analyze_candidate({
            **self.shared,
            "signal": "customer_service",
            "problem": "Businesses struggle to resolve customer complaints.",
            "impact_score": 4,
            "solution_potential": 4,
        })

        concept = analyze_candidate({
            **self.shared,
            "signal": "research_concept",
            "concept": "Customer Complaint Tracking",
            "problem": "Research points to customer complaint problems.",
        })

        self.assertEqual(
            theme.confidence,
            concept.confidence,
            "Confidence should not fall merely because impact and "
            "solution-potential estimates are absent.",
        )

    def test_ranking_does_not_penalize_missing_heuristic_fields(self):
        theme = analyze_candidate({
            **self.shared,
            "signal": "customer_service",
            "problem": "Businesses struggle to resolve customer complaints.",
            "impact_score": 4,
            "solution_potential": 4,
        })

        concept = analyze_candidate({
            **self.shared,
            "signal": "research_concept",
            "concept": "Customer Complaint Tracking",
            "problem": "Research points to customer complaint problems.",
        })

        ranked = rank_opportunities([concept, theme])

        self.assertEqual(
            ranked[0].opportunity_score,
            ranked[1].opportunity_score,
        )
        self.assertEqual(
            ranked[0].confidence,
            ranked[1].confidence,
        )

    def test_weak_evidence_cannot_approve_mvp(self):
        weak_validation = {
            "recommendation": "RESEARCH MORE BEFORE BUILDING",
            "demand": 20,
            "customer": 20,
            "revenue": 10,
            "competition": 0,
            "build_feasibility": 50,
            "risk": 80,
            "readiness": 20,
            "evidence_breakdown": {
                "payment_evidence": 0,
                "pricing_evidence": 0,
                "competition_evidence": 0,
                "unmet_need_evidence": 0,
            },
        }

        result = approve_mvp_build(weak_validation)

        self.assertFalse(result["approved"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class BusinessValidationEvidenceTests(unittest.TestCase):

    def test_willingness_to_pay_is_not_actual_payment(self):
        from brain.business_validation import (
            _commercial_evidence_breakdown,
            _score_revenue,
            _web_evidence_type,
        )

        item = {
            "title": "Small businesses would pay for customer support software",
            "description": "Owners stated willingness to pay for a service.",
            "validation_type": "commercial",
        }

        breakdown = _commercial_evidence_breakdown([item])
        self.assertEqual(breakdown["payment_evidence"], 0)
        self.assertEqual(breakdown["willingness_to_pay_evidence"], 1)
        self.assertLessEqual(_score_revenue([item]), 30)

        web = _web_evidence_type({
            "text": (
                "Small businesses would pay for customer support software."
            )
        })
        self.assertFalse(web["payment"])
        self.assertTrue(web["willingness_to_pay"])

    def test_pricing_alone_does_not_establish_payment(self):
        from brain.business_validation import (
            _commercial_evidence_breakdown,
            _score_revenue,
        )

        items = [
            {
                "title": "Customer support software pricing",
                "description": "Subscription price is ₦10,000 per month.",
                "validation_type": "commercial",
            },
            {
                "title": "Monthly fee for customer service platform",
                "description": "Annual subscription pricing is available.",
                "validation_type": "commercial",
            },
        ]

        breakdown = _commercial_evidence_breakdown(items)
        self.assertEqual(breakdown["payment_evidence"], 0)
        self.assertGreaterEqual(breakdown["pricing_evidence"], 1)
        self.assertLessEqual(_score_revenue(items), 25)

    def test_reported_paid_customers_are_classified_as_claims(self):
        from brain.business_validation import (
            _commercial_evidence_breakdown,
            _score_revenue,
            _web_evidence_type,
        )

        item = {
            "title": "Customer support software gains paying customers",
            "description": "The company reports paying customers.",
            "validation_type": "commercial",
        }

        breakdown = _commercial_evidence_breakdown([item])
        self.assertEqual(breakdown["payment_evidence"], 1)
        self.assertGreater(_score_revenue([item]), 30)

        web = _web_evidence_type({
            "text": (
                "Customer support software gains paying customers."
            )
        })
        self.assertTrue(web["payment"])
        self.assertFalse(web["willingness_to_pay"])

    def test_mvp_gate_rejects_willingness_without_payment(self):
        from brain.build_approval import approve_mvp_build

        validation = {
            "recommendation": "READY FOR MVP VALIDATION",
            "demand": 90,
            "customer": 90,
            "revenue": 90,
            "competition": 80,
            "build_feasibility": 80,
            "risk": 10,
            "readiness": 90,
            "evidence_breakdown": {
                "payment_evidence": 0,
                "willingness_to_pay_evidence": 5,
                "pricing_evidence": 3,
                "competition_evidence": 3,
                "unmet_need_evidence": 3,
            },
        }

        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])
        self.assertIn("payment_evidence", result["failed_checks"])


    def test_vendor_page_does_not_automatically_count_as_competition(self):
        from brain.business_validation import _web_evidence_type

        result = _web_evidence_type({
            "text": "Customer support software helps businesses handle inquiries."
        })

        self.assertTrue(result["vendor"])
        self.assertFalse(result["competition"])

    def test_explicit_competitor_reference_counts_as_competition(self):
        from brain.business_validation import _web_evidence_type

        result = _web_evidence_type({
            "text": (
                "Customer support software competes with other providers "
                "and existing platforms."
            )
        })

        self.assertTrue(result["competition"])

    def test_willingness_to_pay_does_not_create_competition_evidence(self):
        from brain.business_validation import _web_evidence_type

        result = _web_evidence_type({
            "text": "Businesses would pay for customer support software."
        })

        self.assertTrue(result["willingness_to_pay"])
        self.assertFalse(result["competition"])

class ApprovalInputSafetyTests(unittest.TestCase):

    def setUp(self):
        self.valid = {
            "recommendation": "READY FOR MVP VALIDATION",
            "demand": 80,
            "customer": 80,
            "revenue": 80,
            "competition": 80,
            "build_feasibility": 80,
            "risk": 20,
            "readiness": 80,
            "evidence_breakdown": {
                "payment_evidence": 1,
                "pricing_evidence": 1,
                "competition_evidence": 1,
                "unmet_need_evidence": 2,
            },
        }

    def test_valid_input_still_approves(self):
        self.assertTrue(approve_mvp_build(self.valid)["approved"])

    def test_text_score_fails_closed(self):
        validation = {**self.valid, "demand": "unknown"}
        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])
        self.assertIn("demand", result["failed_checks"])

    def test_none_score_fails_closed(self):
        validation = {**self.valid, "revenue": None}
        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])
        self.assertIn("revenue", result["failed_checks"])

    def test_missing_scores_fail_closed(self):
        result = approve_mvp_build({})
        self.assertFalse(result["approved"])

    def test_missing_evidence_breakdown_fails_closed(self):
        validation = {**self.valid}
        validation.pop("evidence_breakdown")
        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])
        self.assertIn("payment_evidence", result["failed_checks"])
        self.assertIn("pricing_evidence", result["failed_checks"])

    def test_malformed_evidence_breakdown_fails_closed(self):
        validation = {**self.valid, "evidence_breakdown": None}
        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])

    def test_boolean_score_cannot_qualify(self):
        validation = {**self.valid, "demand": True}
        result = approve_mvp_build(validation)
        self.assertFalse(result["approved"])
        self.assertIn("demand", result["failed_checks"])

    def test_non_dictionary_input_fails_closed(self):
        result = approve_mvp_build(None)
        self.assertFalse(result["approved"])


class PricingRegexRegressionTests(unittest.TestCase):

    def test_currency_prices_are_detected_without_pricing_keywords(self):
        from brain.business_validation import _web_evidence_type

        examples = [
            "The monthly price is ₦5,000",
            "The monthly price is ₦ 5,000",
            "The subscription costs $20",
            "The service costs $ 20.50",
        ]

        for text in examples:
            with self.subTest(text=text):
                result = _web_evidence_type({"text": text})
                self.assertTrue(result["pricing"])

    def test_written_currency_amounts_are_detected_as_web_pricing(self):
        from brain.business_validation import _web_evidence_type

        examples = [
            "The service costs 5000 naira",
            "The service costs 20 dollars",
        ]

        for text in examples:
            with self.subTest(text=text):
                result = _web_evidence_type({"text": text})
                self.assertTrue(result["pricing"])

    def test_naira_and_dollar_amounts_count_as_pricing_evidence(self):
        from brain.business_validation import _score_revenue

        examples = [
            {"title": "Service information", "description": "₦5,000"},
            {"title": "Service information", "description": "₦ 5,000"},
            {"title": "Service information", "description": "$20"},
            {"title": "Service information", "description": "5000 naira"},
            {"title": "Service information", "description": "20 dollars"},
        ]

        for item in examples:
            with self.subTest(item=item):
                self.assertGreaterEqual(_score_revenue([item]), 15)

    def test_pricing_does_not_automatically_prove_payment(self):
        from brain.business_validation import (
            _commercial_evidence_breakdown,
        )

        item = {
            "title": "Service information",
            "description": "The service costs ₦5,000 per month.",
            "validation_type": "commercial",
        }

        result = _commercial_evidence_breakdown([item])

        self.assertGreaterEqual(result["pricing_evidence"], 1)
        self.assertEqual(result["payment_evidence"], 0)
