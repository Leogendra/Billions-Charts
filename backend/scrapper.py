from backend.database import add_to_database, retrieve_playlist_infos_from_mongo
from backend.utils import create_folder
from spotapi import PublicPlaylist, Artist
from dotenv import load_dotenv
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
    try:
        response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        raise Exception("Error in while fetching access token:", e)


def fetch_playlist_infos(dataPath, WRITE_TO_DATABASE):
    if WRITE_TO_DATABASE:
        dateKey = dataPath.split("_")[-1].split(".")[0]
        playlist = retrieve_playlist_infos_from_mongo(dateKey)
        if playlist:
            print(f"Playlist infos already fetched in database")
            return
    else:
        if os.path.exists(dataPath):
            print(f"Playlist infos already fetched in {dataPath}")
            return
        
    # Fetch playlist infos from Spotify
    create_folder("data/tracks/")
    try:
        playlist = PublicPlaylist(PLAYLIST_ID)
    except Exception as e:
        raise Exception("Error while creating PublicPlaylist:", e)

    print("Fetching playlist infos...")
    try:
        playlist_info = playlist.get_playlist_info(limit=5000)
        if not(playlist_info["data"]):
            raise Exception("Error while fetching playlist infos:", playlist_info["errors"] if playlist_info["errors"] else "No data returned")
    except Exception as e:
        raise Exception("Critical Error while fetching playlist infos:", e)
    
    raw_data = playlist_info["data"]["playlistV2"]

    # Clean playlist infos
    playlist_infos = {}
    playlist_infos["uri"] = raw_data["uri"]
    playlist_infos["name"] = raw_data["name"]
    playlist_infos["description"] = raw_data["description"]
    playlist_infos["followers"] = raw_data["followers"]
    playlist_infos["totalCount"] = raw_data["content"]["totalCount"]
    playlist_infos["generatedTimeStamp"] = int(time.time() * 1000)
    playlist_infos["date"] = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        playlist_infos["coverUrl"] = raw_data["images"]["items"][0]["sources"][0]["url"]
    except:
        playlist_infos["coverUrl"] = None # TODO: Add default image

    try:
        playlist_infos["coverHex"] = raw_data["images"]["items"][0]["extractedColors"]["colorRaw"]["hex"]
    except:
        playlist_infos["coverHex"] = "#000000"

    # Clean track infos
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


    # Fetch missing track infos
    access_token = get_access_token()
    track_ids = [track["id"] for track in playlist_infos["items"]]

    headers = {"Authorization": f"Bearer {access_token}"}
    track_infos = []
    
    # Fetch track infos in chunks of 50 (max limit)
    for i in range(0, len(track_ids), 50):
        print(f"Fetching tracks {i}/{len(track_ids)}...   ", end="\r")
        chunk = track_ids[i:i + 50]
        params = {"ids": ",".join(chunk)}

        try:
            response = requests.get(
                "https://api.spotify.com/v1/tracks", 
                headers=headers, 
                params=params
            )
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

    print(f"Fetching tracks {len(track_ids)}/{len(track_ids)} done!")
                
    # Merge track infos
    for i, track in enumerate(playlist_infos["items"]):
        for info in track_infos:
            if (track["id"] == info["id"]):
                playlist_infos["items"][i]["popularity"] = info["popularity"]
                playlist_infos["items"][i]["release_date"] = info["release_date"]
                playlist_infos["items"][i]["release_date_precision"] = info["release_date_precision"]
                break

    # Fetch Artists infos: genres, followers, popularity, images
    artist_ids = list({artist["id"] for track in playlist_infos["items"] for artist in track["artists"]})

    artists_infos = {}
    for i in range(0, len(artist_ids), 50):
        print(f"Fetching artists {i}/{len(artist_ids)}...   ", end="\r")
        batch = artist_ids[i:i + 50]
        params = {"ids": ",".join(batch)}

        try:
            response = requests.get(
                "https://api.spotify.com/v1/artists", 
                headers=headers, 
                params=params
            )
            response.raise_for_status()
            artists_batch = response.json()["artists"]
            
            for artist in artists_batch:
                artists_infos[artist["id"]] = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "genres": artist["genres"],
                    "followers": artist["followers"]["total"],
                    "popularity": artist["popularity"],
                    "image": max(artist["images"], key=lambda x: x["width"]) if artist["images"] else None
                }

        except Exception as e:
            print(f"Error fetching batch {i}: {e}")

    print(f"Fetching artists {len(artist_ids)}/{len(artist_ids)} done!")

    # Merge artists infos
    for i, track in enumerate(playlist_infos["items"]):
        for j, artist in enumerate(track["artists"]):
            playlist_infos["items"][i]["artists"][j] = artists_infos[artist["id"]]

    # Save or insert in database
    if WRITE_TO_DATABASE:
        add_to_database(playlist_infos)
        print("Song infos inserted in database.")

    else:
        with open(dataPath, "w", encoding="utf-8") as f:
            json.dump(playlist_infos, f, indent=4, ensure_ascii=False)
        print(f"Song infos saved in {dataPath}")