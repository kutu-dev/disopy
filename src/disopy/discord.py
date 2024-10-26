import discord
import logging
from discord import app_commands
from discord.interactions import Interaction
import ctypes.util

logger = logging.getLogger(__name__)


def get_client() -> discord.Client:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @tree.command(
        name="ping", description="Get the latency of the bot client", guild=discord.Object(id=1299488936074412073)
    )
    async def ping(interaction: Interaction) -> None:
        await interaction.response.send_message(f"Pong! ({int(client.latency * 1000)}ms)")

    @tree.command(name="connect", description="TODO", guild=discord.Object(id=1299488936074412073))
    async def connect(interaction: Interaction) -> None:
        channel = interaction.user.voice.channel
        await channel.connect()

        await interaction.response.send_message(f"Connected to the channel: {channel}")

    @tree.command(name="play", description="TODO", guild=discord.Object(id=1299488936074412073))
    async def play(interaction: Interaction) -> None:
        guild = interaction.guild

        voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild=guild)

        audio_source = discord.FFmpegOpusAudio("test.opus")

        if not voice_client.is_playing():
            voice_client.play(audio_source, after=None)

        await interaction.response.send_message("TODO")

    @client.event
    async def on_ready() -> None:
        logger.info(f"Logged in as '{client.user}'")
        await tree.sync(guild=discord.Object(id=1299488936074412073))
        logging.debug("Refreshed command tree")

    return client
