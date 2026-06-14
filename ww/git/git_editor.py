import subprocess
import sys


EDITORS = {
    "zed": "zed --wait",
    "vscode": "code --wait",
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("Usage: ww git editor <zed|vscode>")
        print("")
        print("Set the global git core.editor.")
        print("")
        print("Editors:")
        for name, cmd in EDITORS.items():
            print(f"  {name:8s}  {cmd}")
        return

    name = args[0].lower()
    if name not in EDITORS:
        print(
            f"Error: unknown editor '{name}'. Choose from: {', '.join(EDITORS)}",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = EDITORS[name]
    subprocess.run(["git", "config", "--global", "core.editor", cmd], check=True)
    print(f"git core.editor set to: {cmd}")
