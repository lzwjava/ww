import sys


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv.pop(1)
        if cmd == "create-note":
            from ww.create.create_note import main as create_note_main
            create_note_main()
        elif cmd == "create-log":
            from ww.create.create_log import create_log
            create_log()
        elif cmd == "gif":
            from ww.gif.gif import main as gif_main
            gif_main()
        elif cmd == "gitmessageai":
            from ww.github.gitmessageai import gitmessageai
            import argparse
            from ww.github.gitmessageai import MODEL_MAPPING
            parser = argparse.ArgumentParser(description="Generate commit message with AI and commit changes.")
            parser.add_argument("--no-push", dest="push", action="store_false")
            parser.add_argument("--only-message", dest="only_message", action="store_true")
            parser.add_argument("--model", type=str, default="grok-fast", choices=list(MODEL_MAPPING.keys()))
            parser.add_argument("--allow-pull-push", dest="allow_pull_push", action="store_true")
            parser.add_argument("--type", type=str, default="content", choices=["file", "content"])
            args = parser.parse_args()
            gitmessageai(push=args.push, only_message=args.only_message, model=args.model, allow_pull_push=args.allow_pull_push, type=args.type)
        elif cmd == "github-readme":
            from ww.github.readme import format_projects_to_markdown, all_projects
            import os
            github_username = "lzwjava"
            github_token = os.getenv("GITHUB_TOKEN")
            markdown_output = format_projects_to_markdown(all_projects, github_username, github_token)
            print(markdown_output)
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("hello world")
