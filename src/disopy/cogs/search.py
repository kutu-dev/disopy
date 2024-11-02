# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Holds the cog for search commands."""

from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from ..options import Options
from .base import Base


class Search(Base):
    """Cog that holds search related commands."""

    def __init__(self, bot: Bot, options: Options, subsonic: Subsonic) -> None:
        """The constructor of the cog.

        Args:
            bot: The bot attached to the cog.
            subsonic: The object to be used to access the OpenSubsonic REST API.
        """

        super().__init__(bot, options)

        self.subsonic = subsonic

    def api_search(self, query: str, choice: str) -> tuple[str, list[str]]:
        """Search using a proper API endpoint in the REST API.

        Args:
            query: The query to be searched.
            what: What thing should be searched ("song", "album", "artist")

        Returns:
            A tuple that contains both the title and the content for the embed.
        """

        title = ""
        content = []

        song_count = 0
        album_count = 0
        artist_count = 0

        match choice:
            case "song":
                song_count = 10
            case "album":
                album_count = 10
            case "artist":
                artist_count = 10

        search = self.subsonic.searching.search(
            query, song_count=song_count, album_count=album_count, artist_count=artist_count
        )

        match choice:
            case "song":
                songs = search.songs[:10] if search.songs is not None else []
                title = f"🎵 Songs ({len(songs)} results)"

                for song in songs:
                    content.append(
                        f"- **{song.title}**" + (f" - {song.artist.name}" if song.artist is not None else "")
                    )

            case "album":
                albums = search.albums[:10] if search.albums is not None else []
                title = f"🎶 Albums ({len(albums)} results)"

                for album in albums:
                    content.append(
                        f"- **{album.name}**" + (f" - {album.artist.name}" if album.artist is not None else "")
                    )

            case "artist":
                artists = search.artists[:10] if search.artists is not None else []
                title = f"🎤 Artists ({len(artists)} results)"

                for artist in artists:
                    content.append(f"- **{artist.name}**")

        return title, content

    def playlist_search(self, query: str) -> tuple[str, list[str]]:
        """Naive search using the query as a substring of the name of the playlist.

        Args:
            query: The query to be searched.
            what: What thing should be searched.

        Returns:
            A tuple that contains both the title and the content for the embed.
        """

        content: list[str] = []

        for playlist in self.subsonic.playlists.get_playlists():
            if playlist.name is None:
                continue

            if query in playlist.name:
                content.append(f"- {playlist.name}")

        title = f"🎼 Playlists ({len(content)} results)"

        return title, content

    @app_commands.command(description="Search for a song, album, artist or playlist")
    @app_commands.choices(
        what=[
            app_commands.Choice(name="Song", value="song"),
            app_commands.Choice(name="Album", value="album"),
            app_commands.Choice(name="Artist", value="artist"),
            app_commands.Choice(name="Playlist", value="playlist"),
        ]
    )
    async def search(
        self,
        interaction: Interaction,
        query: str,
        # Ignore the MyPy error because discord.py uses the type to add autocompletion
        what: app_commands.Choice[str] = "song",  # type: ignore
    ) -> None:
        """Search a song, album, artist or playlist from the OpenSubsonic REST API.

        Args:
            interaction: The interaction that started the command.
            query: The query to be searched.
            what: What thing should be searched.
        """

        # Extract the type of element to be search, taking care of the default value
        choice = what if isinstance(what, str) else what.value

        title = ""
        content: list[str] = []

        if choice == "playlist":
            # Basic implementation just checking if the query is contained inside the playlist name
            title, content = self.playlist_search(query)
        else:
            title, content = self.api_search(query, choice)

        await self.send_answer(interaction, title, content)
