import argparse
import sys

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


def _create_log_with_content(content, direct=False):
    if len(content) > 1048576:
        print("Error: Content exceeds 1MB. Please shorten the log and try again.")
        return

    if direct:
        create_normal_log(content)
        return

    if is_sensitive_content(content):
        print("Sensitive content detected. Obfuscating...")
        obfuscated = obfuscate_content(content)
        if not obfuscated:
            print("Error: Obfuscation failed.")
            return
        create_normal_log(obfuscated)
    else:
        create_normal_log(content)


def create_log():
    parser = argparse.ArgumentParser(description="Create a log entry from clipboard")
    parser.add_argument(
        "--direct", action="store_true", help="Skip sensitivity check and obfuscation"
    )
    args = parser.parse_args(sys.argv[1:])

    content = get_clipboard_content()
    _create_log_with_content(content, args.direct)


def create_log_from_file():
    parser = argparse.ArgumentParser(description="Create a log entry from a file")
    parser.add_argument("file", help="Path to the file to read content from")
    parser.add_argument(
        "--direct", action="store_true", help="Skip sensitivity check and obfuscation"
    )
    args = parser.parse_args(sys.argv[1:])

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
    _create_log_with_content(content, args.direct)
