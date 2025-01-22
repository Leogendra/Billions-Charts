from spotapi import PublicPlaylist
import json


PLAYLIST_ID = "37i9dQZF1DX7iB3RCnBnN4"

playlist = PublicPlaylist(PLAYLIST_ID)
playlist_info = playlist.get_playlist_info(limit=100)

with open("test.json", "w", encoding="utf-8") as f:
    json.dump(playlist_info, f, ensure_ascii=False, indent=4)