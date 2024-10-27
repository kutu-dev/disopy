# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from knuckles import Subsonic

from .base import Base


class Search(Base):
    def __init__(self, bot: Bot, subsonic: Subsonic) -> None:
        super().__init__(bot)

        self.subsonic = subsonic

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
        choice = what if isinstance(what, str) else what.value

        if choice == "playlist":
            # TODO: Implement this somehow (ask in GH?)
            await self.send_embed(
                interaction,
                "To be implemented!",
                ["[Check the GitHub for updates](https://github.com/kutu-dev/disopy)"],
            )

        match choice:
            case "song":
                songs = self.subsonic.searching.search(query, song_count=10, album_count=0, artist_count=0).songs
                songs = songs[:10] if songs is not None else []

                content = [
                    f"- **{song.title}**{f"- {song.artist.name}" if song.artist is not None else ""}" for song in songs
                ]
                await self.send_embed(interaction, f"Songs ({len(songs)} results)", content)

            case "album":
                albums = self.subsonic.searching.search(query, song_count=0, album_count=10, artist_count=0).albums
                albums = albums[:10] if albums is not None else []

                content = [
                    f"- **{album.name}**{f" - {album.artist.name}" if album.artist is not None else ""}"
                    for album in albums
                ]
                await self.send_embed(interaction, f"Albums ({len(albums)} results)", content)

            case "artist":
                artists = self.subsonic.searching.search(query, song_count=0, album_count=0, artist_count=10).artists
                artists = artists[:10] if artists is not None else []

                content = [f"- **{artist.name}**" for artist in artists]
                await self.send_embed(interaction, f"Artists ({len(artists)} results)", content)
