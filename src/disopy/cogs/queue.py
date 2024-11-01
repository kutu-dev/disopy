# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Holds the cog for queue handling and music playback commands."""

import logging
from collections import deque
from typing import Iterable, NamedTuple, cast

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
    """Data representation for a Subsonic song.

    Attributes:
        id: The ID in the Subsonic server.
        title: The title of the song.
    """

    id: str
    title: str


class Queue:
    """Manage the queue and split it per guild."""

    def __init__(self) -> None:
        """Create a new queue."""

        self.queue: dict[str, deque[Song]] = {}

    def _check_guild(self, interaction: Interaction) -> str | None:
        """Check if a guild has an associated queue and if not creates a new one.

        Args:
            interaction: The interaction where the guild ID can be found.

        Returns:
            Either the guild ID or None if the interaction did not have a guild attach to it.
        """

        if interaction.guild is None:
            logger.error("The guild of the interaction was None!")
            return None

        id = str(interaction.guild.id)

        if id not in self.queue:
            self.queue[id] = deque()

        return id

    def get(self, interaction: Interaction) -> Iterable[Song]:
        """Get the queue of a guild.

        Args:
            interaction: The interaction where the guild ID can be found.

        Returns:
            An iterable with the songs of the queue.
        """

        id = self._check_guild(interaction)
        if id is None:
            return []

        return self.queue[id]

    def pop(self, interaction: Interaction) -> Song | None:
        """Remove and get one song from the queue.

        Args:
            interaction: The interaction where the guild ID can be found.

        Returns:
            The next song in the queue or None if the action failed.
        """

        id = self._check_guild(interaction)
        if id is None:
            return None

        return self.queue[id].pop()

    def append(self, interaction: Interaction, song: Song) -> None:
        """Append new songs to the queue.

        Args:
            interaction: The interaction where the guild ID can be found.
            song: The song to append.
        """

        id = self._check_guild(interaction)
        if id is None:
            return

        return self.queue[id].append(song)

    def length(self, interaction: Interaction) -> int:
        """Get the length of the queue.

        Args:
            interaction: The interaction where the guild ID can be found.

        Returns:
            The length of the queue.
        """

        id = self._check_guild(interaction)
        if id is None:
            # A little ugly but gets the job done
            return 0

        return len(self.queue[id])


class QueueCog(Base):
    """Cog that holds queue handling and music playback commands."""

    def __init__(self, bot: Bot, options: Options, subsonic: Subsonic, config: Config) -> None:
        """The constructor of the cog.

        Args:
            bot: The bot attached to the cog.
            options: The options of the program.
            subsonic: The object to be used to access the OpenSubsonic REST API.
            config: The config of the program.
        """

        super().__init__(bot, options)

        self.subsonic = subsonic
        self.config = config

        self.queue = Queue()

        self.skip_next_autoplay = False

    async def get_voice_client(self, interaction: Interaction) -> VoiceClient | None:
        """Get the voice client of an interaction.

        Args:
            interaction: The interaction to get the voice client from.

        Returns:
            The voice client or None if the interaction doesn't have one attach to it.
        """

        if interaction.guild is None:
            await self.send_embed(interaction, "We're not taking in a guild!")
            return None

        if interaction.guild.voice_client is None:
            await self.send_embed(interaction, "I'm not connected to a channel!")
            return None

        return cast(VoiceClient, interaction.guild.voice_client)

    async def is_not_in_channel(self, interaction: Interaction, connect: bool = False) -> bool:
        """Check if the user is with the bot in the same voice channel.

        Args:
            interaction: The interaction to get the voice channel from.
            connect: If the bot should automatically connect to the channel where the user is.

        Returns:
            If the user is with the bot in the same voice channel.
        """

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
        """Callback called when starting the playback of the next song in the queue.

        Args:
            interaction: The interaction where the guild will be extracted.
            exception: An exception that discord.py may have raised.
        """

        if self.skip_next_autoplay:
            self.skip_next_autoplay = False
            return

        self.play_queue(interaction, exception)

    def play_queue(self, interaction: Interaction, exception: Exception | None) -> None:
        """Play the next song in the queue.

        Args:
            interaction: The interaction where the guild will be extracted.
            exception: An exception that discord.py may have raised.
        """

        if exception is not None:
            raise exception

        if self.queue.length(interaction) == 0:
            logger.info("The queue is empty")
            return

        song = self.queue.pop(interaction)
        if song is None:
            logger.error("Unable to get the song for playback")
            return

        song_path = self.options.cache_path / "subsonic/songs" / f"{song.id}.audio"

        if not song_path.is_file():
            song_path.parent.mkdir(parents=True, exist_ok=True)
            self.subsonic.media_retrieval.download(song.id, song_path)

        if interaction.guild is None:
            logger.warning("There is no guild attached to the interaction!")
            return

        if interaction.guild.voice_client is None:
            logger.warning("There is not available voice client in this interaction!")
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
        """Add a song in the queue and start the playback if it's stop.

        Args:
            interaction: The interaction that started the command.
            song_name: The name of the song.
        """

        if await self.is_not_in_channel(interaction, True):
            return

        songs = self.subsonic.searching.search(song_name, song_count=10, album_count=0, artist_count=0).songs
        if songs is None:
            await self.send_embed(interaction, f"No song found with the name: {song_name}")
            return

        song = songs[0]
        if song.title is None:
            await self.send_embed(interaction, f"The song is missing required metadata: {song_name}")
            return

        self.queue.append(interaction, Song(song.id, song.title))
        await self.send_embed(interaction, "Feel the beets... 🎵", [f"Playing: **{song.title}**"])

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            self.play_queue(interaction, None)

    @app_commands.command(description="Stop the current song")
    async def stop(self, interaction: Interaction) -> None:
        """Stop the song that is currently playing.

        Args:
            interaction: The interaction that started the command.
        """

        if await self.is_not_in_channel(interaction):
            return

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_embed(interaction, "No song currently playing!")
            return

        self.skip_next_autoplay = True
        voice_client.stop()

        await self.send_embed(interaction, "Song stopped", [f"Stopped: **{voice_client.source.title}**"])

    @app_commands.command(description="Skip the current song")
    async def skip(self, interaction: Interaction) -> None:
        """Skip the currently playing song.

        Args:
            interaction: The interaction that started the command.
        """

        if await self.is_not_in_channel(interaction):
            return

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_embed(interaction, "No song currently playing!")
            return

        voice_client.stop()
        await self.send_embed(interaction, "Song skipped", [f"Skipped to: **{voice_client.source.title}**"])

    @app_commands.command(description="Resume the queue playback")
    async def resume(self, interaction: Interaction) -> None:
        """Resume the playback of the song and if there is no one playing play the next one in the queue.

        Args:
            interaction: The interaction that started the command.
        """

        if await self.is_not_in_channel(interaction):
            return

        if self.queue.length(interaction) == 0:
            await self.send_embed(interaction, "The queue is empty")
            return

        self.play_queue(interaction, None)
        await self.send_embed(interaction, "Resuming the playback", [f"Resumed: **{voice_client.source.title}**"])

    @app_commands.command(name="queue", description="See the current queue")
    # Name changed to avoid collisions with the property `queue`
    async def queue_command(self, interaction: Interaction) -> None:
        """List the songs added to the queue.

        Args:
            interaction: The interaction that started the command.
        """

        content = []
        for song in self.queue.get(interaction):
            content.append(f"- **{song.title}**")

        await self.send_embed(interaction, f"Queue ({self.queue.length(interaction)} remaining)", content)

    @app_commands.command(description="Adjust the volume")
    async def volume(self, interaction: Interaction, volume: int) -> None:
        """Adjust the volume of the playback.

        Args:
            interaction: The interaction that started the command.
            volume: The new volume level.
        """

        if volume < 0 or volume > 100:
            await self.send_embed(interaction, "Volume must be between 0 and 100")
            return

        self.config.volume = volume
        await self.send_embed(interaction, f"Volume set to {volume}%")

    @app_commands.command(description="Pause the current song")
    async def pause(self, interaction: Interaction) -> None:
        """Pause the song that is currently playing.

        Args:
            interaction: The interaction that started the command.
        """

        if await self.is_not_in_channel(interaction):
            return

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_embed(interaction, "No song currently playing!")
            return

        voice_client.pause()
        await self.send_embed(interaction, "Song paused", [f"Paused: **{voice_client.source.title}**"])
