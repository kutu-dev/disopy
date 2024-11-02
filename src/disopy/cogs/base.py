# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Holds a generic cog for the rest of them to be based of."""

import logging

import discord
from discord.ext.commands import Bot, Cog
from discord.interactions import Interaction

from ..options import Options

logger = logging.getLogger(__name__)


class Base(Cog):
    """Base cog for all the other ones, with some utility function."""

    def __init__(self, bot: Bot, options: Options) -> None:
        """The constructor of the cog.

        Args:
            bot: The bot attached to the cog.
        """

        self.bot = bot
        self.options = options

    async def send_answer(
        self, interaction: Interaction, title: str, content: list[str] | None = None, ephemeral: bool = False
    ) -> None:
        """Send an embed as the response of an interaction.

        Args:
            interaction: The interaction to response.
            title: The title of the embed.
            content: The content of the embed split in its lines.
            ephemeral: If the message should only be seen by the user that triggered the interaction.
        """

        if self.options.debug >= 3:
            logger.debug(f"Sending embed (Title: {title} Content: {content} Ephemeral: {ephemeral})")

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

    async def send_error(self, interaction: Interaction, error_content: list[str], ephemeral: bool = False) -> None:
        await self.send_answer(interaction, "Error ⚠️", error_content, ephemeral)
