from spotapi import PublicPlaylist
import json


playlist = PublicPlaylist("4bT9Ay9RHjruGhJIndqlw1")
playlist_info = playlist.get_playlist_info(limit=100)
# print(playlist_info)


with open("test.json", "w") as f:
    f.write(json.dumps(playlist_info, indent=4))