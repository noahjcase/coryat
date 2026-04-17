import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "playj" / "config.toml"


def load() -> dict:
    if not CONFIG_PATH.exists():
        raise SystemExit(
            f"config not found at {CONFIG_PATH}\n"
            "create it with:\n"
            f"  mkdir -p {CONFIG_PATH.parent}\n"
            f'  echo \'data_repo_path = "/path/to/coryat-data"\' > {CONFIG_PATH}'
        )
    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    if "data_repo_path" not in cfg:
        raise SystemExit("config missing required key: data_repo_path")
    return cfg
