from .main import CONFIG
from .queue import Queue
from .subsonic import Song, Subsonic
from .messages import info, warn, error
import asyncio
import sys
from typing import Callable
import discord
from discord import Interaction, app_commands
from requests import Response
from colorama import Fore, Style


def start_client() -> None:
    print_info: Callable[[str], None] = lambda message: info(
        f"{Fore.BLUE}Discord{Style.RESET_ALL} ", message
    )
    print_warn: Callable[[str], None] = lambda message: warn(
        f"{Fore.BLUE}Discord{Style.RESET_ALL} ", message
    )
    print_error: Callable[[str], None] = lambda message: error(
        f"{Fore.BLUE}Discord{Style.RESET_ALL} ", message
    )

    intents: discord.Intents = discord.Intents.default()
    client: discord.Client = discord.Client(intents=intents)
    tree: discord.app_commands.CommandTree = discord.app_commands.CommandTree(client)

    queue: Queue = Queue()
    subsonic: Subsonic = Subsonic()

    async def send_embed(
        interaction: Interaction, title: str, description: str
    ) -> None:
        embed: discord.Embed = discord.Embed(
            description=description, color=discord.Color.from_rgb(50, 48, 153)
        )
        embed.set_author(name=f"| {title}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @client.event
    async def on_ready() -> None:
        print_info(f"Logged in as {client.user} (ID: {client.user.id})")

        print_info("Testing Subsonic server status")
        if subsonic.ping():
            print_info("Connection successfully established")
        else:
            print_error("Failed to establish a connection. Aborting!")
            sys.exit(1)

        # Sync slash commands
        await tree.sync()

    @tree.command(name="ping", description="Test the connection to the Subsonic server")
    async def ping(interaction: Interaction) -> None:
        print_info("Requested a ping to the Subsonic server")
        if subsonic.ping():
            await send_embed(
                interaction,
                "Server ping",
                "Successfully connected to the Subsonic server!",
            )
            print_info("Successfully connected to the Subsonic server!")
        else:
            await send_embed(
                interaction,
                "Server ping",
                "Failed to connect to the Subsonic server",
            )
            print_warn("Failed to connect to the Subsonic server")

    @tree.command(
        name="join", description="Join to the voice channel you're currently into"
    )
    async def join(interaction: Interaction) -> None:
        print_info(f"Requested join to a voice channel")
        if interaction.user.voice is None:
            await send_embed(
                interaction,
                "Join voice channel",
                "You need to join a voice channel first",
            )
            print_warn("The request failed as the user wasn't in a voice channel")
            return

        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
            print_info(f'Moved to the voice channel "{interaction.user.voice.channel}"')
        else:
            await interaction.user.voice.channel.connect(self_deaf=True)
            print_info(
                f'Connected to the voice channel "{interaction.guild.voice_client.channel}"'
            )

        await send_embed(
            interaction,
            "Join voice channel",
            "Connected to the channel",
        )

    @tree.command(name="leave", description="Disconnect from the voice channel")
    async def leave(interaction: Interaction) -> None:
        print_info("Requested disconnect from the voice channel")
        if interaction.guild.voice_client is None:
            await send_embed(
                interaction,
                "Leave voice channel",
                "I'm not connected to any voice channel",
            )
            print_warn("The request failed as the bot wasn't in a voice channel")
            return

        # Done it in this order because cleanup() exits the function
        print_info(
            f'Successfully disconnected to the voice channel "{interaction.guild.voice_client.channel}"'
        )
        await interaction.guild.voice_client.disconnect()
        await send_embed(
            interaction,
            "Leave voice channel",
            "Disconnected from the channel",
        )
        queue.clear_queue(interaction)
        interaction.guild.voice_client.cleanup()

    @tree.command(name="song", description="Play the searched song")
    @app_commands.describe(query="Search term to be played")
    async def song(interaction: Interaction, query: str) -> None:
        if interaction.user.voice is None:
            await send_embed(
                interaction,
                "Play song",
                "You need to join a voice channel first",
            )
            print_warn("The request failed as the user wasn't in a voice channel")
            return

        song: Song | None = subsonic.search_song(query)

        if song is None:
            await send_embed(
                interaction,
                "Play song",
                "No song has been found",
            )
            print_warn("The request failed as the song wasn't find")
            return

        if (
            interaction.guild.voice_client is not None
            and interaction.guild.voice_client.channel != interaction.user.voice.channel
        ):
            if interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()

            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
            print_info(
                f'Moved to the voice channel "{interaction.guild.voice_client.channel}"'
            )
        elif interaction.guild.voice_client is None:
            await interaction.user.voice.channel.connect(self_deaf=True)
            print_info(
                f'Connected to the voice channel "{interaction.guild.voice_client.channel}"'
            )

        if interaction.guild.voice_client.is_playing():
            await send_embed(
                interaction,
                "Play song",
                f'"{song.title}" added to queue',
            )
            print_info(f'Added the song "{song.title}" to the queue')
        else:
            await send_embed(
                interaction,
                "Play song",
                f'Now playing: "{song.title}"',
            )
            print_info(f'Started playing "{song.title}"')

        queue.add_to_queue(song, interaction)

    @tree.command(name="pause", description="Pause the player")
    async def pause(interaction: Interaction) -> None:
        print_info("Requested pause the song")
        if interaction.guild.voice_client is None:
            await send_embed(
                interaction,
                "Pause song",
                "No song is playing",
            )
            print_warn("The request failed as no song was playing")
            return

        if not interaction.guild.voice_client.is_playing():
            await send_embed(
                interaction,
                "Pause song",
                "No song is playing",
            )
            print_warn("The request failed as no song was playing")
            return

        interaction.guild.voice_client.pause()
        await send_embed(
            interaction,
            "Pause song",
            "Song paused",
        )
        print_info("Successfully paused the song")

    @tree.command(name="resume", description="Resume the player")
    async def resume(interaction: Interaction) -> None:
        print_info("Requested resume the song")
        if interaction.guild.voice_client is None:
            await send_embed(
                interaction,
                "Resume song",
                "No song is paused",
            )
            print_warn("The request failed as no song was paused")
            return

        if not interaction.guild.voice_client.is_paused():
            await send_embed(
                interaction,
                "Resume song",
                "No song is paused",
            )
            print_warn("The request failed as no song was paused")
            return

        interaction.guild.voice_client.resume()
        await send_embed(
            interaction,
            "Resume song",
            "Song resumed",
        )
        print_info("Successfully resumed the song")

    @tree.command(name="skip", description="Skip the current song")
    async def skip(interaction: Interaction) -> None:
        print_info("Requested skip the song")

        # As every song has an after function pointing to next_in_queue
        # the only way to truly stop the player is disconnecting it
        if not interaction.guild.voice_client.is_playing():
            await send_embed(
                interaction,
                "Skip song",
                "No song is playing",
            )
            print_warn("The request failed as no song was playing")

        await send_embed(
            interaction,
            "Skip song",
            "Song skipped",
        )
        print_info("Successfully skipped the song")
        interaction.guild.voice_client.stop()

    @tree.command(name="clear", description="Clear the queue")
    async def clear(interaction: Interaction) -> None:
        print_info("Requested clear the queue")

        await send_embed(
            interaction,
            "Clear queue",
            "Queue cleared",
        )
        print_info("Successfully cleared the queue")
        queue.clear_queue(interaction)

    @tree.command(name="queue", description="Prints the current queue")
    async def list_queue(interaction: Interaction) -> None:
        print_info("Requested list the queue")

        queue_list: list[Song] = queue.get_guild_queue(interaction.guild_id)

        if len(queue_list) == 0:
            await send_embed(interaction, "List queue", "The queue is empty")
            print_info("Successfully listed the queue")
            return

        if len(queue_list) >= 20:
            queue_list = queue_list[:20]

        stylized_songs: list[str] = [
            f"{i+1}. {song.title}" for i, song in enumerate(queue_list)
        ]

        if len(stylized_songs) >= 20:
            stylized_songs.append("And more...")
        stylized_songs.insert(0, "The current queue is:")

        if (
            interaction.guild.voice_client is not None
            and interaction.guild.voice_client.is_playing()
        ):
            stylized_songs[1] = f"**{stylized_songs[1]}** *(now playing)*"

        await send_embed(
            interaction,
            "List queue",
            "\n".join(stylized_songs),
        )
        print_info("Successfully listed the queue")

    @tree.command(name="restart", description="Restart the current song")
    async def restart(interaction: Interaction) -> None:
        print_info("Requested restart the song")

        if (
            interaction.guild.voice_client is None
            or not interaction.guild.voice_client.is_playing()
        ):
            await send_embed(
                interaction,
                "Restart song",
                "No song is playing",
            )
            print_warn("The request failed as no song was playing")

        await send_embed(
            interaction,
            "Restart song",
            "Replaying the current song",
        )
        print_info("Successfully replayed the song")
        queue.play_again(interaction)

    @tree.command(name="album", description="Add an album to the queue")
    @app_commands.describe(query="Search term to be added")
    async def album(interaction: Interaction, query: str):
        if interaction.user.voice is None:
            await send_embed(
                interaction,
                "Play album",
                "You need to join a voice channel first",
            )
            print_warn("The request failed as the user wasn't in a voice channel")
            return

        album: list[Song] | None = subsonic.search_album(query)

        if album is None:
            await send_embed(
                interaction,
                "Play album",
                "No album has been found",
            )
            print_warn("The request failed as the album wasn't find")
            return

        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
        else:
            await interaction.user.voice.channel.connect(self_deaf=True)

        await send_embed(
            interaction,
            "Play album",
            "All songs added to the queue",
        )

        for song in album:
            print_info(f'Added the song "{song.title}" to the queue')
            queue.add_to_queue(song, interaction)

        print_info("Successfully added all the songs from the album")

    @tree.command(name="playlist", description="Add an playlist to the queue")
    @app_commands.describe(query="Search term to be added")
    async def playlist(interaction: Interaction, query: str):
        if interaction.user.voice is None:
            await send_embed(
                interaction,
                "Play playlist",
                "You need to join a voice channel first",
            )
            print_warn("The request failed as the user wasn't in a voice channel")
            return

        playlist: list[Song] | None = subsonic.search_playlist(query)

        if playlist is None:
            await send_embed(
                interaction,
                "Play playlist",
                "No playlist has been found",
            )
            print_warn("The request failed as the playlist wasn't find")
            return

        if playlist == []:
            await send_embed(
                interaction,
                "Play playlist",
                "This playlist is empty",
            )
            print_warn("The request failed as the playlist was empty")
            return

        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
        else:
            await interaction.user.voice.channel.connect(self_deaf=True)

        await send_embed(
            interaction,
            "Play playlist",
            "All songs added to the queue",
        )

        for song in playlist:
            print_info(f'Added the song "{song.title}" to the queue')
            queue.add_to_queue(song, interaction)

        print_info("Successfully added all the songs from the playlist")

    async def start_bot() -> None:
        async with client:
            await client.start(CONFIG["discordToken"])

    asyncio.run(start_bot())
