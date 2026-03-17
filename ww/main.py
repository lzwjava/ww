import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "create-note":
        sys.argv.pop(1)
        from ww.create.create_note import main as create_note_main
        create_note_main()
    else:
        print("hello world")
