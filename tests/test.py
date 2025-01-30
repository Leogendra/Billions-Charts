from spotapi import PublicAlbum
import json

# query an artists
artist = PublicAlbum("3dQQAi7HumuMD2TL3Ky7t4")
artists_infos = artist.get_album_info()


if (artists_infos["data"] is not None):
    print("Good")
else:
    print("!!! Test failed !!!")

with open("test.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(artists_infos, indent=4))