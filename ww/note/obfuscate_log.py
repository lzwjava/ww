import argparse
import difflib
import sys

from ww.llm.openrouter_client import call_openrouter_api


OBFUSCATE_PROMPT = """Obfuscate all sensitive information in the following text. Replace:
- IP addresses → 10.x.x.x or 192.168.x.x
- SSH keys → [SSH_KEY_REDACTED]
- API keys/tokens → [API_KEY_REDACTED]
- Passwords → [PASSWORD_REDACTED]
- Email addresses → user@example.com
- Hostnames/domains that look internal → host.example.com
- AWS account IDs → 123456789012
- Private file paths containing usernames → /home/user/...
- Phone numbers → +1-555-000-0000
- MAC addresses → 00:00:00:00:00:00
- Any other credentials or secrets → [REDACTED]

Keep all non-sensitive text exactly as-is. Respond with ONLY the obfuscated text, no explanations.

---
{content}
---"""


def read_input_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def show_diff(original, obfuscated):
    orig_lines = original.splitlines(keepends=True)
    obf_lines = obfuscated.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines, obf_lines, fromfile="original", tofile="obfuscated"
    )
    diff_text = "".join(diff)
    if not diff_text:
        print("No sensitive content found. File unchanged.")
        return False
    print(diff_text)
    return True


def obfuscate_log():
    parser = argparse.ArgumentParser(
        description="Obfuscate sensitive data in log files"
    )
    parser.add_argument("input_file", help="Path to .md, .txt, or .log file")
    args = parser.parse_args(sys.argv[1:])

    content = read_input_file(args.input_file)
    prompt = OBFUSCATE_PROMPT.format(content=content)
    obfuscated = call_openrouter_api(prompt)

    if not obfuscated:
        print("Error: LLM call failed.")
        sys.exit(1)

    has_changes = show_diff(content, obfuscated)
    if not has_changes:
        return

    with open(args.input_file, "w", encoding="utf-8") as f:
        f.write(obfuscated)
    print(f"Obfuscated: {args.input_file}")
