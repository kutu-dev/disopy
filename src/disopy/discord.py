# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Implementation of the Discord bot"""

import logging
from typing import Final

import discord
from discord.ext.commands import Bot
from knuckles import Subsonic

from . import APP_NAME_LOWER
from .cogs.misc import Misc
from .cogs.queue import QueueCog
from .cogs.search import Search
from .config import Config
from .options import Options

logger = logging.getLogger(__name__)

COMMAND_TREE_STATUS_FILE_CONTENT: Final[str] = "Disopy Command Tree version: 1"


def check_command_tree_status(options: Options) -> bool:
    command_tree_status_path = options.cache_path / "discord/command-tree-status.txt"

    status = True

    if not command_tree_status_path.is_file():
        command_tree_status_path.parent.mkdir(parents=True, exist_ok=True)
        command_tree_status_path.touch()

        status = False

    with open(command_tree_status_path, "r+") as f:
        content = f.readline()

        if content != COMMAND_TREE_STATUS_FILE_CONTENT:
            f.seek(0)
            f.write(COMMAND_TREE_STATUS_FILE_CONTENT)
            f.truncate()

            status = False

    return status


def get_bot(subsonic: Subsonic, config: Config, options: Options) -> Bot:
    """Get the Discord bot.

    Args:
        subsonic: The object to be used to access the OpenSubsonic REST API.
        config: The config of the program.
        options: The options set on startup.

    Returns:
        A configured ready to use bot.
    """

    intents = discord.Intents.default()
    intents.message_content = True

    bot = discord.ext.commands.Bot(f"!{APP_NAME_LOWER}", intents=intents)

    @bot.event
    async def on_ready() -> None:
        """Thing to be run the startup of the bot"""

        logger.info(f"Logged in as '{bot.user}'")

        await bot.add_cog(Misc(bot, options, subsonic, config))
        await bot.add_cog(Search(bot, options, subsonic))
        await bot.add_cog(QueueCog(bot, options, subsonic, config))

        logger.info("Checking if the Command Tree is up to date in the Discord API...")
        if not check_command_tree_status(options):
            logger.info("The Command Tree is outdated, forcing sync!")
            await bot.tree.sync()

        if config.developer_discord_sync_guild is not None:
            logger.info(
                f"Developer config detected, reloading command tree for guild: '{config.developer_discord_sync_guild}'"
            )
            guild_object = discord.Object(id=config.developer_discord_sync_guild)

            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

    return bot
