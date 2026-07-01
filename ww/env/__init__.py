import os
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    # 1. Canonical config: ~/.config/ww/.env (base defaults)
    xdg_config = Path.home() / ".config" / "ww" / ".env"
    if xdg_config.is_file():
        load_dotenv(xdg_config, override=False)

    # 2. Load from current working directory (local overrides for dev)
    load_dotenv()

    # 3. Also load from the ww project root (where .env used to live)
    project_root = Path(__file__).parent.parent
    project_env = project_root / ".env"
    if project_env.is_file():
        load_dotenv(project_env, override=False)

    # 4. BASE_PATH overrides everything (explicit override mechanism)
    base_path = os.environ.get("BASE_PATH", "").strip()
    if base_path and base_path != ".":
        extra_env = os.path.join(base_path, ".env")
        if os.path.isfile(extra_env):
            load_dotenv(extra_env, override=True)
