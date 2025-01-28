from backend.database import retrieve_playlist_infos_from_mongo
import json



date = "2025-01-28"
infos = retrieve_playlist_infos_from_mongo(date)

for track in infos["items"]:
    for artist in track["artists"]:
        if not(artist["image"]):
            print(artist)

with open("test.json", "w", encoding="utf-8") as f:
    json.dump(infos, f, ensure_ascii=False, indent=4)