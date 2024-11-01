# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle environment variables of the process."""

import logging
import os
from typing import NamedTuple

from . import APP_NAME_UPPER

logger = logging.getLogger(__name__)


class Env(NamedTuple):
    """Hold all the relevant environment information.

    Attributes:
        no_color: If the color on the output should be disabled.
        subsonic_password: The password to be used in the OpenSubsonic REST API.
        discord_token: The token to be used to connect to Discord.
    """

    no_color: bool
    subsonic_password: str
    discord_token: str


def get_env_variable(variable_name: str, disable_critical_message: bool = False) -> str | None:
    """Get an environment variable prefixed with the app name.

    Args:
        variable_name: The name of the variable.
        disable_critical_message: If an error message should not be printed
            if the variable is not found.

    Returns:
        The found variable or none.
    """

    env_name = f"{APP_NAME_UPPER}_{variable_name}"
    if env_name not in os.environ:
        if not disable_critical_message:
            logger.critical(f"The '{env_name}' environment variable is missing!")

        return None

    return os.environ[env_name]


def get_env() -> Env | None:
    """Get the relevant environment of the program.

    Returns:
        The environment of the program.
    """

    subsonic_password = get_env_variable("SUBSONIC_PASSWORD")
    discord_token = get_env_variable("DISCORD_TOKEN")

    if subsonic_password is None or discord_token is None:
        return None

    no_color = (
        "NO_COLOR" in os.environ
        or get_env_variable("NO_COLOR", True) is not None
        or os.environ.get("TERM", "") == "dumb"
    )

    return Env(
        no_color=no_color,
        subsonic_password=subsonic_password,
        discord_token=discord_token,
    )
