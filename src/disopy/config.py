# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle the configuration defined by the user in the config file."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit import TOMLDocument, comment, document, item, nl, table

from . import APP_NAME, APP_NAME_LOWER

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Holds all the user defined config.

    Attributes:
        version: The version of the config file.
        volume: The base volume the playback should have.
        

        subsonic_url: The URL of the OpenSubsonic REST API.
        use_https: Whether to verify the server's certificate.
        subsonic_user: The user to be used in authentication on the OpenSubsonic REST API.

        developer_discord_sync_guild: The guild where commands should always be synced.
        developer_discord_sync_users: The users allowed to trigger a global sync with.
    """

    version: int
    volume: int
    
    subsonic_url: str
    use_https: bool
    subsonic_user: str

    developer_discord_sync_guild: int | None
    developer_discord_sync_users: list[int]


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


def generate_new_config(config_path: Path) -> None:
    """Generate a new config file

    Args:
        config_path: The path to the folder where config file should be stored.
    """

    logger.info("Generating a new config file")

    config_file = get_config_file_path(config_path)

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

    subsonic_table.add(comment("Whether to verify the server's certificate"))
    subsonic_table.add("use_https", True)

    subsonic_table.add(comment("The user to be used when authenticating in the OpenSubsonic server"))
    subsonic_table.add("user", "Alice")

    doc.add("subsonic", subsonic_table)

    with open(config_file, "w") as f:
        f.write(doc.as_string())


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

        for entry in ["url", "use_https", "user"]:
            if entry not in config["subsonic"].value:
                missing_entry_error_message(f"subsonic.{entry}")
                return None

        subsonic_url = str(config["subsonic"]["url"])
        use_https = bool(config["subsonic"]["use_https"])
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
            use_https=use_https,
            subsonic_user=subsonic_user,
            developer_discord_sync_guild=developer_discord_sync_guild,
            developer_discord_sync_users=developer_discord_sync_users,
        )
