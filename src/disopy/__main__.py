# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The main module of the Discord bot"""

import logging

from knuckles import Subsonic

from . import APP_NAME
from .config import generate_new_config, get_config
from .discord import get_bot
from .env import get_env
from .logging import setup_logging
from .options import get_options

logger = logging.getLogger(__name__)


def main() -> None:
    """The entry point of the program."""

    env = get_env()
    if env is None:
        return

    options = get_options(env.no_color)

    setup_logging(options.debug >= 1, options.color)

    if options.generate_config:
        generate_new_config(options.config_path)
        return

    config = get_config(options.config_path)
    if config is None:
        return

    subsonic = Subsonic(
        url=config.subsonic_url,
        user=config.subsonic_user,
        password=env.subsonic_password,
        client=APP_NAME,
        use_https=config.use_https,
    )

    logger.info(f"Starting {APP_NAME}!")

    if not config.use_https:
        logger.warning(
            "Secure conection (HTTPS) to the Subsonic server is disable in the config file, using plain HTTP!"
        )

    logger.info("Checking OpenSubsonic REST API status...")
    if subsonic.system.ping().status != "ok":
        logger.critical("The OpenSubsonic server is not available!")
        return

    logger.info("Healthy Subsonic server status reported!")

    logger.info("Logging to Discord...")
    get_bot(subsonic, config, options).run(
        env.discord_token,
        # Enable discord.py debug logging only on verbosity level 2 as it prints a lot
        log_level=logging.DEBUG if options.debug >= 2 else logging.INFO,
    )
