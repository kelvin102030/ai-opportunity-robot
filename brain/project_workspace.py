"""Safe workspace management for AI-generated application projects."""

import os
import re
import zipfile
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_ROOT = PROJECT_ROOT / "generated_apps"

MAX_FILES = 100
MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 2_000_000

_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bsk-[a-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)\b(?:api_key|api_secret|access_token|client_secret)"
        r"\s*[:=]\s*['\"]?[a-z0-9_./+=-]{12,}"
    ),
]


class WorkspaceError(ValueError):
    """Raised when generated project content is unsafe or invalid."""


def _safe_project_name(name):
    """Convert a project name into a safe directory name."""
    if not isinstance(name, str):
        raise WorkspaceError("Project name must be text.")

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-_").lower()

    if not slug or slug in {".", ".."} or len(slug) > 60:
        raise WorkspaceError("Invalid project name.")

    return slug


def _validate_relative_path(name):
    """Reject absolute paths, traversal, hidden paths and unsafe names."""
    if not isinstance(name, str) or not name or len(name) > 240:
        raise WorkspaceError("Invalid generated file path.")

    if "\\" in name or "\x00" in name:
        raise WorkspaceError("Invalid path characters.")

    path = PurePosixPath(name)

    if path.is_absolute() or any(
        part in {"", ".", ".."} for part in name.split("/")
    ):
        raise WorkspaceError("Unsafe generated file path.")

    if any(part.startswith(".") for part in path.parts):
        raise WorkspaceError("Hidden files are not permitted.")

    if any(":" in part for part in path.parts):
        raise WorkspaceError("Invalid path component.")

    if path.parts and path.parts[0].lower() in {
        ".git", ".env", "secrets", "credentials"
    }:
        raise WorkspaceError("Sensitive paths are not permitted.")

    return path


def _check_content(content):
    if not isinstance(content, str):
        raise WorkspaceError("Generated file content must be text.")

    encoded = content.encode("utf-8")

    if len(encoded) > MAX_FILE_BYTES:
        raise WorkspaceError("Generated file exceeds the size limit.")

    for pattern in _SECRET_PATTERNS:
        if pattern.search(content):
            raise WorkspaceError(
                "Potential secret detected; generated file rejected."
            )

    return encoded


def create_project(name, files):
    """
    Write generated files into a controlled project workspace.

    Only explicitly supplied text files are written. This function does
    not execute generated code or install generated dependencies.
    """
    slug = _safe_project_name(name)

    if not isinstance(files, dict) or not files:
        raise WorkspaceError("A non-empty file mapping is required.")

    if len(files) > MAX_FILES:
        raise WorkspaceError("Too many generated files.")

    validated = []
    total_size = 0

    for filename, content in files.items():
        relative = _validate_relative_path(filename)
        encoded = _check_content(content)
        total_size += len(encoded)

        if total_size > MAX_TOTAL_BYTES:
            raise WorkspaceError("Project exceeds the total size limit.")

        validated.append((relative, encoded))

    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    root = GENERATED_ROOT.resolve()
    destination = root / slug

    if destination.exists():
        raise WorkspaceError(
            "Project already exists. Choose a new name to avoid overwriting."
        )

    # Validate every file before writing any of them.
    destination.mkdir(mode=0o700)

    try:
        for relative, encoded in validated:
            target = destination.joinpath(*relative.parts)

            # The generated directory is new and generated paths cannot
            # contain traversal or hidden components.
            target.parent.mkdir(parents=True, exist_ok=True)

            resolved = target.resolve()
            if os.path.commonpath((str(root), str(resolved))) != str(root):
                raise WorkspaceError("Generated path escaped the workspace.")

            with target.open("xb") as handle:
                handle.write(encoded)

        return destination

    except Exception:
        # Remove only the new workspace created by this invocation.
        import shutil
        shutil.rmtree(destination, ignore_errors=True)
        raise


def archive_project(name):
    """Create a ZIP containing only files inside a generated project."""
    slug = _safe_project_name(name)
    root = GENERATED_ROOT.resolve()
    project = (root / slug).resolve()

    if os.path.commonpath((str(root), str(project))) != str(root):
        raise WorkspaceError("Project path escaped the workspace.")

    if not project.is_dir() or project.is_symlink():
        raise WorkspaceError("Generated project does not exist.")

    archive = root / f"{slug}.zip"

    if archive.exists():
        raise WorkspaceError("Archive already exists.")

    try:
        with zipfile.ZipFile(
            archive, "x", compression=zipfile.ZIP_DEFLATED
        ) as bundle:
            for path in sorted(project.rglob("*")):
                if path.is_symlink():
                    raise WorkspaceError("Symbolic links are not permitted.")

                if not path.is_file():
                    continue

                resolved = path.resolve()
                if os.path.commonpath(
                    (str(project), str(resolved))
                ) != str(project):
                    raise WorkspaceError("File escaped the project.")

                bundle.write(path, path.relative_to(project))

        return archive

    except Exception:
        archive.unlink(missing_ok=True)
        raise
