import pytest

import web


@pytest.fixture
def isolated_robot_state():
    original = web.robot_state.copy()

    web.robot_state.update({
        "status": "ready",
        "message": "Test starting.",
        "running": False,
        "result": None,
        "build_context": None,
        "app_build": None,
    })

    yield web.robot_state

    web.robot_state.clear()
    web.robot_state.update(original)


def approved_context():
    return {
        "status": "complete",
        "opportunity": {
            "title": "Test Opportunity",
            "problem": "A test problem",
            "solution": "A test solution",
        },
        "validation": {
            "recommendation": "READY FOR MVP VALIDATION",
            "demand": 80,
            "customer": 75,
            "revenue": 80,
            "competition": 60,
            "build_feasibility": 80,
            "risk": 20,
            "readiness": 85,
            "evidence_breakdown": {
                "payment_evidence": 2,
                "pricing_evidence": 2,
                "competition_evidence": 2,
                "unmet_need_evidence": 3,
            },
        },
        "build_plan": {
            "build_eligibility": "MVP BUILD APPROVED",
            "mvp_features": ["Record and track a request"],
        },
    }


def test_build_worker_failure_resets_state(
    isolated_robot_state, monkeypatch
):
    def fail_generation(**kwargs):
        raise RuntimeError("Simulated provider failure")

    monkeypatch.setattr(
        "brain.app_builder.generate_application",
        fail_generation,
    )

    web.robot_state["running"] = True
    web.robot_state["status"] = "generating_app"

    web.run_app_build(approved_context())

    assert web.robot_state["running"] is False
    assert web.robot_state["status"] == "app_build_error"
    assert web.robot_state["app_build"]["status"] == "error"
    assert (
        web.robot_state["app_build"]["message"]
        == "Simulated provider failure"
    )

    with web.app.test_client() as client:
        response = client.get("/api/status")

    assert response.status_code == 200
    status = response.get_json()
    assert status["running"] is False
    assert status["status"] == "app_build_error"
    assert status["app_build"]["status"] == "error"


def test_generation_can_be_retried_after_failure(
    isolated_robot_state, monkeypatch
):
    context = approved_context()
    web.robot_state["build_context"] = context
    web.robot_state["running"] = False
    web.robot_state["status"] = "app_build_error"
    web.robot_state["app_build"] = {
        "status": "error",
        "message": "Previous attempt failed.",
    }

    started = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            started.append(self)

    monkeypatch.setattr(web.threading, "Thread", FakeThread)

    with web.app.test_client() as client:
        response = client.post("/api/generate-app")

    assert response.status_code == 202
    assert len(started) == 1
    assert web.robot_state["running"] is True
    assert web.robot_state["status"] == "generating_app"
    assert web.robot_state["app_build"]["status"] == "generating"

    # The fake thread never executes the real generator.
    # Restore a stopped state for fixture cleanup.
    web.robot_state["running"] = False
