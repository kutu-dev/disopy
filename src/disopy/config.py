# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle the configuration defined by the user in the config file."""

import logging
from pathlib import Path
from typing import NamedTuple

from .config_loader import get_config, get_config_file_path
from .config_saver import generate_new_config

logger = logging.getLogger(__name__)


class Config(NamedTuple):
    """Holds all the user defined config.

    Attributes:
        version: The version of the config file.
        volume: The base volume the playback should have.

        subsonic_url: The URL of the OpenSubsonic REST API.
        subsonic_user: The user to be used in authentication on the OpenSubsonic REST API.

        developer_discord_sync_guild: The guild where commands should always be synced.
        developer_discord_sync_users: The users allowed to trigger a global sync with.
    """

    version: int
    volume: int

    subsonic_url: str
    subsonic_user: str

    developer_discord_sync_guild: int | None
    developer_discord_sync_users: list[int]

    def save(self, config_path: Path) -> None:
        """Save the updated config to the config file.

        Args:
            config_path: The path to the folder where config file should be stored.
        """
        config_file = get_config_file_path(config_path)

        doc = document()
        doc.add(comment(f"{APP_NAME} config file"))
        doc.add(nl())

        doc.add(comment("DO NOT MODIFY ME! Internal config file version"))
        doc.add("version", item(self.version))
        doc.add(comment("The volume of the music playback in percentage"))
        doc.add("volume", item(self.volume))

        doc.add(nl())

        subsonic_table = table()
        subsonic_table.add(comment("The URL where the OpenSubsonic REST API can be accessed"))
        subsonic_table.add("url", self.subsonic_url)

        subsonic_table.add(comment("The user to be used when authenticating in the OpenSubsonic server"))
        subsonic_table.add("user", self.subsonic_user)

        doc.add("subsonic", subsonic_table)

        with open(config_file, "w") as f:
            f.write(doc.as_string())
