import os
import sys
import xml.etree.ElementTree as ET

NS = "{http://maven.apache.org/POM/4.0.0}"
group_id_cache = {}


def get_group_id(pom_path, pom_map):
    if pom_path in group_id_cache:
        return group_id_cache[pom_path]

    tree = ET.parse(pom_path)
    root = tree.getroot()
    group_id_elem = root.find(NS + "groupId")

    if group_id_elem is not None:
        group_id = group_id_elem.text.strip()
    else:
        parent = root.find(NS + "parent")
        if parent is not None:
            parent_relative_path = parent.find(NS + "relativePath")
            if parent_relative_path is not None and parent_relative_path.text:
                parent_pom_path = os.path.normpath(
                    os.path.join(os.path.dirname(pom_path), parent_relative_path.text)
                )
            else:
                parent_pom_path = os.path.normpath(
                    os.path.join(os.path.dirname(pom_path), "..", "pom.xml")
                )

            if parent_pom_path in pom_map:
                group_id = get_group_id(parent_pom_path, pom_map)
            else:
                raise ValueError(f"Parent POM not found for {pom_path}: {parent_pom_path}")
        else:
            raise ValueError(f"No groupId or parent specified in {pom_path}")

    group_id_cache[pom_path] = group_id
    return group_id


def get_artifact_id(pom_path):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    artifact_id_elem = root.find(NS + "artifactId")
    if artifact_id_elem is None:
        raise ValueError(f"pom.xml must specify artifactId: {pom_path}")
    return artifact_id_elem.text.strip()


def get_dependencies(pom_path):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    dependencies = []
    for dep in root.findall(NS + "dependencies/" + NS + "dependency"):
        dep_group_id_elem = dep.find(NS + "groupId")
        dep_artifact_id_elem = dep.find(NS + "artifactId")
        if dep_group_id_elem is not None and dep_artifact_id_elem is not None:
            dependencies.append((dep_group_id_elem.text.strip(), dep_artifact_id_elem.text.strip()))
    return dependencies


def main():
    if len(sys.argv) != 2:
        print("Usage: ww analyze-poms <root_directory>")
        sys.exit(1)

    root_dir = sys.argv[1]
    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a directory")
        sys.exit(1)

    pom_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(root_dir)
        for file in files
        if file == "pom.xml"
    ]

    if not pom_files:
        print(f"No pom.xml files found in {root_dir}")
        sys.exit(1)

    pom_map = {pom_file: None for pom_file in pom_files}

    modules = {}
    for pom_file in pom_files:
        try:
            group_id = get_group_id(pom_file, pom_map)
            artifact_id = get_artifact_id(pom_file)
            modules[(group_id, artifact_id)] = pom_file
        except ValueError as e:
            print(f"Warning: Skipping {pom_file} due to error: {e}")
            continue

    dependencies = set()
    for pom_file in pom_files:
        try:
            importer_group_id = get_group_id(pom_file, pom_map)
            importer_artifact_id = get_artifact_id(pom_file)
            importer_key = (importer_group_id, importer_artifact_id)
            deps = get_dependencies(pom_file)
            for dep_group_id, dep_artifact_id in deps:
                dep_key = (dep_group_id, dep_artifact_id)
                if dep_key in modules and dep_key != importer_key:
                    dependencies.add((importer_artifact_id, dep_artifact_id))
        except ValueError as e:
            print(f"Warning: Error processing dependencies in {pom_file}: {e}")
            continue

    print("digraph G {")
    for from_module, to_module in sorted(dependencies):
        print(f'  "{from_module}" -> "{to_module}";')
    print("}")
