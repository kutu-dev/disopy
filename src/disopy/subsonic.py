from pathlib import Path
from knuckles import Subsonic


def download_song(subsonic: Subsonic, song_query: str) -> None:
