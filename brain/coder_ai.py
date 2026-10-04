import os
import requests


def ask_ai(task, project_context):
    api_key = os.getenv("BREWKEG_API_KEY")
    base_url = os.getenv("BREWKEG_BASE_URL", "https://brewkeg.dev/v1").rstrip("/")

    if not api_key:
        raise RuntimeError("BREWKEG_API_KEY is not set.")

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-5-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a coding assistant working on the user's local project. "
                        "Analyze the task and project context carefully. "
                        "Do not invent files or claim changes were made when they were not."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task:\n{task}\n\n"
                        f"Project context:\n{project_context}"
                    ),
                },
            ],
        },
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]
