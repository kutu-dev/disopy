# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from collections import deque
from typing import NamedTuple

import discord
from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..options import Options
from .base import Base

logger = logging.getLogger(__name__)


class Song(NamedTuple):
    id: str
    title: str


class Queue(Base):
    def __init__(self, bot: Bot, subsonic: Subsonic, options: Options) -> None:
        super().__init__(bot)

        self.subsonic = subsonic
        self.options = options
        self.queue: deque[Song] = deque()

    async def is_not_in_channel(self, interaction: Interaction) -> bool:
        user = interaction.user
        if isinstance(user, discord.User):
            await interaction.response.send_message(
                "You are not a member of the guild, something has gone very wrong..."
            )
            return True

        if user.voice is None or user.voice.channel is None:
            await interaction.response.send_message("You are not connected to any voice channel!")
            return True

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("We are not chatting in a guild, something has gone very wrong...")
            return True

        if guild.voice_client is None:
            await user.voice.channel.connect(self_deaf=True)
            return False

        if user.voice.channel != guild.voice_client.channel:
            await interaction.response.send_message("Join the same voice channel where I am")
            return True

        return False

    def play_song(self, interaction: Interaction, exception: Exception | None) -> None:
        if exception is not None:
            raise exception

        song = self.queue.popleft()

        self.options.cache_path.mkdir(parents=True, exist_ok=True)
        song_path = self.subsonic.media_retrieval.download(song.id, self.options.cache_path)

        interaction.guild.voice_client.play(
            discord.FFmpegPCMAudio(
                str(song_path.absolute()),
            ),
            after=lambda e: self.play_song(interaction, e),
        )

    @app_commands.command(description="Play a song")
    async def play(self, interaction: Interaction, song_name: str) -> None:
        if await self.is_not_in_channel(interaction):
            return None

        songs = self.subsonic.searching.search(song_name, song_count=10, album_count=0, artist_count=0).songs
        if songs is None:
            await self.send_embed(interaction, f"No song found with the name: {song_name}")
            return None

        song = songs[0]
        if song.title is None:
            # TODO: Improve message
            await self.send_embed(interaction, f"The song is missing required metadata: {song_name}")
            return None

        self.queue.append(Song(song.id, song.title))
        await self.send_embed(interaction, f"Playing song: {song.title}")

        if not interaction.guild.voice_client.is_playing():
            self.play_song(interaction, None)
