import spotapi
import json

import logging
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)


playlist = spotapi.PublicPlaylist("5ncmDMsWsIHoNSGyrZLDNb")
playlist_info = playlist.get_playlist_info(limit=5000, enable_watch_feed_entrypoint=True)
# print(playlist_info)


with open("test.json", "w") as f:
    f.write(json.dumps(playlist_info, indent=4))