"""Static review of generated applications without executing their code."""

import ast
import zipfile
from pathlib import Path

from brain.project_workspace import (
    GENERATED_ROOT,
    MAX_FILES,
    MAX_FILE_BYTES,
    MAX_TOTAL_BYTES,
    WorkspaceError,
    _safe_project_name,
)


class AppReviewError(ValueError):
    """Raised when a generated project cannot be reviewed."""


def review_generated_project(name):
    """
    Inspect a generated application without executing generated code.

    Checks project structure, Python syntax, README and test presence,
    and ZIP integrity. Passing this review does not mean the application
    has been executed, tested, or approved for publication.
    """
    if (
        not isinstance(name, str)
        or not name
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    ):
        raise AppReviewError("Invalid project name.")

    try:
        slug = _safe_project_name(name)
    except WorkspaceError as exc:
        raise AppReviewError(f"Invalid project name: {exc}") from exc

    root = GENERATED_ROOT.resolve()
    project = (root / slug).resolve()
    archive = root / f"{slug}.zip"

    if project.parent != root:
        raise AppReviewError("Project path escaped the generated workspace.")

    if project.is_symlink() or not project.is_dir():
        raise AppReviewError("Generated project does not exist.")

    files = []
    syntax_errors = []
    oversized_files = []
    total_bytes = 0

    for path in sorted(project.rglob("*")):
        if path.is_symlink():
            raise AppReviewError("Symbolic links are not permitted.")

        if not path.is_file():
            continue

        resolved = path.resolve()

        if resolved != project and project not in resolved.parents:
            raise AppReviewError("A file escaped the generated project.")

        relative = path.relative_to(project).as_posix()
        files.append(relative)

        try:
            content = path.read_bytes()
        except OSError as exc:
            raise AppReviewError(
                f"Cannot read generated file: {relative}"
            ) from exc

        total_bytes += len(content)

        if len(content) > MAX_FILE_BYTES:
            oversized_files.append(relative)

        if relative.endswith(".py"):
            try:
                source = content.decode("utf-8")
                ast.parse(source, filename=relative)
            except UnicodeDecodeError:
                syntax_errors.append(
                    {"file": relative, "error": "File is not valid UTF-8."}
                )
            except SyntaxError as exc:
                syntax_errors.append({
                    "file": relative,
                    "error": f"Line {exc.lineno}: {exc.msg}",
                })

    if not files:
        raise AppReviewError("Generated project contains no files.")

    has_readme = any(
        Path(filename).name.lower() == "readme.md"
        for filename in files
    )

    has_tests = any(
        filename.startswith("tests/")
        and Path(filename).name.startswith("test")
        and filename.endswith(".py")
        for filename in files
    )

    # These checks inspect names and sizes only; generated code is never run.
    has_entry_point = any(
        filename.lower() in {
            "main.py",
            "app.py",
            "run.py",
            "manage.py",
            "main.js",
            "index.js",
            "index.html",
            "main.dart",
            "app.dart",
            "android/app/build.gradle",
            "android/app/build.gradle.kts",
        }
        for filename in files
    )

    file_limit_exceeded = len(files) > MAX_FILES
    total_size_exceeded = total_bytes > MAX_TOTAL_BYTES

    archive_valid = False
    archive_error = None

    if not archive.is_file() or archive.is_symlink():
        archive_error = "Project ZIP archive is missing."
    else:
        try:
            with zipfile.ZipFile(archive, "r") as bundle:
                bad_member = bundle.testzip()

                if bad_member is not None:
                    archive_error = (
                        f"ZIP integrity check failed at: {bad_member}"
                    )
                else:
                    archive_names = set(bundle.namelist())
                    expected_names = set(files)

                    if archive_names != expected_names:
                        archive_error = (
                            "ZIP contents do not match project files."
                        )
                    else:
                        archive_valid = True
        except (OSError, zipfile.BadZipFile) as exc:
            archive_error = f"Invalid ZIP archive: {exc}"

    warnings = []

    if not has_readme:
        warnings.append("README.md is missing.")

    if not has_tests:
        warnings.append("No Python test file was found under tests/.")

    if not has_entry_point:
        warnings.append("No recognized application entry point was found.")

    if file_limit_exceeded:
        warnings.append(
            f"Project exceeds the workspace file limit of {MAX_FILES}."
        )

    if total_size_exceeded:
        warnings.append(
            f"Project exceeds the workspace total size limit of "
            f"{MAX_TOTAL_BYTES} bytes."
        )

    if oversized_files:
        warnings.append(
            f"One or more files exceed the workspace file size limit "
            f"of {MAX_FILE_BYTES} bytes."
        )

    if syntax_errors:
        warnings.append("One or more Python files contain syntax errors.")

    if not archive_valid:
        warnings.append(archive_error or "Archive verification failed.")

    review_passed = (
        not syntax_errors
        and archive_valid
        and not file_limit_exceeded
        and not total_size_exceeded
        and not oversized_files
    )

    return {
        "project_name": slug,
        "project_path": str(project),
        "archive_path": str(archive),
        "files_reviewed": len(files),
        "total_bytes": total_bytes,
        "python_files_checked": sum(
            filename.endswith(".py") for filename in files
        ),
        "syntax_errors": syntax_errors,
        "has_readme": has_readme,
        "has_tests": has_tests,
        "has_entry_point": has_entry_point,
        "file_limit_exceeded": file_limit_exceeded,
        "total_size_exceeded": total_size_exceeded,
        "oversized_files": oversized_files,
        "archive_valid": archive_valid,
        "review_passed": review_passed,
        "status": (
            "static_review_passed"
            if review_passed
            else "static_review_failed"
        ),
        "tests_executed": False,
        "play_store_ready": False,
        "warnings": warnings,
    }
