# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The initial module of the Discord bot"""

from pathlib import Path
from typing import Final

import colorama
import platformdirs

__version__ = "2.2.0"

APP_NAME: Final[str] = "Disopy"
APP_NAME_UPPER: Final[str] = APP_NAME.upper()
APP_NAME_LOWER: Final[str] = APP_NAME.lower()

DEFAULT_CONFIG_PATH: Final[Path] = Path(platformdirs.user_config_dir(APP_NAME_LOWER))
DEFAULT_CACHE_PATH: Final[Path] = Path(platformdirs.user_cache_dir(APP_NAME_LOWER))

colorama.just_fix_windows_console()
