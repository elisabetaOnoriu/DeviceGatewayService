import os
from pathlib import Path
from dotenv import load_dotenv

"""Path to the .env file in project root"""
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

""" Load .env if it exists"""
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

def get_env(key: str, default: str | None = None) -> str | None:
    """Helper to get environment variables with optional default"""
    return os.getenv(key, default)
