from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def collect_project_context():
    files = []

    for path in sorted(PROJECT_ROOT.rglob("*")):
        if not path.is_file():
            continue

        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue

        if path.name.endswith((".db", ".save", ".pyc")):
            continue

        relative = path.relative_to(PROJECT_ROOT)
        files.append(str(relative))

    return "\n".join(files)


def create_task_prompt(task):
    context = collect_project_context()

    return (
        "You are assisting with a software project.\n\n"
        f"USER TASK:\n{task}\n\n"
        "PROJECT FILES:\n"
        f"{context}\n\n"
        "Instructions:\n"
        "- Inspect the existing project before proposing changes.\n"
        "- Preserve existing functionality.\n"
        "- Do not delete unrelated files.\n"
        "- Identify the smallest set of files that need changes.\n"
        "- Explain what should be changed before implementation.\n"
    )
