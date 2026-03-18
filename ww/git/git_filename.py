import subprocess
import re
import sys


def check_git_filenames():
    try:
        result = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        )
        filenames = [f for f in result.stdout.strip().split("\n") if f]

        general_pattern = re.compile(r"^[A-Za-z0-9._/]+$")
        markdown_pattern = re.compile(r"^[A-Za-z0-9._/-]+$")

        def is_invalid(filename):
            if filename.endswith(".md"):
                return not markdown_pattern.match(filename)
            else:
                return not general_pattern.match(filename)

        invalid_files = [f for f in filenames if is_invalid(f)]

        if invalid_files:
            print("Files with invalid characters found:")
            for file in invalid_files:
                print(f"  {file}")
            return False
        else:
            print("All filenames contain only allowed characters")
            return True

    except subprocess.CalledProcessError:
        print("Error: Not in a git repository or git command failed")
        return False
    except re.error as e:
        print(f"Regex error: {e}")
        return False


def main():
    success = check_git_filenames()
    sys.exit(0 if success else 1)
