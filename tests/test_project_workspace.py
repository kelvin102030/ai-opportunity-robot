import zipfile

import pytest

from brain import project_workspace as workspace


@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    root = tmp_path / "generated_apps"
    monkeypatch.setattr(workspace, "GENERATED_ROOT", root)
    return root


def test_creates_real_project_files(isolated_workspace):
    project = workspace.create_project(
        "sample-app",
        {
            "main.py": "print('Hello')\n",
            "src/app.py": "def run():\n    return True\n",
        },
    )

    assert project == isolated_workspace / "sample-app"
    assert (project / "main.py").read_text() == "print('Hello')\n"
    assert (project / "src/app.py").is_file()


@pytest.mark.parametrize(
    "filename",
    [
        "../outside.txt",
        "/tmp/outside.txt",
        "src/../../outside.txt",
        ".env",
        ".git/config",
        "src/.secret",
        r"src\..\outside.txt",
    ],
)
def test_rejects_unsafe_paths(filename, isolated_workspace):
    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project(
            "unsafe-app",
            {filename: "test content"},
        )

    assert not (isolated_workspace / "unsafe-app").exists()


def test_rejects_potential_api_secrets(isolated_workspace):
    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project(
            "secret-app",
            {"config.py": 'api_key = "abcdefghijklmnop123456"'},
        )

    assert not (isolated_workspace / "secret-app").exists()


def test_rejects_empty_project(isolated_workspace):
    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project("empty-app", {})


def test_rejects_existing_project_without_overwriting(
    isolated_workspace,
):
    project = workspace.create_project(
        "sample-app",
        {"main.py": "original"},
    )

    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project(
            "sample-app",
            {"main.py": "replacement"},
        )

    assert (project / "main.py").read_text() == "original"


def test_archives_project_files(isolated_workspace):
    workspace.create_project(
        "archive-app",
        {
            "main.py": "print('Hello')\n",
            "src/module.py": "VALUE = 1\n",
        },
    )

    archive = workspace.archive_project("archive-app")

    assert archive.is_file()

    with zipfile.ZipFile(archive) as bundle:
        assert set(bundle.namelist()) == {
            "main.py",
            "src/module.py",
        }
        assert bundle.read("main.py").decode() == "print('Hello')\n"


def test_cannot_archive_missing_project(isolated_workspace):
    with pytest.raises(workspace.WorkspaceError):
        workspace.archive_project("missing-app")


def test_rejects_invalid_project_names(isolated_workspace):
    for name in ("", ".", "..", "///", None):
        with pytest.raises(workspace.WorkspaceError):
            workspace.create_project(name, {"main.py": "pass"})


def test_rejects_too_many_files(isolated_workspace):
    files = {
        f"module_{index}.py": "pass\n"
        for index in range(workspace.MAX_FILES + 1)
    }

    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project("large-app", files)

    assert not (isolated_workspace / "large-app").exists()


def test_rejects_oversized_file(isolated_workspace):
    content = "x" * (workspace.MAX_FILE_BYTES + 1)

    with pytest.raises(workspace.WorkspaceError):
        workspace.create_project(
            "large-file-app",
            {"main.py": content},
        )

    assert not (isolated_workspace / "large-file-app").exists()
