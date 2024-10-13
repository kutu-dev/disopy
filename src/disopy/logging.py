# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import os
from typing import Final

from colorama import Fore, Style

from . import APP_NAME

# The relation between the logging level number and its prefix text and color
LOG_PREFIX: Final[dict[int, tuple[str, str]]] = {
    logging.DEBUG: ("DEBUG", Fore.GREEN),
    logging.INFO: ("INFO", Fore.BLUE),
    logging.WARNING: ("WARNING", Fore.YELLOW),
    logging.ERROR: ("ERROR", Fore.RED),
    logging.CRITICAL: ("CRITICAL", Fore.MAGENTA),
}


# If the color should be disabled
COLOR_DISABLED: Final[bool] = (
    "NO_COLOR" in os.environ or f"{APP_NAME.upper()}_NO_COLOR" in os.environ or os.environ.get("TERM", "") == "dumb"
)


class ColoredFormatter(logging.Formatter):
    """A custom formatter that takes care of coloring the output following the [CLIG](https://clig.dev/)."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the record taking care of output coloring.

        Args:
            record: The record to format.

        Returns:
            The formatted output.
        """

        prefix_text, prefix_color = LOG_PREFIX[record.levelno]

        formatter = logging.Formatter(
            (
                f"%(asctime)s - {Style.BRIGHT}{"" if COLOR_DISABLED else prefix_color}"
                + f"{prefix_text}{Style.RESET_ALL} - %(name)s: %(message)s"
            )
        )

        return formatter.format(record)


def setup_logging(debug: bool) -> None:
    """Setup the root logger.

    Args:
        debug: If debug messages should be logged.
    """

    logging_level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(logging_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging_level)
    stream_handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(stream_handler)
