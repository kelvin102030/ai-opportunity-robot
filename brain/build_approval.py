def _is_number(value):
    """Accept real numeric values but reject booleans and malformed input."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def approve_mvp_build(validation):
    """
    Decide whether a validated opportunity is strong enough
    to begin MVP construction.

    Invalid or missing values fail closed: they cannot approve a build.
    """

    if not isinstance(validation, dict):
        validation = {}

    breakdown = validation.get("evidence_breakdown", {})
    if not isinstance(breakdown, dict):
        breakdown = {}

    def at_least(value, threshold):
        return _is_number(value) and value >= threshold

    def at_most(value, threshold):
        return _is_number(value) and value <= threshold

    checks = {
        "recommendation": (
            validation.get("recommendation")
            == "READY FOR MVP VALIDATION"
        ),
        "demand": at_least(validation.get("demand"), 70),
        "customer": at_least(validation.get("customer"), 60),
        "revenue": at_least(validation.get("revenue"), 70),
        "competition": at_least(validation.get("competition"), 40),
        "build_feasibility": at_least(
            validation.get("build_feasibility"), 60
        ),
        "risk": at_most(validation.get("risk"), 40),
        "readiness": at_least(validation.get("readiness"), 75),
        "payment_evidence": at_least(
            breakdown.get("payment_evidence"), 1
        ),
        "pricing_evidence": at_least(
            breakdown.get("pricing_evidence"), 1
        ),
        "competition_evidence": at_least(
            breakdown.get("competition_evidence"), 1
        ),
        "unmet_need_evidence": at_least(
            breakdown.get("unmet_need_evidence"), 2
        ),
    }

    approved = all(checks.values())

    failed_checks = [
        name for name, passed in checks.items()
        if not passed
    ]

    return {
        "approved": approved,
        "status": (
            "MVP BUILD APPROVED"
            if approved
            else "MVP BUILD NOT APPROVED"
        ),
        "checks": checks,
        "failed_checks": failed_checks,
    }
