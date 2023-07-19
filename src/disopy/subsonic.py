from .main import CONFIG
from .authentication import Auth
from .messages import info, warn, error
from dataclasses import dataclass
from typing import Callable
import urllib
import requests
import xml.etree.ElementTree as ET
from colorama import Fore, Style


@dataclass()
class Song:
    """Song model"""

    title: str
    stream_url: str


class Subsonic:
    def __init__(self) -> None:
        self.auth: Auth = Auth()
        self.url: str = CONFIG["subsonicUrl"]

        self.params: dict[str, str] = {
            "u": CONFIG["user"]["username"],
            "t": self.auth.token,
            "s": self.auth.salt,
            "v": "1.15.0",
            # Client name
            "c": "Subrift",
        }

        self.info: Callable[[str], None] = lambda message: info(
            f"{Fore.MAGENTA}Subsonic{Style.RESET_ALL}", message
        )
        self.warn: Callable[[str], None] = lambda message: warn(
            f"{Fore.MAGENTA}Subsonic{Style.RESET_ALL}", message
        )
        self.error: Callable[[str], None] = lambda message: error(
            f"{Fore.MAGENTA}Subsonic{Style.RESET_ALL}", message
        )

    def xml_request(self, subroute: str, params: dict[str, str]) -> ET.Element:
        """
        Generic request to the Subsonic API in XML.

        Subroute should come in the format of /subroute, with the slash ahead of it.
        """

        r: requests.Response = requests.get(
            url=self.url + "/rest" + subroute,
            params=params,
        )

        return ET.fromstring(r.text)

    def build_url(self, subroute: str, params: dict) -> str:
        """
        Generates a generic Subsonic API URL.

        Subroute should come in the format of /subroute, with the slash ahead of it.
        """

        return f"{self.url}/rest{subroute}?{urllib.parse.urlencode(params)}"

    def build_song(self, atrib: dict[str, str]) -> Song:
        stream_url: str = self.build_url("/stream", {**self.params, "id": atrib["id"]})

        # Make a model of only the necessary data of the song
        return Song(title=atrib["title"], stream_url=stream_url)

    def ping(self) -> bool:
        """Test if the server is only and return true only if the status is ok."""

        response: ET.Element = self.xml_request("/ping", self.params)
        self.info("Requested ping to server")

        if response.attrib["status"] == "ok":
            self.info("Requested ping returned ok status")
            return True
        elif response.attrib["status"] == "failed":
            self.warn("Requested ping returned failed status")
            return False
        else:
            self.error("Requested ping returned an unexpected status value")
            return False

    def get_album(self, id: str) -> list[Song]:
        """Generates a list of Songs"""

        album_data: ET.Element = self.xml_request(
            "/getAlbum", {**self.params, "id": id}
        )[0]

        album_songs: list[Song] = []

        for song in album_data:
            album_songs.append(self.build_song(song.attrib))

        return album_songs

    def search_song(self, query: str) -> Song | None:
        """Search a song with a query and generates a Song model with the first result or None if no one is found"""

        self.info(f'Searching a song with the query "{query}"')

        search_results: ET.Element = self.xml_request(
            "/search3", {**self.params, "query": query}
        )[0]

        only_songs_results: list[ET.Element] = [
            result
            for result in search_results
            if result.tag == "{http://subsonic.org/restapi}song"
        ]

        # Return None if no song is found
        if len(only_songs_results) == 0:
            self.warn(f"No song has been matched")
            return None

        first_song_result_metadata = only_songs_results[0].attrib

        # Make a model of only the necessary data of the song
        song: Song = self.build_song(first_song_result_metadata)
        self.info(f'Matched the song "{song.title}"')

        return song

    def search_album(self, query: str) -> list[Song] | None:
        """Search an album with a query and returns a list of Song models with all the songs in the album or None is no album is found"""

        self.info(f'Searching an album with the query "{query}"')

        search_results: ET.Element = self.xml_request(
            "/search3", {**self.params, "query": query}
        )[0]

        only_albums_results: list[ET.Element] = [
            result
            for result in search_results
            if result.tag == "{http://subsonic.org/restapi}album"
        ]

        # Return None if no album is found
        if len(only_albums_results) == 0:
            self.warn(f"No album has been matched")
            return None

        first_album_result_id: str = only_albums_results[0].attrib["id"]
        self.info(f'Matched the album "{only_albums_results[0].attrib["title"]}"')

        return self.get_album(first_album_result_id)

    def search_playlist(self, query: str) -> list[Song] | None:
        """Search an playlist with a query and returns a list of Song models with all the songs in the album or None is no playlist is found"""

        self.info(f'Searching a playlist with the query "{query}"')
        playlists_list: ET.Element = self.xml_request("/getPlaylists", self.params)[0]

        matched_playlist: str
        for playlist_element in playlists_list:
            if query in playlist_element.attrib["name"]:
                matched_playlist = playlist_element.attrib
                break

        if matched_playlist["id"] == None:
            self.warn(f"No playlist has been matched")
            return None

        playlist: ET.Element = self.xml_request(
            "/getPlaylist", {**self.params, "id": matched_playlist["id"]}
        )[0]

        only_entries: list[ET.Element] = [
            data
            for data in playlist
            if data.tag == "{http://subsonic.org/restapi}entry"
        ]

        song_list: list[Song] = [
            self.build_song(entry.attrib) for entry in only_entries
        ]

        self.info(f'Matched the playlist "{matched_playlist["name"]}"')

        return song_list
