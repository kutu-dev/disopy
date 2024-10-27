# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import discord
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from .cogs.misc import Misc
from .cogs.queue import Queue
from .cogs.search import Search
from .config import Config
from .options import Options

logger = logging.getLogger(__name__)


def get_bot(subsonic: Subsonic, config: Config, options: Options) -> Bot:
    """Get the Discord bot.

    Args:
        subsonic: The object to be used to access the OpenSubsonic REST API.
        config: The configurations of the program.

    Returns:
        A configured ready to use bot
    """

    intents = discord.Intents.default()
    bot = discord.ext.commands.Bot("!", intents=intents)

    async def send_embed(
        interaction: Interaction, title: str, content: list[str] | None = None, ephemeral: bool = False
    ) -> None:
        embed: discord.Embed = discord.Embed(
            description="\n".join(content) if content is not None else None, color=discord.Color.from_rgb(124, 0, 40)
        )

        if bot.user is None:
            logger.error("The bot doesn't have a user attach to it!")
            return

        icon_url = None
        if bot.user.avatar is not None:
            icon_url = bot.user.avatar.url

        embed.set_author(name=f"{title}", icon_url=icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @bot.event
    async def on_ready() -> None:
        logger.info(f"Logged in as '{bot.user}'")

        await bot.add_cog(Misc(bot, subsonic, config))
        await bot.add_cog(Search(bot, subsonic))
        await bot.add_cog(Queue(bot, subsonic, options))

        if config.developer_discord_sync_guild is not None:
            logger.info(
                f"Developer config detected, reloading command tree for guild: '{config.developer_discord_sync_guild}'"
            )
            guild_object = discord.Object(id=config.developer_discord_sync_guild)

            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

    return bot
