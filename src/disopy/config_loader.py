# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle loading the configuration defined by the user in the config file."""

import logging
from pathlib import Path
from typing import Any

import tomlkit

from . import APP_NAME_LOWER
from .config import Config

logger = logging.getLogger(__name__)


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

    logger.info(f"You can generate a default config file with: {APP_NAME_LOWER} --generate-config")


def missing_entry_error_message(missing_entry: str) -> None:
    """Print an error about a missing entry in the config file"""

    logger.critical(f"The provided config file is missing the '{missing_entry}' entry")
    generate_new_config_tip_message()


def get_config(config_path: Path) -> Config | None:
    """Process the config files and returns it deserialized.

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

        if "volume" not in config:
            missing_entry_error_message("volume")
            return None

        volume = int(config["volume"])
        if volume < 0:
            logger.critical("The volume config entry is lower than 0%")

        if "subsonic" not in config:
            missing_entry_error_message("subsonic")
            return None

        for entry in ["url", "user"]:
            if entry not in config["subsonic"].value:
                missing_entry_error_message(f"subsonic.{entry}")
                return None

        subsonic_url = str(config["subsonic"]["url"])
        subsonic_user = str(config["subsonic"]["user"])

        developer_discord_sync_guild = None
        developer_discord_sync_users: list[int] = []
        if "developer" in config:
            developer_discord_sync_guild = config["developer"]["discord-sync-guild"]
            developer_discord_sync_users = config["developer"]["discord-sync-users"]

        return Config(
            version=version,
            volume=volume,
            subsonic_url=subsonic_url,
            subsonic_user=subsonic_user,
            developer_discord_sync_guild=developer_discord_sync_guild,
            developer_discord_sync_users=developer_discord_sync_users,
        )
