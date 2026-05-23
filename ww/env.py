import os
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    # Load from current working directory first
    load_dotenv()

    # Also load from the ww project root (where .env lives)
    project_root = Path(__file__).parent.parent
    project_env = project_root / ".env"
    if project_env.is_file():
        load_dotenv(project_env, override=False)

    base_path = os.environ.get("BASE_PATH", "").strip()
    if base_path and base_path != ".":
        extra_env = os.path.join(base_path, ".env")
        if os.path.isfile(extra_env):
            load_dotenv(extra_env, override=True)
