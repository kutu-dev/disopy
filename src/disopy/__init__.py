# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Final

import colorama

# TODO: Change in release!
__version__ = "0.1.0"

# TODO: May be changed in the future
# The name of the application
APP_NAME: Final[str] = "Disopy"

colorama.just_fix_windows_console()
