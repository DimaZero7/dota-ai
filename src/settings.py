"""Load project settings from a local TOML file or the default template."""

from pathlib import Path

import toml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.toml"

if not CONFIG_FILE.exists():
    CONFIG_FILE = BASE_DIR / "default_config.toml"

with CONFIG_FILE.open("r", encoding="utf-8") as config_file:
    config_toml = toml.load(config_file)
