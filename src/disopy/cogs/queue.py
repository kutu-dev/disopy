# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from collections import deque
from typing import NamedTuple, cast

import discord
from discord import VoiceClient, app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..config import Config
from ..options import Options
from .base import Base

logger = logging.getLogger(__name__)


class Song(NamedTuple):
    id: str
    title: str


class Queue(Base):
    def __init__(self, bot: Bot, options: Options, subsonic: Subsonic, config: Config) -> None:
        super().__init__(bot, options)

        self.subsonic = subsonic
        self.config = config

        self.queue: deque[Song] = deque()
        self.skip_next_autoplay = False

    async def get_voice_client(self, interaction: Interaction) -> VoiceClient | None:
        if interaction.guild is None:
            await self.send_embed(interaction, "We're not taking in a guild!")
            return None

        if interaction.guild.voice_client is None:
            await self.send_embed(interaction, "I'm not connected to a channel!")
            return None

        return cast(VoiceClient, interaction.guild.voice_client)

    async def is_not_in_channel(self, interaction: Interaction, connect: bool = True) -> bool:
        # TODO: Invert the connect bool
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
            if connect:
                await user.voice.channel.connect(self_deaf=True)
            return False

        if user.voice.channel != guild.voice_client.channel:
            await interaction.response.send_message("Join the same voice channel where I am")
            return True

        return False

    def play_next_callback(self, interaction: Interaction, exception: Exception | None) -> None:
        if self.skip_next_autoplay:
            self.skip_next_autoplay = False
            return

        self.play_queue(interaction, exception)

    def play_queue(self, interaction: Interaction, exception: Exception | None) -> None:
        if exception is not None:
            raise exception

        if len(self.queue) == 0:
            logger.info("The queue is empty")
            return

        song = self.queue.popleft()
        song_path = self.options.cache_path / "subsonic/songs" / f"{song.id}.audio"

        if not song_path.is_file():
            song_path.parent.mkdir(parents=True, exist_ok=True)
            self.subsonic.media_retrieval.download(song.id, song_path)

        # TODO: This is ugly and repeated
        if interaction.guild is None:
            logger.warning("The interaction did not come from a guild")
            return

        if interaction.guild.voice_client is None:
            logger.warning("No available voice client")
            return

        voice_client = cast(VoiceClient, interaction.guild.voice_client)

        voice_client.play(
            discord.FFmpegPCMAudio(str(song_path.absolute()), options=f'-filter:a "volume={self.config.volume / 100}"'),
            # The ugliest Python syntax ever added to the language. The only way to do an conditional in a lambda
            # is with ternary operator, the value it returns is meaningless
            after=lambda exception: self.play_next_callback(interaction, exception),
        )

    @app_commands.command(description="Play a song")
    async def play(self, interaction: Interaction, song_name: str) -> None:
        if await self.is_not_in_channel(interaction):
            return

        songs = self.subsonic.searching.search(song_name, song_count=10, album_count=0, artist_count=0).songs
        if songs is None:
            await self.send_embed(interaction, f"No song found with the name: {song_name}")
            return

        song = songs[0]
        if song.title is None:
            await self.send_embed(interaction, f"The song is missing required metadata: {song_name}")
            return

        self.queue.append(Song(song.id, song.title))
        await self.send_embed(interaction, "Feel the beets... 🎵", [f"Playing: **{song.title}**"])

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            self.play_queue(interaction, None)

    @app_commands.command(description="Stop the current song")
    async def stop(self, interaction: Interaction) -> None:
        if await self.is_not_in_channel(interaction, False):
            return

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_embed(interaction, "No song currently playing!")
            return

        self.skip_next_autoplay = True
        voice_client.stop()

        await self.send_embed(interaction, "Song stopped")

    @app_commands.command(description="Skip the current song")
    async def skip(self, interaction: Interaction) -> None:
        if await self.is_not_in_channel(interaction, False):
            return

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_embed(interaction, "No song currently playing!")
            return

        voice_client.stop()
        await self.send_embed(interaction, "Song skipped")

    @app_commands.command(description="Resume the queue playback")
    async def resume(self, interaction: Interaction) -> None:
        if await self.is_not_in_channel(interaction, False):
            return

        if len(self.queue) == 0:
            await self.send_embed(interaction, "The queue is empty")

        self.play_queue(interaction, None)
        await self.send_embed(interaction, "Resuming the playback")

    @app_commands.command(name="queue", description="See the current queue")
    # Name changed to avoid collisions with the property `queue`
    async def queue_command(self, interaction: Interaction) -> None:
        content = []
        for song in self.queue:
            content.append(f"- **{song.title}**")

        await self.send_embed(interaction, f"Queue ({len(self.queue)} remaining)", content)
