"""Tests for static review of generated application projects."""

import zipfile

import pytest

from brain import generated_app_review as review


@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    root = tmp_path / "generated_apps"
    root.mkdir()

    monkeypatch.setattr(review, "GENERATED_ROOT", root)

    return root


def make_project(root, name="sample-app", files=None):
    project = root / name
    project.mkdir()

    if files is None:
        files = {
            "README.md": "# Sample app\n",
            "main.py": "def main():\n    return 'hello'\n",
            "tests/test_app.py": "def test_example():\n    assert True\n",
        }

    for filename, content in files.items():
        target = project / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    archive = root / f"{name}.zip"

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(project.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(project))

    return project, archive


def test_reviews_valid_project_without_executing_code(isolated_workspace):
    project, archive = make_project(isolated_workspace)

    result = review.review_generated_project("sample-app")

    assert result["review_passed"] is True
    assert result["status"] == "static_review_passed"
    assert result["files_reviewed"] == 3
    assert result["python_files_checked"] == 2
    assert result["has_readme"] is True
    assert result["has_tests"] is True
    assert result["archive_valid"] is True
    assert result["tests_executed"] is False
    assert result["play_store_ready"] is False


def test_detects_python_syntax_errors(isolated_workspace):
    make_project(
        isolated_workspace,
        files={
            "README.md": "# Sample app\n",
            "main.py": "def broken(:\n    pass\n",
            "tests/test_app.py": "def test_example():\n    assert True\n",
        },
    )

    result = review.review_generated_project("sample-app")

    assert result["review_passed"] is False
    assert result["status"] == "static_review_failed"
    assert result["syntax_errors"]
    assert result["syntax_errors"][0]["file"] == "main.py"


def test_warns_when_readme_and_tests_are_missing(isolated_workspace):
    make_project(
        isolated_workspace,
        files={"main.py": "print('hello')\n"},
    )

    result = review.review_generated_project("sample-app")

    assert result["has_readme"] is False
    assert result["has_tests"] is False
    assert any("README.md is missing" in warning for warning in result["warnings"])
    assert any("test file" in warning for warning in result["warnings"])


def test_detects_missing_archive(isolated_workspace):
    project = isolated_workspace / "sample-app"
    project.mkdir()
    (project / "main.py").write_text("pass\n", encoding="utf-8")

    result = review.review_generated_project("sample-app")

    assert result["archive_valid"] is False
    assert result["review_passed"] is False
    assert any("missing" in warning.lower() for warning in result["warnings"])


def test_detects_archive_content_mismatch(isolated_workspace):
    project, archive = make_project(isolated_workspace)

    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("different.py", "pass\n")

    result = review.review_generated_project("sample-app")

    assert result["archive_valid"] is False
    assert result["review_passed"] is False


def test_rejects_missing_project(isolated_workspace):
    with pytest.raises(review.AppReviewError, match="does not exist"):
        review.review_generated_project("missing-app")


def test_rejects_invalid_project_name(isolated_workspace):
    with pytest.raises(review.AppReviewError, match="Invalid project name"):
        review.review_generated_project("../outside")


def test_reports_invalid_utf8_python_file(isolated_workspace):
    project, archive = make_project(isolated_workspace)

    (project / "main.py").write_bytes(b"\xff\xfe\xfa")

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(project.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(project))

    result = review.review_generated_project("sample-app")

    assert result["review_passed"] is False
    assert any(
        "UTF-8" in item["error"]
        for item in result["syntax_errors"]
    )



def test_reports_missing_application_entry_point(isolated_workspace):
    make_project(
        isolated_workspace,
        files={
            "README.md": "# Sample app\\n",
            "notes.txt": "Project notes only.\\n",
        },
    )

    result = review.review_generated_project("sample-app")

    assert "has_entry_point" in result
    assert result["has_entry_point"] is False
    assert any(
        "entry point" in warning.lower()
        for warning in result["warnings"]
    )


def test_reports_project_exceeding_workspace_file_limit(
    isolated_workspace,
):
    files = {
        "README.md": "# Sample app\\n",
        "main.py": "def main():\\n    return True\\n",
    }

    files.update({
        f"module_{index}.txt": "data\\n"
        for index in range(101)
    })

    make_project(isolated_workspace, files=files)

    result = review.review_generated_project("sample-app")

    assert result["file_limit_exceeded"] is True
    assert result["review_passed"] is False
    assert any(
        "file limit" in warning.lower()
        for warning in result["warnings"]
    )


def test_static_review_never_claims_execution_or_store_readiness(
    isolated_workspace,
):
    make_project(isolated_workspace)

    result = review.review_generated_project("sample-app")

    assert result["tests_executed"] is False
    assert result["play_store_ready"] is False


def test_reports_individual_file_exceeding_workspace_limit(
    isolated_workspace,
):
    from brain.project_workspace import MAX_FILE_BYTES

    make_project(
        isolated_workspace,
        files={
            "README.md": "# Sample app\n",
            "main.py": "x" * (MAX_FILE_BYTES + 1),
        },
    )

    result = review.review_generated_project("sample-app")

    assert result["oversized_files"] == ["main.py"]
    assert result["review_passed"] is False
    assert any(
        "file size limit" in warning.lower()
        for warning in result["warnings"]
    )
