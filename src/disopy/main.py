from . import __version__
from .messages import info, error
import argparse
import os
from pathlib import Path
import sys
import json
from colorama import Fore, Style

parser = argparse.ArgumentParser(
    prog="Disopy",
    description="A basic Discord bot for Subsonic",
    epilog="Created with ♥ by Kutu (https://kutu-dev.github.io/)",
)

xdg_config_home: Path
if os.environ.get("XDG_CONFIG_HOME") is None:
    xdg_config_home = Path(Path().home(), ".config")
else:
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME"))

parser.add_argument(
    "-v",
    "--version",
    action="store_true",
    help="shows the current version of unipropic",
)

parser.add_argument(
    "-c",
    "--config",
    type=Path,
    default=Path(xdg_config_home, "disopy/disopy.json"),
    help="path to the config file",
)

args: argparse.Namespace = parser.parse_args()

if args.version:
    info(f"{Fore.CYAN}Disopy{Style.RESET_ALL}", f"Version {__version__}")
    sys.exit(0)

# Basic config file check
CONFIG: dict[str, str] = {}


def regenerate_config_file() -> None:
    with open(args.config, "w") as file:
        default_json: dict[str, str] = {
            "user": {"username": "", "password": ""},
            "discordToken": "",
            "subsonicUrl": "https://",
            "caCertsPath": "",
        }

        error(
            f"{Fore.CYAN}Disopy{Style.RESET_ALL}",
            "Invalid JSON config file, recreating a default one",
        )
        file.write(json.dumps(default_json))


config_file: Path = parser.parse_args().config

if not config_file.is_file():
    info(
        "Disopy",
        f'Creating a default config file, please check "{config_file.absolute()}"',
    )
    config_file.parents[0].mkdir(parents=True, exist_ok=True)
    config_file.touch()
    sys.exit(0)


with open(parser.parse_args().config, "r+") as file:
    try:
        CONFIG = json.load(file)
    except json.decoder.JSONDecodeError:
        error("Disopy", "Invalid JSON config file, recreating a default one")
        regenerate_config_file()
        # Exit as the default json file will fail to connect to Discord and Subsonic
        sys.exit(1)

# Set custom ca certs env path if it exists in the config file
if CONFIG["caCertsPath"] != "":
    os.environ["REQUESTS_CA_BUNDLE"] = CONFIG["caCertsPath"]
    os.environ["SSL_CERT_FILE"] = CONFIG["caCertsPath"]

from .discord import start_client


def main() -> None:
    start_client()
