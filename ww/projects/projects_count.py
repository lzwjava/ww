import os


def main():
    projects_dir = os.path.expanduser("~/projects")
    if not os.path.isdir(projects_dir):
        print(f"Directory not found: {projects_dir}")
        return

    dirs = [
        d
        for d in os.listdir(projects_dir)
        if os.path.isdir(os.path.join(projects_dir, d)) and not d.startswith(".")
    ]
    print(len(dirs))
