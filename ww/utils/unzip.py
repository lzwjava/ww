import zipfile
import os
import argparse


def unzip(zip_file_path):
    directory = os.path.dirname(zip_file_path)
    folder_name = os.path.splitext(os.path.basename(zip_file_path))[0]
    destination_folder = os.path.join(directory, folder_name)

    os.makedirs(destination_folder, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(destination_folder)

    print(f"Contents extracted to {destination_folder}")


def main():
    parser = argparse.ArgumentParser(
        description="Unzip a file to the same directory with the same name."
    )
    parser.add_argument("zip_file", help="Path to the zip file")
    args = parser.parse_args()
    unzip(args.zip_file)
