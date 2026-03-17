import os
import sys
import re


def get_package(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"^\s*package\s+([\w.]+);", line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return None


def get_specific_imports(file_path):
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"^\s*import\s+([\w.]+);", line)
                if match:
                    imp = match.group(1)
                    if not imp.endswith(".*"):
                        imports.append(imp)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return imports


def get_package_group(full_class_name, level):
    package = ".".join(full_class_name.split(".")[:-1])
    parts = package.split(".")
    if len(parts) <= level:
        return package
    return ".".join(parts[:level])


def main():
    if len(sys.argv) != 3:
        print("Usage: ww analyze-deps <root_directory> <level>")
        sys.exit(1)

    root_dir = sys.argv[1]
    try:
        level = int(sys.argv[2])
        if level < 1:
            raise ValueError
    except ValueError:
        print("Error: level must be a positive integer")
        sys.exit(1)

    all_classes = set()

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                package = get_package(file_path)
                if package:
                    class_name = file.replace(".java", "")
                    all_classes.add(f"{package}.{class_name}")

    group_dependencies = set()

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                package = get_package(file_path)
                if package:
                    class_name = file.replace(".java", "")
                    full_class_name = f"{package}.{class_name}"
                    importer_group = get_package_group(full_class_name, level)
                    imports = get_specific_imports(file_path)
                    for imp in imports:
                        if imp in all_classes and imp != full_class_name:
                            imported_group = get_package_group(imp, level)
                            if imported_group != importer_group:
                                group_dependencies.add((importer_group, imported_group))

    print("digraph G {")
    for from_group, to_group in sorted(group_dependencies):
        print(f'  "{from_group}" -> "{to_group}";')
    print("}")
