"""Settings from the package configuration file."""

from importlib.resources import files

import yaml


def load_settings(
    config_file: str | None = None,
    settings_type: str = "default",
) -> dict:
    """Load settings from YAML config file.

    Args:
        config_file: Path to config YAML. Defaults to package metadata config.
        settings_type: Which settings block to load ('default' or 'custom').

    Returns:
        Dictionary of settings values.
    """
    if config_file is None:
        config_file = str(files("uitnodigingsregel.metadata") / "config.yaml")
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if settings_type == "default":
        return config["default_settings"]
    if settings_type == "custom":
        return config["custom_settings"]
    raise ValueError("No settings found. Choose 'default' or 'custom'.")
