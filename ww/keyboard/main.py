import sys


def _pop_subcmd():
    if len(sys.argv) > 1:
        return sys.argv.pop(1)
    return ""


def _print_help():
    print("Usage: ww keyboard <command>")
    print("")
    print("Commands:")
    print("  capslock-ctrl   Toggle Caps Lock <-> Left Ctrl swap (Ubuntu/GNOME)")


def main():
    subcmd = _pop_subcmd()
    if subcmd in ("", "--help", "-h", "help"):
        _print_help()
        return

    if subcmd == "capslock-ctrl":
        from ww.keyboard.capslock_ctrl import run

        run()
    else:
        print(f"Unknown keyboard command: {subcmd}")
        sys.exit(1)
