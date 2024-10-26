# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Handle command line arguments."""

import argparse
from pathlib import Path
from typing import NamedTuple

from . import APP_NAME, DEFAULT_CONFIG_PATH, __version__


class Options(NamedTuple):
    """Holds all the global options for the program.

    Attributes:
        debug: If the output logs should be verbose.
        color: If the output logs should be colored.
        generate_config: If the config should be generated.
        config_path: The path for config to be saved.
    """

    debug: bool
    color: bool
    generate_config: bool

    config_path: Path


def get_options(force_no_color: bool = False) -> Options:
    """Get the options declared by the user.

    Args:
        force_no_color: If the color in the output of the program
            should be disabled.

    Returns:
        An object that holds all the options declared by the user.
    """

    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        # TODO: To be added (like in the flake)
        description="...",
    )

    parser.add_argument("-v", "--version", action="version", version=f"{APP_NAME} - {__version__}")

    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--generate-config", action="store_true")

    parser.add_argument("-c", "--config")

    args = parser.parse_args()

    config_path = DEFAULT_CONFIG_PATH if args.config is None else Path(args.config)

    no_color = args.no_color or force_no_color

    return Options(
        debug=args.debug,
        color=not no_color,
        generate_config=args.generate_config,
        config_path=config_path,
    )
