from ww.llm.openrouter_client import call_openrouter_api
from ww.note.create_normal_log import create_normal_log
from ww.note.create_note_utils import get_clipboard_content, generate_title
from ww.note.obfuscate_log import OBFUSCATE_PROMPT


def is_sensitive_content(content):
    sensitivity_prompt = lambda c: (
        f"Does the following text contain sensitive information such as passwords, API keys, or personal data? Respond with 'yes' or 'no' only: {c}"
    )
    response = generate_title(content, 1, sensitivity_prompt).lower()
    return response == "yes"


def obfuscate_content(content):
    prompt = OBFUSCATE_PROMPT.format(content=content)
    obfuscated = call_openrouter_api(prompt)
    if not obfuscated:
        return None
    return obfuscated


def create_log():
    content = get_clipboard_content()

    if len(content) > 1048576:
        print("Error: Content exceeds 1MB. Please shorten the log and try again.")
        return

    if is_sensitive_content(content):
        print("Sensitive content detected. Obfuscating...")
        obfuscated = obfuscate_content(content)
        if not obfuscated:
            print("Error: Obfuscation failed.")
            return
        create_normal_log(obfuscated)
    else:
        create_normal_log()
