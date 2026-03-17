import sys
import argparse
from difflib import SequenceMatcher


def clean_log(
    input_path=None, output_path=None, similarity_threshold=1.0, lines_to_compare=1
):
    if not isinstance(lines_to_compare, int) or lines_to_compare < 1:
        raise ValueError(
            "lines_to_compare must be an integer greater than or equal to 1."
        )

    if input_path:
        try:
            with open(input_path, "r") as infile:
                lines = infile.readlines()
        except FileNotFoundError:
            print(f"Error: File not found at path: {input_path}", file=sys.stderr)
            sys.exit(1)
    else:
        lines = sys.stdin.readlines()

    if output_path:
        try:
            outfile = open(output_path, "w")
        except IOError:
            print(
                f"Error: Unable to open file for writing: {output_path}",
                file=sys.stderr,
            )
            sys.exit(1)
    elif input_path:
        try:
            outfile = open(input_path, "w")
        except IOError:
            print(
                f"Error: Unable to open file for writing: {input_path}", file=sys.stderr
            )
            sys.exit(1)
    else:
        outfile = sys.stdout

    num_lines = len(lines)
    i = 0
    removed_lines = 0
    while i < num_lines:
        current_lines = lines[i : min(i + lines_to_compare, num_lines)]

        if len(current_lines) == lines_to_compare:
            current_standards = []
            all_standard = True
            for line in current_lines:
                parts = line.split(" | ", 3)
                if len(parts) == 4:
                    level, _, thread, message = parts
                    current_standards.append((thread, message))
                else:
                    print(f"Non-standard line: {line.strip()}")
                    print(line, end="", file=outfile)
                    all_standard = False
                    break

            if all_standard:
                next_lines_start = i + lines_to_compare
                next_lines = lines[
                    next_lines_start : min(
                        next_lines_start + lines_to_compare, num_lines
                    )
                ]

                if len(next_lines) == lines_to_compare:
                    next_standards = []
                    for line in next_lines:
                        parts = line.split(" | ", 3)
                        if len(parts) == 4:
                            level, _, thread, message = parts
                            next_standards.append((thread, message))
                        else:
                            next_standards = None
                            break

                    if next_standards:
                        similarity = SequenceMatcher(
                            None,
                            " ".join([" ".join(x) for x in current_standards]),
                            " ".join([" ".join(x) for x in next_standards]),
                        ).ratio()
                        print(
                            f"Similarity: {similarity:.4f}, Threshold: {similarity_threshold:.4f}"
                        )

                        if similarity < similarity_threshold:
                            for line in current_lines:
                                print(line, end="", file=outfile)
                        else:
                            print(
                                f"Skipping duplicate lines: {''.join([line.strip() for line in current_lines])}"
                            )
                            removed_lines += len(current_lines)
                    else:
                        for line in current_lines:
                            print(line, end="", file=outfile)
                else:
                    for line in current_lines:
                        print(line, end="", file=outfile)
            i += lines_to_compare
        else:
            for line in current_lines:
                parts = line.split(" | ", 3)
                if len(parts) == 4:
                    print(line, end="", file=outfile)
                else:
                    print(f"Non-standard line: {line.strip()}")
                    print(line, end="", file=outfile)
            i += len(current_lines)

    if output_path or input_path:
        outfile.close()

    print(f"Removed {removed_lines} duplicate lines.")


def is_valid_similarity_threshold(value):
    try:
        value = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Similarity threshold must be a floating-point number."
        )
    if 0.0 <= value <= 1.0:
        return value
    raise argparse.ArgumentTypeError(
        "Similarity threshold must be between 0.0 and 1.0."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Clean duplicate log lines from a file or stdin."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        type=str,
        help="Path to the input log file (optional, defaults to stdin)",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="Path to the output log file (optional, defaults to overwriting input)",
    )
    parser.add_argument(
        "-s",
        "--similarity",
        type=is_valid_similarity_threshold,
        default=1.0,
        help="Similarity threshold 0.0-1.0 (default: 1.0)",
    )
    parser.add_argument(
        "-l",
        "--lines",
        type=int,
        default=1,
        help="Number of consecutive lines to compare (default: 1)",
    )
    args = parser.parse_args()
    clean_log(args.input_path, args.output_path, args.similarity, args.lines)
