# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import discord
from discord.ext.commands import Bot, Cog
from discord.interactions import Interaction

logger = logging.getLogger(__name__)


class Base(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_embed(
        self, interaction: Interaction, title: str, content: list[str] | None = None, ephemeral: bool = False
    ) -> None:
        embed: discord.Embed = discord.Embed(
            description="\n".join(content) if content is not None else None, color=discord.Color.from_rgb(124, 0, 40)
        )

        if self.bot.user is None:
            logger.error("The bot doesn't have a user attach to it!")
            return

        icon_url = None
        if self.bot.user.avatar is not None:
            icon_url = self.bot.user.avatar.url

        embed.set_author(name=f"{title}", icon_url=icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
