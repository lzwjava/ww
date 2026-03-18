import os

from dotenv import load_dotenv


def load_env():
    load_dotenv()
    base_path = os.environ.get("BASE_PATH", "").strip()
    if base_path and base_path != ".":
        extra_env = os.path.join(base_path, ".env")
        if os.path.isfile(extra_env):
            load_dotenv(extra_env, override=True)
