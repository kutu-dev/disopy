# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The main module of the Discord bot"""

import logging

from knuckles import Subsonic

from . import APP_NAME
from .config import generate_new_config, get_config
from .env import get_env
from .logging import setup_logging
from .options import get_options
from .discord import get_client

logger = logging.getLogger(__name__)


def main() -> None:
    """The entry point of the program."""

    env = get_env()
    if env is None:
        return

    options = get_options(env.no_color)

    setup_logging(options.debug, options.color)

    if options.generate_config:
        generate_new_config(options.config_path)
        return

    config = get_config(options.config_path)
    if config is None:
        return

    _subsonic = Subsonic(
        url=config.subsonic_url, user=config.subsonic_user, password=env.subsonic_password, client=APP_NAME
    )

    get_client().run(env.discord_token)


if __name__ == "__main__":
    main()
