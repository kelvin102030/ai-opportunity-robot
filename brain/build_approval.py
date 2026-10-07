def approve_mvp_build(validation):
    """
    Decide whether a validated opportunity is strong enough
    to begin MVP construction.
    """

    breakdown = validation.get("evidence_breakdown", {})

    checks = {
        "recommendation": validation.get("recommendation") == "READY FOR MVP VALIDATION",
        "demand": validation.get("demand", 0) >= 70,
        "customer": validation.get("customer", 0) >= 60,
        "revenue": validation.get("revenue", 0) >= 70,
        "competition": validation.get("competition", 0) >= 40,
        "build_feasibility": validation.get("build_feasibility", 0) >= 60,
        "risk": validation.get("risk", 100) <= 40,
        "readiness": validation.get("readiness", 0) >= 75,
        "payment_evidence": breakdown.get("payment_evidence", 0) >= 1,
        "pricing_evidence": breakdown.get("pricing_evidence", 0) >= 1,
        "competition_evidence": breakdown.get("competition_evidence", 0) >= 1,
        "unmet_need_evidence": breakdown.get("unmet_need_evidence", 0) >= 2,
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
