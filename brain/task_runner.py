from brain.tasks import create_task_prompt
from brain.coder_ai import ask_ai


def run_task(task):
    prompt = create_task_prompt(task)

    print("AI CODING ROBOT")
    print("================")
    print()
    print("TASK:")
    print(task)
    print()
    print("Sending task for analysis...")
    print()

    result = ask_ai(task, prompt)

    print("AI RESPONSE")
    print("-----------")
    print(result)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print('Usage: python -m brain.task_runner "your task here"')
        raise SystemExit(1)

    task = " ".join(sys.argv[1:])
    run_task(task)
