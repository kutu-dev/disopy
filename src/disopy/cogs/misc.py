# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Holds the cog for misc commands."""

import discord
from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..config import Config
from ..options import Options
from .base import Base


class Misc(Base):
    """Cog that holds miscellaneous commands."""

    def __init__(self, bot: Bot, options: Options, subsonic: Subsonic, config: Config) -> None:
        """The constructor of the cog.

        Args:
            bot: The bot attached to the cog.
            subsonic: The object to be used to access the OpenSubsonic REST API.
            config: The config of the program.
        """

        super().__init__(bot, options)

        self.subsonic = subsonic
        self.config = config

    @app_commands.command(description="Get the latency of the bot")
    async def ping(self, interaction: Interaction) -> None:
        """Prints some information about the status of the bot.

        Args:
            interaction: The interaction that started the command.
        """

        subsonic_status = "✅ Ok" if self.subsonic.system.ping().status == "ok" else "❌ Failed"

        await self.send_answer(
            interaction,
            "🏓 Pong!",
            [f"Bot latency: **{int(self.bot.latency * 1000)}ms**", f"Subsonic status: **{subsonic_status}**"],
        )

    @app_commands.command(description="Sync the slash commands to the Discord cache globaly")
    async def sync(self, interaction: discord.Interaction) -> None:
        """Reloads the command tree globally, only if the user is authorized by the config.

        Args:
            interaction: The interaction that started the command.
        """

        if interaction.user.id not in self.config.developer_discord_sync_users:
            await self.send_error(interaction, ["❌ Action not authorized"], ephemeral=True)
            return

        await self.bot.tree.sync()
        await self.send_answer(interaction, "🔁 Command tree reloaded", ephemeral=True)
