from ww.note.create_normal_log import create_normal_log
from ww.note.create_note_utils import get_clipboard_content, generate_title


def is_sensitive_content(content):
    sensitivity_prompt = lambda c: (
        f"Does the following text contain sensitive information such as passwords, API keys, or personal data? Respond with 'yes' or 'no' only: {c}"
    )
    response = generate_title(content, 1, sensitivity_prompt).lower()
    return response == "yes"


def create_log():
    content = get_clipboard_content()

    if len(content) > 1048576:
        print("Error: Content exceeds 1MB. Please shorten the log and try again.")
        return

    if is_sensitive_content(content):
        print(
            "Error: Sensitive content detected. Please remove passwords, keys, or personal data and try again."
        )
        return

    create_normal_log()
