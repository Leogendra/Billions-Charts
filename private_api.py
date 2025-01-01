from spotapi import Song, PublicPlaylist
import pymongo
import redis
import websockets
import time
from dotenv import load_dotenv
import datetime
import json
import os

load_dotenv()
PLAYLIST_ID = os.getenv("PLAYLIST_ID")




def fetch_playlist_infos(dataPath):
    playlist = PublicPlaylist(PLAYLIST_ID)
    playlist_info = playlist.get_playlist_info(limit=1000)
    raw_data = playlist_info["data"]["playlistV2"]

    playlist_infos = {}
    playlist_infos["uri"] = raw_data["uri"]
    playlist_infos["name"] = raw_data["name"]
    playlist_infos["description"] = raw_data["description"]
    playlist_infos["followers"] = raw_data["followers"]
    playlist_infos["totalCount"] = raw_data["content"]["totalCount"]
    playlist_infos["generatedTimeStamp"] = int(time.time() * 1000)

    try:
        playlist_infos["coverUrl"] = raw_data["images"]["items"][0]["sources"][0]["url"]
    except:
        playlist_infos["coverUrl"] = None # TODO: Add default image

    try:
        playlist_infos["coverHex"] = raw_data["images"]["items"][0]["extractedColors"]["colorRaw"]["hex"]
    except:
        playlist_infos["coverHex"] = "#000000"

    playlist_infos["items"] = []
    for item in raw_data["content"]["items"]:
        playlist_infos["items"].append({
            "added_at": item["addedAt"]["isoString"],
            "id": item["itemV2"]["data"]["uri"].split(":")[-1],
            "name": item["itemV2"]["data"]["name"],
            "playcount": item["itemV2"]["data"]["playcount"],
            "contentRating": item["itemV2"]["data"]["contentRating"]["label"],
            "duration_ms": item["itemV2"]["data"]["trackDuration"]["totalMilliseconds"],
            "artists": [
                {
                    "name": artist["profile"]["name"],
                    "id": artist["uri"].split(":")[-1]
                }
                for artist in item["itemV2"]["data"]["artists"]["items"]
            ],
            "image": max(item["itemV2"]["data"]["albumOfTrack"]["coverArt"]["sources"], key=lambda x: x["width"])
        })
        

    with open(dataPath, "w", encoding="utf-8") as f:
        json.dump(playlist_infos, f, indent=4, ensure_ascii=False)

    print(f"Playlist infos saved in {dataPath}")


def fetch_songs_infos(dataPath):
    # TODO: Query Spotify's public API
    pass




if __name__ == "__main__":

    TIME_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{TIME_KEY}.json"

    fetch_playlist_infos(dataPath)
    fetch_songs_infos(dataPath)



    """
    song = Song()

    BELIEVER = "0pqnGHJpmpxLKifKRmU6WP"

    track_info = song.get_track_info(BELIEVER)
    with open("track_info.json", "w", encoding="utf-8") as f:
        json.dump(track_info, f, indent=4, ensure_ascii=False)


    songs = song.query_songs("Imagine Dragons", limit=3)
    data = songs["data"]["searchV2"]["tracksV2"]["items"]
    with open("songs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    """