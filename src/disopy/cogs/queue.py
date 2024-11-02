# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Holds the cog for queue handling and music playback commands."""

import logging
from collections import deque
from typing import Iterable, NamedTuple, cast

import discord
from discord import PCMVolumeTransformer, VoiceClient, app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..config import Config
from ..options import Options
from .base import Base


class Song(NamedTuple):
    """Data representation for a Subsonic song.

    Attributes:
        id: The ID in the Subsonic server.
        title: The title of the song.
    """

    id: str
    title: str


logger = logging.getLogger(__name__)


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
        self.now_playing: Song | None = None

        self.skip_next_autoplay = False

    async def get_voice_client(self, interaction: Interaction, connect: bool = False) -> VoiceClient | None:
        user = interaction.user
        if isinstance(user, discord.User):
            await self.send_error(interaction, ["You are not a member of the guild, something has gone very wrong..."])
            return None

        if user.voice is None or user.voice.channel is None:
            await self.send_error(interaction, ["You are not connected to any voice channel!"])
            return None

        guild = interaction.guild
        if guild is None:
            await self.send_error(interaction, ["We are not chatting in a guild, something has gone very wrong..."])
            return None

        if guild.voice_client is None:
            if connect:
                return await user.voice.channel.connect(self_deaf=True)
            await self.send_error(interaction, ["I'm not connected to a voice channel!"])
            return None

        if user.voice.channel != guild.voice_client.channel:
            await self.send_error(interaction, ["Join the same voice channel where I am"])
            return None

        return cast(VoiceClient, guild.voice_client)

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
            discord.FFmpegPCMAudio(str(song_path.absolute())),
            # The ugliest Python syntax ever added to the language. The only way to do an conditional in a lambda
            # is with ternary operator, the value it returns is meaningless
            after=lambda exception: self.play_next_callback(interaction, exception),
        )

        if voice_client.source is None:
            logger.error("The source is not available to attach a volume transformer!")
            return

        self.now_playing = song
        voice_client.source = PCMVolumeTransformer(voice_client.source, volume=self.config.volume / 100)

    @app_commands.command(description="Add a song, album, or playlist to the queue")
    @app_commands.choices(
        what=[
            app_commands.Choice(name="Song", value="song"),
            app_commands.Choice(name="Album", value="album"),
            app_commands.Choice(name="Playlist", value="playlist"),
        ]
    )
    async def play(
        self,
        interaction: Interaction,
        query: str,
        # Ignore the MyPy error because discord.py uses the type to add autocompletion
        what: app_commands.Choice[str] = "song",  # type: ignore
    ) -> None:
        """Add a song in the queue and start the playback if it's stop.

        Args:
            interaction: The interaction that started the command.
            song_name: The name of the song.
        """

        # Extract the type of element to be search, taking care of the default value
        choice = what if isinstance(what, str) else what.value

        voice_client = await self.get_voice_client(interaction, True)
        if voice_client is None:
            return

        playing_element_name = query
        first_play = self.queue.length(interaction) == 0 and self.now_playing is None

        match choice:
            case "song":
                songs = self.subsonic.searching.search(query, song_count=10, album_count=0, artist_count=0).songs
                if songs is None:
                    await self.send_error(interaction, [f"No songs found with the name: **{query}**"])
                    return

                song = songs[0]
                if song.title is None:
                    await self.send_error(interaction, [f"The song is missing the required metadata: {query}"])
                    return

                playing_element_name = song.title
                self.queue.append(interaction, Song(song.id, song.title))

            case "album":
                albums = self.subsonic.searching.search(query, song_count=0, album_count=10, artist_count=0).albums
                if albums is None:
                    await self.send_error(interaction, [f"No albums found with the name: **{query}**"])
                    return

                album = albums[0].generate()
                print(album)
                if album.songs is None:
                    await self.send_error(interaction, [f"The album is missing the required metadata: {query}"])
                    return

                if album.name is not None:
                    playing_element_name = album.name

                for song in album.songs:
                    if song.title is None:
                        logger.error(f"The song with ID '{song.id}' is missing the name metadata entry")
                        continue

                    self.queue.append(interaction, Song(song.id, song.title))

            case "playlist":
                for playlist in self.subsonic.playlists.get_playlists():
                    if playlist.name is None:
                        continue

                    if query in playlist.name:
                        playlist = playlist.generate()
                        if playlist.songs is None:
                            await self.send_error(interaction, ["The playlist has no songs!"])
                            return

                        if playlist.name is not None:
                            playing_element_name = playlist.name

                        for song in playlist.songs:
                            if song.title is None:
                                logger.error(f"The song with ID '{song.id}' is missing the name metadata entry")
                                continue

                            self.queue.append(interaction, Song(song.id, song.title))
                        break

        if first_play:
            await self.send_answer(interaction, "🎵 Now playing!", [f"**{playing_element_name}**"])
        else:
            await self.send_answer(interaction, "🎧 Added to the queue", [f"**{playing_element_name}**"])

        if not voice_client.is_playing():
            self.play_queue(interaction, None)

    @app_commands.command(description="Stop the current song")
    async def stop(self, interaction: Interaction) -> None:
        """Stop the song that is currently playing.

        Args:
            interaction: The interaction that started the command.
        """

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_error(interaction, ["No song currently playing!"])
            return

        self.skip_next_autoplay = True
        voice_client.stop()
        self.now_playing = None

        await self.send_answer(interaction, "🛑 Song stopped")

    @app_commands.command(description="Pause the current song")
    async def pause(self, interaction: Interaction) -> None:
        """Pause the song that is currently playing.

        Args:
            interaction: The interaction that started the command.
        """

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_error(interaction, ["No song currently playing!"])
            return

        voice_client.pause()
        await self.send_answer(interaction, "⏸️ Song paused")

    @app_commands.command(description="Skip the current song")
    async def skip(self, interaction: Interaction) -> None:
        """Skip the currently playing song.

        Args:
            interaction: The interaction that started the command.
        """

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if not voice_client.is_playing():
            await self.send_error(interaction, ["No song currently playing!"])
            return

        voice_client.stop()
        await self.send_answer(interaction, "⏭️ Song skipped")

    @app_commands.command(description="Resume the playback")
    async def resume(self, interaction: Interaction) -> None:
        """Resume the playback of the song and if there is no one playing play the next one in the queue.

        Args:
            interaction: The interaction that started the command.
        """

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if voice_client.is_paused():
            voice_client.resume()
            await self.send_answer(interaction, "▶️ Resuming the song")
            return

        if self.queue.length(interaction) == 0:
            await self.send_error(interaction, ["The queue is empty"])
            return

        self.play_queue(interaction, None)
        await self.send_answer(interaction, "▶️ Resuming the playback")

    @app_commands.command(name="queue", description="See the current queue")
    # Name changed to avoid collisions with the property `queue`
    async def queue_command(self, interaction: Interaction) -> None:
        """List the songs added to the queue.

        Args:
            interaction: The interaction that started the command.
        """

        content = []
        if self.now_playing is not None:
            content.append(f"Now playing: **{self.now_playing.title}**")
            content.append("")

        length = self.queue.length(interaction)

        if length > 0:
            content.append("Next:")
            for song in self.queue.get(interaction):
                content.append(f"- **{song.title}**")

        if length == 0:
            content.append("_Queue empty_")

        await self.send_answer(interaction, f"🎹 Queue ({length} songs remaining)", content)

    @app_commands.command(description="Adjust the volume")
    async def volume(self, interaction: Interaction, volume: int) -> None:
        """Adjust the volume of the playback.

        Args:
            interaction: The interaction that started the command.
            volume: The new volume level.
        """

        voice_client = await self.get_voice_client(interaction)
        if voice_client is None:
            return

        if volume < 0:
            await self.send_error(interaction, ["The requested volume must be at least 0%"])
            return

        if voice_client.source is None:
            await self.send_error(interaction, ["The voice client source is not available"])
            return

        # Every source has a volume handler attach to it so suppressing the mypy error is safe
        voice_client.source.volume = volume / 100  # type: ignore[attr-defined]
        await self.send_answer(interaction, f"🔊 Volume level set to {volume}%")
