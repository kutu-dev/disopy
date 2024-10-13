# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import hikari
import knuckles
import platformdirs

from . import APP_NAME
from .logging import setup_logging


def main() -> None:
    setup_logging(True)

    logger = logging.getLogger(__name__)
    logger.debug(hikari)
    logger.info(hikari)
    logger.warning(knuckles)
    logger.error(platformdirs.user_config_dir(APP_NAME))
    logger.critical(platformdirs.user_config_dir(APP_NAME))


if __name__ == "__main__":
    main()
