from spotapi import PublicAlbum, Artist
import json



# query an artists
artist_url = "672zgt6YECMA7Om9h5V2HE"
artist = Artist()
artists_infos = artist.get_artist(artist_url)


if (artists_infos["data"] is not None):
    print("Good")
else:
    print("!!! Test failed !!!")

with open("tests/test.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(artists_infos, indent=4))