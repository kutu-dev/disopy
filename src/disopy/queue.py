from .subsonic import Song
from discord import Interaction
import discord


class Queue:
    def __init__(self) -> None:
        self.songs: dict[str, list[Song]] = {}

    def get_guild_queue(self, guild_id: int) -> list[Song]:
        if not guild_id in self.songs:
            self.songs[guild_id] = []

        return self.songs[guild_id]

    def add_to_queue(self, song: Song, interaction: Interaction) -> None:
        """Add a song to the queue and plays it if no other song is playing"""

        self.get_guild_queue(interaction.guild_id).append(song)

        if not interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.play(
                discord.FFmpegPCMAudio(
                    source=self.get_guild_queue(interaction.guild_id)[0].stream_url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                ),
                after=lambda e: self.next_in_queue(interaction, e),
            )

    def next_in_queue(
        self, interaction: Interaction, e: Exception | None = None
    ) -> None:
        """Remove the current song in queue and play the next one"""

        if e is not None:
            raise e

        self.get_guild_queue(interaction.guild_id).pop(0)

        if len(self.get_guild_queue(interaction.guild_id)) == 0:
            return

        interaction.guild.voice_client.play(
            discord.FFmpegPCMAudio(
                source=self.get_guild_queue(interaction.guild_id)[0].stream_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            ),
            after=lambda e: self.next_in_queue(interaction, e),
        )

    def play_again(self, interaction: Interaction) -> None:
        # Yeah this sucks
        self.get_guild_queue(interaction.guild_id).insert(1, self.songs[0])
        interaction.guild.voice_client.stop()

    def clear_queue(self, interaction: Interaction) -> None:
        """Clear the queue and stops the song that is playing"""

        self.songs[interaction.guild_id]: list[Song] = []

        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
