import os
import shutil
import argparse


def convert_files_to_txt(source_dir, dest_dir):
    """Copy all files in source_dir to dest_dir with a .txt extension."""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for item in os.listdir(source_dir):
        source_path = os.path.join(source_dir, item)

        if os.path.isfile(source_path):
            name, _ = os.path.splitext(item)
            dest_path = os.path.join(dest_dir, name + ".txt")

            try:
                shutil.copy2(source_path, dest_path)
                print(f"Copied and renamed: {item} -> {name}.txt")
            except Exception as e:
                print(f"Error processing {item}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Copy files to a directory with .txt extensions."
    )
    parser.add_argument("source_dir", help="Directory containing files to convert")
    parser.add_argument(
        "dest_dir", nargs="?", help="Destination directory (default: source_dir/txt)"
    )
    args = parser.parse_args()

    source_dir = args.source_dir
    dest_dir = args.dest_dir or os.path.join(source_dir, "txt")
    convert_files_to_txt(source_dir, dest_dir)
