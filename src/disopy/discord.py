# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Implementation of the Discord bot"""

import logging

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

        if config.developer_discord_sync_guild is not None:
            logger.info(
                f"Developer config detected, reloading command tree for guild: '{config.developer_discord_sync_guild}'"
            )
            guild_object = discord.Object(id=config.developer_discord_sync_guild)

            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

    return bot
