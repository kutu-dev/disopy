# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from pathlib import Path
from typing import Any, NamedTuple

import tomlkit
from tomlkit import document, nl, table, comment, item

from . import APP_NAME

logger = logging.getLogger(__name__)


class Config(NamedTuple):
    version: int
    subsonic_url: str
    subsonic_user: str


def get_config_file_path(config_path: Path) -> Path:
    """Get the config file path and generate the file.

    Args:
        config_path: The path of the config folder.

    Returns:
        The path of the config file.
    """

    config_path.mkdir(parents=True, exist_ok=True)

    config_file = config_path / "config.toml"
    config_file.touch()

    return config_file


def generate_new_config_tip_message() -> None:
    """Print a tip about how to generate a default config"""

    # TODO: May change this
    logger.info("You can generate a default config file with: disopy --generate-config")


def missing_entry_error_message(missing_entry: str) -> None:
    """Print an error about a missing entry in the config file"""

    logger.critical(f"The provided config file is missing the '{missing_entry}' entry")
    generate_new_config_tip_message()


def generate_new_config(config_path: Path) -> None:
    """Generate a new config file

    Args:
        config_path: The path to the folder where config file should be stored.
    """

    logger.info("Generating config file")

    config_file = get_config_file_path(config_path)

    doc = document()
    doc.add(comment(f"{APP_NAME} config file"))
    doc.add(nl())

    doc.add(comment("DO NOT MODIFY ME! Internal config file version"))
    # Ugly hack to avoid `mypy` errors, the `tomlkit` typing is really bad
    doc.add("version", item(1))
    doc.add(nl())

    subsonic_table = table()
    subsonic_table.add(comment("The URL where the OpenSubsonic REST API can be accessed"))
    subsonic_table.add("url", "http://example.com")

    subsonic_table.add(comment("The user to be use when authenticating in the OpenSubsonic server"))
    subsonic_table.add("user", "Alice")

    doc.add("subsonic", subsonic_table)

    with open(config_file, "w") as f:
        f.write(doc.as_string())


def get_config(config_path: Path) -> Config | None:
    """Process the config files and returns them deserialized.

    Args:
        config_path: The path to the folder where config file should be accessed.
    """

    config_file = get_config_file_path(config_path)

    with open(config_file, "r+") as f:
        try:
            config: dict[str, Any] = tomlkit.load(f)
        except tomlkit.exceptions.ParseError as e:
            logger.critical("The provided config file is not valid TOML")
            generate_new_config_tip_message()
            logger.critical(e)

        if "version" not in config:
            missing_entry_error_message("version")
            return None

        version = int(config["version"])

        # Here old version can be migrated

        if "subsonic" not in config:
            missing_entry_error_message("subsonic")
            return None

        for entry in ["url", "user"]:
            if entry not in config["subsonic"].value:
                missing_entry_error_message(f"subsonic.{entry}")
                return None

        subsonic_url = str(config["subsonic"]["url"])
        subsonic_user = str(config["subsonic"]["user"])

        return Config(version=version, subsonic_url=subsonic_url, subsonic_user=subsonic_user)
