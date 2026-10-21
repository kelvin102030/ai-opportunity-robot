import json
import zipfile

import pytest

from brain import app_builder


def approved_validation():
    return {
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
    }


def approved_plan():
    return {
        "build_eligibility": "MVP BUILD APPROVED",
        "mvp_features": ["Record and track a request"],
    }


def valid_ai_response():
    return json.dumps({
        "files": {
            "README.md": "# Sample MVP\n",
            "main.py": "def run():\n    return 'ok'\n",
            "tests/test_app.py": (
                "from main import run\n"
                "def test_run():\n"
                "    assert run() == 'ok'\n"
            ),
        }
    })


@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(
        app_builder,
        "create_project",
        lambda name, files: real_create_project(
            tmp_path, name, files
        ),
    )

    monkeypatch.setattr(
        app_builder,
        "archive_project",
        lambda name: real_archive_project(tmp_path, name),
    )

    monkeypatch.setattr(
        app_builder,
        "review_generated_project",
        lambda name: {
            "project_name": name,
            "review_passed": True,
            "status": "static_review_passed",
            "tests_executed": False,
            "play_store_ready": False,
            "warnings": [],
        },
    )


def real_create_project(root, name, files):
    from pathlib import Path
    from brain import project_workspace

    destination = Path(root) / name

    if destination.exists():
        raise project_workspace.WorkspaceError(
            "Project already exists."
        )

    destination.mkdir()

    for filename, content in files.items():
        relative = project_workspace._validate_relative_path(filename)
        encoded = project_workspace._check_content(content)
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)

    return destination


def real_archive_project(root, name):
    from pathlib import Path

    project = Path(root) / name
    archive = Path(root) / f"{name}.zip"

    with zipfile.ZipFile(archive, "w") as bundle:
        for path in project.rglob("*"):
            if path.is_file():
                bundle.write(path, path.relative_to(project))

    return archive


def test_generates_and_archives_project(isolated_workspace):
    def fake_provider(task, context):
        assert "Return ONLY valid JSON" in task
        return valid_ai_response()

    result = app_builder.generate_application(
        "sample-app",
        {"name": "Sample opportunity"},
        approved_validation(),
        approved_plan(),
        provider=fake_provider,
    )

    assert result["status"] == "generated_not_executed"
    assert result["tests_run"] is False
    assert result["play_store_ready"] is False
    assert result["files_created"] == 3
    assert result["static_review_passed"] is True
    assert result["static_review"]["status"] == "static_review_passed"
    assert result["static_review"]["tests_executed"] is False

    from pathlib import Path

    project = Path(result["project_path"])
    archive = Path(result["archive_path"])

    assert (project / "main.py").is_file()
    assert archive.is_file()

    with zipfile.ZipFile(archive) as bundle:
        assert "main.py" in bundle.namelist()


def test_rejects_unapproved_opportunity():
    called = []

    def fake_provider(task, context):
        called.append(True)
        return valid_ai_response()

    validation = approved_validation()
    validation["demand"] = 20

    with pytest.raises(app_builder.AppBuildError, match="not approved"):
        app_builder.generate_application(
            "sample-app",
            {"name": "Sample"},
            validation,
            approved_plan(),
            provider=fake_provider,
        )

    assert called == []


def test_rejects_unapproved_build_plan():
    with pytest.raises(app_builder.AppBuildError, match="build plan"):
        app_builder.generate_application(
            "sample-app",
            {"name": "Sample"},
            approved_validation(),
            {"build_eligibility": "MVP BUILD NOT APPROVED"},
            provider=lambda task, context: valid_ai_response(),
        )


@pytest.mark.parametrize(
    "response",
    [
        "not JSON",
        "[]",
        "{}",
        '{"files": {}}',
        '{"files": ["main.py"]}',
        '```json\n{"files": {}}\n```',
    ],
)
def test_rejects_invalid_ai_responses(response):
    with pytest.raises(app_builder.AppBuildError):
        app_builder.generate_application(
            "sample-app",
            {"name": "Sample"},
            approved_validation(),
            approved_plan(),
            provider=lambda task, context: response,
        )


def test_rejects_unsafe_generated_paths(isolated_workspace):
    response = json.dumps({
        "files": {
            "../outside.txt": "unsafe",
        }
    })

    with pytest.raises(app_builder.AppBuildError, match="workspace security"):
        app_builder.generate_application(
            "unsafe-app",
            {"name": "Sample"},
            approved_validation(),
            approved_plan(),
            provider=lambda task, context: response,
        )


def test_rejects_generated_secrets(isolated_workspace):
    response = json.dumps({
        "files": {
            "config.py": 'api_key = "abcdefghijklmnop123456"',
        }
    })

    with pytest.raises(app_builder.AppBuildError, match="workspace security"):
        app_builder.generate_application(
            "secret-app",
            {"name": "Sample"},
            approved_validation(),
            approved_plan(),
            provider=lambda task, context: response,
        )
