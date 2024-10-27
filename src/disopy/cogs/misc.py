# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..config import Config
from .base import Base


class Misc(Base):
    def __init__(self, bot: Bot, subsonic: Subsonic, config: Config) -> None:
        super().__init__(bot)

        self.subsonic = subsonic
        self.config = config

    @app_commands.command(description="Get the latency of the bot")
    async def ping(self, interaction: Interaction) -> None:
        subsonic_status = "Ok ✅" if self.subsonic.system.ping().status == "ok" else "Failed ❌"

        await self.send_embed(
            interaction,
            "Pong! 🏓",
            [f"Bot latency: **{int(self.bot.latency * 1000)}ms**", f"Subsonic status: **{subsonic_status}**"],
        )

    @app_commands.command(description="Sync the slash commands to the Discord cache globaly")
    async def sync(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in self.config.developer_discord_sync_users:
            await self.send_embed(interaction, "Action not authorized", ephemeral=True)
            return

        await self.bot.tree.sync()
        await self.send_embed(interaction, "Command tree reloaded", ephemeral=True)
