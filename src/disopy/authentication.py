from .main import CONFIG
import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Auth:
    """Holds the token and salt used for Subsonic API authentication"""

    salt: str = secrets.token_hex(16)
    token: str = hashlib.md5(
        CONFIG["user"]["password"].encode("utf-8") + salt.encode("utf-8")
    ).hexdigest()
