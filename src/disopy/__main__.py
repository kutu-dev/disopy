# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from .config import get_config, generate_new_config
from .logging import setup_logging
from .options import get_options

logger = logging.getLogger(__name__)


def main() -> None:
    """The entry point of the program."""

    options = get_options()

    setup_logging(options.debug, options.color)

    if options.generate_config:
        generate_new_config(options.config_path)
        return

    config = get_config(options.config_path)
    if config is None:
        return

    print(config)


if __name__ == "__main__":
    main()
