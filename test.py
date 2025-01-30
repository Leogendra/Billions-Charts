from spotapi import Artist, Song
import json




artist_id = "508jmRnvWMx4TLLJ12uidt"
artist = Song()
artist_infos = artist.get_track_info(artist_id)

with open("test.json", "w", encoding="utf-8") as f:
    json.dump(artist_infos, f, ensure_ascii=False, indent=4)
