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
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("hello world")
