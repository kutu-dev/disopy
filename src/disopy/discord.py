# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import discord
from discord import app_commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
import base64
from knuckles import Subsonic

from .config import Config
from . import DEFAULT_CACHE_PATH

logger = logging.getLogger(__name__)


async def is_not_in_channel(interaction: Interaction) -> bool:
    user = interaction.user
    if isinstance(user, discord.User):
        await interaction.response.send_message("You are not a member of the guild, something has gone very wrong...")
        return True

    if user.voice is None or user.voice.channel is None:
        await interaction.response.send_message("You are not connected to any voice channel!")
        return True

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("We are not chatting in a guild, something has gone very wrong...")
        return True

    if guild.voice_client is None:
        await user.voice.channel.connect()
        return False

    if user.voice.channel != guild.voice_client.channel:
        await interaction.response.send_message("Join the same voice channel where I am")
        return True

    return False


def get_bot(subsonic: Subsonic, config: Config) -> Bot:
    """Get the Discord bot.

    Args:
        subsonic: The object to be used to access the OpenSubsonic REST API.
        config: The configurations of the program.

    Returns:
        A configured ready to use bot
    """

    intents = discord.Intents.default()
    bot = discord.ext.commands.Bot("!", intents=intents)

    async def send_embed(
        interaction: Interaction, title: str, content: list[str] | None = None, ephemeral: bool = False
    ) -> None:
        embed: discord.Embed = discord.Embed(
            description="\n".join(content) if content is not None else None, color=discord.Color.from_rgb(124, 0, 40)
        )

        if bot.user is None:
            logger.error("The bot doesn't have a user attach to it!")
            return

        icon_url = None
        if bot.user.avatar is not None:
            icon_url = bot.user.avatar.url

        embed.set_author(name=f"{title}", icon_url=icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @bot.event
    async def on_ready() -> None:
        logger.info(f"Logged in as '{bot.user}'")

        if config.developer_discord_sync_guild is not None:
            logger.info(
                f"Developer config detected, reloading command tree for guild: '{config.developer_discord_sync_guild}'"
            )
            guild_object = discord.Object(id=config.developer_discord_sync_guild)

            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

    @bot.tree.command(description="Get the latency of the bot")
    async def ping(interaction: Interaction) -> None:
        subsonic_status = "Ok ✅" if subsonic.system.ping().status == "ok" else "Failed ❌"

        await send_embed(
            interaction,
            "Pong! 🏓",
            [f"Bot latency: **{int(bot.latency * 1000)}ms**", f"Subsonic status: **{subsonic_status}**"],
        )

    @bot.tree.command(description="Sync the slash commands to the Discord cache globaly")
    async def sync(interaction: discord.Interaction) -> None:
        if interaction.user.id not in config.developer_discord_sync_users:
            await send_embed(interaction, "Action not authorized", ephemeral=True)
            return

        await bot.tree.sync()
        await send_embed(interaction, "Command tree reloaded", ephemeral=True)

    @bot.tree.command(description="Search for a song, album, artist or playlist")
    @app_commands.choices(
        what=[
            app_commands.Choice(name="Song", value="song"),
            app_commands.Choice(name="Album", value="album"),
            app_commands.Choice(name="Artist", value="artist"),
            app_commands.Choice(name="Playlist", value="playlist"),
        ]
    )
    async def search(
        interaction: Interaction,
        query: str,
        # Ignore the MyPy error because discord.py uses the type to add autocompletion
        what: app_commands.Choice[str] = "song",  # type: ignore
    ) -> None:
        choice = what if isinstance(what, str) else what.value

        if choice == "playlist":
            # TODO: Implement this somehow (ask in GH?)
            await send_embed(
                interaction,
                "To be implemented!",
                ["[Check the GitHub for updates](https://github.com/kutu-dev/disopy)"],
            )

        match choice:
            case "song":
                songs = subsonic.searching.search(query, song_count=10, album_count=0, artist_count=0).songs
                songs = songs[:10] if songs is not None else []

                content = [
                    f"- **{song.title}**{f"- {song.artist.name}" if song.artist is not None else ""}" for song in songs
                ]
                await send_embed(interaction, f"Songs: {len(songs)} results", content)

            case "album":
                albums = subsonic.searching.search(query, song_count=0, album_count=10, artist_count=0).albums
                albums = albums[:10] if albums is not None else []

                content = [
                    f"- **{album.name}**{f" - {album.artist.name}" if album.artist is not None else ""}"
                    for album in albums
                ]
                await send_embed(interaction, f"Albums: {len(albums)} results", content)

            case "artist":
                artists = subsonic.searching.search(query, song_count=0, album_count=0, artist_count=10).artists
                artists = artists[:10] if artists is not None else []

                content = [f"- **{artist.name}**" for artist in artists]
                await send_embed(interaction, f"Artists: {len(artists)} results", content)

    @bot.tree.command(description="Play a song")
    async def play(interaction: Interaction, song_name: str) -> None:
        if await is_not_in_channel(interaction):
            return None

        songs = subsonic.searching.search(song_name, song_count=10, album_count=0, artist_count=0).songs
        if songs is None:
            return None

        song = songs[0]
        DEFAULT_CACHE_PATH.mkdir(parents=True, exist_ok=True)
        song_path = subsonic.media_retrieval.download(song.id, DEFAULT_CACHE_PATH)

        interaction.guild.voice_client.play(
            discord.FFmpegPCMAudio(
                str(song_path.absolute()),
            ),
        )

        await interaction.response.send_message(f"Playing song {song_name}")

    return bot
