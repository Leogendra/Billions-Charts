from spotapi import Song, PublicPlaylist
from dotenv import load_dotenv
# import websockets
# import pymongo
# import redis
from report import generate_report
import datetime
import requests
import time
import json
import os

load_dotenv()
PLAYLIST_ID = os.getenv("PLAYLIST_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")




def get_access_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_playlist_infos(dataPath):
    # check if file already exists
    if os.path.exists(dataPath):
        print(f"Playlist infos already fetched in {dataPath}")
        return
    
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
            "playcount": int(item["itemV2"]["data"]["playcount"]),
            "contentRating": item["itemV2"]["data"]["contentRating"]["label"],
            "duration_ms": item["itemV2"]["data"]["trackDuration"]["totalMilliseconds"],
            "artists": [
                {
                    "name": artist["profile"]["name"],
                    "id": artist["uri"].split(":")[-1]
                }
                for artist in item["itemV2"]["data"]["artists"]["items"]
            ],
            "image": max(item["itemV2"]["data"]["albumOfTrack"]["coverArt"]["sources"], key=lambda x: x["width"])["url"],
            "image_size": max(item["itemV2"]["data"]["albumOfTrack"]["coverArt"]["sources"], key=lambda x: x["width"])["width"]
        })
        

    with open(dataPath, "w", encoding="utf-8") as f:
        json.dump(playlist_infos, f, indent=4, ensure_ascii=False)

    print(f"Playlist infos saved in {dataPath}")


def fetch_songs_infos(dataPath):
    # Query Spotify's public API to retrieve missing data
    with open(dataPath, "r", encoding="utf-8") as f:
        tracks_data = json.load(f)

    # check if infos is already fetched
    already_fetched = True
    for track in tracks_data["items"]:
        if ("popularity" not in track):
            print(f"Some songs infos are missing in {track['name']}")
            already_fetched = False
            break
    
    if already_fetched:
        print(" All songs infos already fetched.")
        return

    access_token = get_access_token()

    track_ids = [track["id"] for track in tracks_data["items"]]

    url = "https://api.spotify.com/v1/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    track_infos = []
    
    # Fetch track infos in chunks of 50
    for i in range(0, len(track_ids), 50):

        print(f"Fetching tracks {i} to {i + 50}...", end="\r")
        chunk = track_ids[i:i + 50]
        params = {"ids": ",".join(chunk)}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tracks_fetched = response.json()["tracks"]
        except:
            print("Error while fetching track info:", track)
        
        for track in tracks_fetched:                
            if track:
                track_infos.append({
                    "id": track["id"],
                    "popularity": track["popularity"],
                    "release_date": track["album"]["release_date"],
                    "release_date_precision": track["album"]["release_date_precision"]
                })
            else:
                print("Corrupted track info:", track)
                
    for i, track in enumerate(tracks_data["items"]):
        for info in track_infos:
            if (track["id"] == info["id"]):
                tracks_data["items"][i]["popularity"] = info["popularity"]
                tracks_data["items"][i]["release_date"] = info["release_date"]
                tracks_data["items"][i]["release_date_precision"] = info["release_date_precision"]
                break

    with open(dataPath, "w", encoding="utf-8") as f:
        json.dump(tracks_data, f, indent=4, ensure_ascii=False)

    print(f"Song infos saved in {dataPath}")
    
    


if __name__ == "__main__":

    TIME_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{TIME_KEY}.json"
    reportPath = f"data/reports/report_{TIME_KEY}.json"

    fetch_playlist_infos(dataPath)
    fetch_songs_infos(dataPath)

    generate_report(dataPath, reportPath)