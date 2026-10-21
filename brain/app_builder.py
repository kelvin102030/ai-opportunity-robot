"""Generate application source files through the configured AI provider."""

import json
import re

from brain.coder_ai import ask_ai
from brain.generated_app_review import review_generated_project
from brain.project_workspace import (
    WorkspaceError,
    archive_project,
    create_project,
)


class AppBuildError(ValueError):
    """Raised when an application cannot be safely generated."""


def _safe_project_name(name):
    if not isinstance(name, str):
        raise AppBuildError("Project name must be text.")

    slug = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        name,
    ).strip("-_").lower()

    if not slug or len(slug) > 60:
        raise AppBuildError("Invalid project name.")

    return slug


def _extract_files(response):
    """Parse the AI response as a JSON object containing source files."""

    if not isinstance(response, str):
        raise AppBuildError("AI response must be text.")

    response = response.strip()

    # Accept a plain JSON response or a single JSON Markdown code block.
    if response.startswith("```"):
        lines = response.splitlines()

        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise AppBuildError("AI returned an incomplete code block.")

        response = "\n".join(lines[1:-1]).strip()

    try:
        payload = json.loads(response)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AppBuildError(
            "AI response was not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise AppBuildError("AI response must be a JSON object.")

    files = payload.get("files")

    if not isinstance(files, dict) or not files:
        raise AppBuildError(
            "AI response must contain a non-empty files object."
        )

    return files


def generate_application(
    project_name,
    opportunity,
    validation,
    build_plan,
    provider=None,
):
    """
    Generate and archive application source files.

    The caller must supply an explicit approval result from
    brain.build_approval.approve_mvp_build().

    Generated code is written to disk but is never executed here.
    """

    if not isinstance(opportunity, dict):
        raise AppBuildError("Opportunity details must be a dictionary.")

    if not isinstance(validation, dict):
        raise AppBuildError("Validation results must be a dictionary.")

    if not isinstance(build_plan, dict):
        raise AppBuildError("Build plan must be a dictionary.")

    # Re-evaluate the actual evidence and scores instead of trusting
    # a caller-supplied boolean or a fabricated approval flag.
    from brain.build_approval import approve_mvp_build

    approval = approve_mvp_build(validation)

    if not approval["approved"]:
        raise AppBuildError(
            "Application generation denied: opportunity is not approved. "
            "Failed checks: " + ", ".join(approval["failed_checks"])
        )

    if build_plan.get("build_eligibility") != "MVP BUILD APPROVED":
        raise AppBuildError(
            "Application generation denied: build plan is not approved."
        )

    slug = _safe_project_name(project_name)

    task = f"""
Generate a real, minimal, runnable MVP application.

Project name: {slug}

Business opportunity:
{json.dumps(opportunity, ensure_ascii=False, indent=2)}

Validated business findings:
{json.dumps(validation, ensure_ascii=False, indent=2)}

Approved build plan:
{json.dumps(build_plan, ensure_ascii=False, indent=2)}

Requirements:
1. Generate actual source files, not just a plan or explanation.
2. Implement a coherent, minimal version of the main user workflow.
3. Include a README with setup and run instructions.
4. Include appropriate automated tests for the generated application.
5. Include dependency information where needed.
6. Use relative file paths.
7. Do not include API keys, passwords, access tokens, or private keys.
8. Do not include hidden files, environment files, or Git metadata.
9. Do not claim that tests were run.
10. Do not include binary files or base64-encoded binaries.
11. Keep the MVP small enough to review and test.
12. If a mobile app is appropriate, explain its required build tools.
    Do not pretend that a Python web app is already a native Android app.

Return ONLY valid JSON in this exact shape:
{{
  "files": {{
    "README.md": "file contents",
    "main.py": "file contents",
    "tests/test_app.py": "file contents"
  }}
}}

All file contents must be JSON strings with proper escaping.
Do not wrap the JSON in Markdown.
"""

    project_context = (
        "AI Opportunity Robot application generation.\n"
        "The generated project is stored in an isolated workspace.\n"
        "Never claim that source files have been executed or tested.\n"
        "Return only the JSON object requested by the task."
    )

    ai_provider = provider or ask_ai

    try:
        response = ai_provider(task, project_context)
        files = _extract_files(response)

        # The workspace performs its own path, size, and secret checks.
        project_path = create_project(slug, files)

        try:
            archive_path = archive_project(slug)
        except Exception:
            # Preserve the generated source files for recovery.
            raise AppBuildError(
                "Source files were generated, but ZIP creation failed. "
                f"Project location: {project_path}"
            )

    except WorkspaceError as exc:
        raise AppBuildError(
            f"Generated files were rejected by workspace security: {exc}"
        ) from exc

    # Review the saved project and archive without executing generated code.
    try:
        review = review_generated_project(slug)
    except Exception as exc:
        # Preserve generated files even if the review itself encounters
        # an unexpected error. Report the failure honestly.
        review = {
            "project_name": slug,
            "review_passed": False,
            "status": "static_review_error",
            "tests_executed": False,
            "play_store_ready": False,
            "warnings": [
                f"Static review could not be completed: {exc}"
            ],
        }

    return {
        "project_name": slug,
        "project_path": str(project_path),
        "archive_path": str(archive_path),
        "files_created": len(files),
        "status": "generated_not_executed",
        "tests_run": False,
        "static_review": review,
        "static_review_passed": review["review_passed"],
        "play_store_ready": False,
        "message": (
            "Source files generated and archived. "
            + (
                "Static review passed. "
                if review["review_passed"]
                else "Static review found problems or could not be completed. "
            )
            + "The application has not been executed or tested."
        ),
    }
