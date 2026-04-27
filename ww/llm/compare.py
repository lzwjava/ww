import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from ww.llm.openrouter_client import call_openrouter_api

MODELS = [
    ("gpt-4o", "openai/gpt-4o"),
    ("gpt-4.1", "openai/gpt-4.1"),
    ("gemini-2-flash", "google/gemini-2.0-flash-001"),
    ("gemini-2.5-pro", "google/gemini-2.5-pro"),
    ("claude-3.7-sonnet", "anthropic/claude-3.7-sonnet"),
    ("claude-3-haiku", "anthropic/claude-3-haiku"),
]

JUDGE_MODEL = "anthropic/claude-3.7-sonnet"


def read_clipboard():
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return result.stdout.strip()


def query_model(label, model_id, prompt):
    try:
        answer = call_openrouter_api(prompt, model=model_id, max_tokens=1024)
        return label, answer
    except Exception as e:
        return label, f"[ERROR: {e}]"


def judge_responses(prompt, responses):
    parts = [f"Original question:\n{prompt}\n"]
    for label, answer in responses:
        parts.append(f"--- {label} ---\n{answer}\n")
    parts.append(
        "Based on the above responses, which answer is the best? "
        "Explain briefly why, then state the winner model name."
    )
    judge_prompt = "\n".join(parts)
    return call_openrouter_api(judge_prompt, model=JUDGE_MODEL, max_tokens=512)


def main():
    prompt = read_clipboard()
    if not prompt:
        print("Clipboard is empty. Copy a question first.")
        sys.exit(1)

    print(f"Question:\n{prompt}\n")
    print("=" * 60)

    responses = []
    with ThreadPoolExecutor(max_workers=len(MODELS)) as executor:
        futures = {
            executor.submit(query_model, label, model_id, prompt): label
            for label, model_id in MODELS
        }
        for future in as_completed(futures):
            label, answer = future.result()
            responses.append((label, answer))
            print(f"\n--- {label} ---\n{answer}")

    responses.sort(key=lambda x: [lbl for lbl, _ in MODELS].index(x[0]))

    print("\n" + "=" * 60)
    print("JUDGE VERDICT")
    print("=" * 60)
    verdict = judge_responses(prompt, responses)
    print(verdict)
