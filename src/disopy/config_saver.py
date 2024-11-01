# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle saving the configuration defined by the user in the config file."""

import logging
from pathlib import Path

from tomlkit import comment, document, item, nl, table

from . import APP_NAME, APP_NAME_LOWER
from .config import Config

logger = logging.getLogger(__name__)


def generate_new_config_tip_message() -> None:
    """Print a tip about how to generate a default config"""

    logger.info(f"You can generate a default config file with: {APP_NAME_LOWER} --generate-config")


def generate_new_config(config_path: Path) -> None:
    """Generate a new config file

    Args:
        config_path: The path to the folder where config file should be stored.
    """

    logger.info("Generating a new config file")

    config_file = config_path / "config.toml"
    config_file.touch()

    doc = document()
    doc.add(comment(f"{APP_NAME} config file"))
    doc.add(nl())

    doc.add(comment("DO NOT MODIFY ME! Internal config file version"))
    # Ugly hack to avoid `mypy` errors when using numbers, the `tomlkit` typing is really bad
    doc.add("version", item(1))
    doc.add(comment("The volume of the music playback in percentage"))
    doc.add("volume", item(100))

    doc.add(nl())

    subsonic_table = table()
    subsonic_table.add(comment("The URL where the OpenSubsonic REST API can be accessed"))
    subsonic_table.add("url", "http://example.com")

    subsonic_table.add(comment("The user to be used when authenticating in the OpenSubsonic server"))
    subsonic_table.add("user", "Alice")

    doc.add("subsonic", subsonic_table)

    with open(config_file, "w") as f:
        f.write(doc.as_string())
