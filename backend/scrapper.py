from backend.track_enricher import enrich_tracks_with_correct_release_dates, fetch_artists_batch
from backend.musicbrainz_enricher import enrich_tracks_with_musicbrainz, enrich_artists_with_musicbrainz
from backend.database import add_to_database, check_playlist_header_from_mongo
from backend.database import tracks_collection, artists_collection
from backend.utils import create_folder
from spotapi import PublicPlaylist
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
        response = requests.post(
            url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET)
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        raise Exception("Error in while fetching access token:", e)


def fetch_raw_playlist():
    """Fetches raw playlist data from Spotify and returns a parsed dict."""
    create_folder("data/tracks/")
    try:
        playlist = PublicPlaylist(PLAYLIST_ID)
    except Exception as e:
        raise Exception("Error while creating PublicPlaylist:", e)

    print("Fetching playlist infos...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            playlist_info = playlist.get_playlist_info(limit=5000)
            if not playlist_info["data"]:
                raise Exception(
                    "Error while fetching playlist infos:",
                    (
                        playlist_info["errors"]
                        if playlist_info["errors"]
                        else "No data returned"
                    ),
                )
            break
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e}")
            if (attempt + 1) == max_retries:
                raise Exception("Critical Error while fetching playlist infos:", e)
            time.sleep(3)

    raw_data = playlist_info["data"]["playlistV2"]

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
    except Exception:
        playlist_infos["coverUrl"] = None

    try:
        playlist_infos["coverHex"] = raw_data["images"]["items"][0]["extractedColors"][
            "colorRaw"
        ]["hex"]
    except Exception:
        playlist_infos["coverHex"] = "#000000"

    playlist_infos["items"] = []
    for item in raw_data["content"]["items"]:
        playlist_infos["items"].append(
            {
                "added_at": item["addedAt"]["isoString"],
                "id": item["itemV2"]["data"]["uri"].split(":")[-1],
                "name": item["itemV2"]["data"]["name"],
                "playcount": int(item["itemV2"]["data"]["playcount"]),
                "contentRating": item["itemV2"]["data"]["contentRating"]["label"],
                "duration_ms": item["itemV2"]["data"]["trackDuration"][
                    "totalMilliseconds"
                ],
                "artists": [
                    {
                        "name": artist["profile"]["name"],
                        "id": artist["uri"].split(":")[-1],
                    }
                    for artist in item["itemV2"]["data"]["artists"]["items"]
                ],
                "image": max(
                    item["itemV2"]["data"]["albumOfTrack"]["coverArt"]["sources"],
                    key=lambda x: x["width"],
                )["url"],
                "image_size": max(
                    item["itemV2"]["data"]["albumOfTrack"]["coverArt"]["sources"],
                    key=lambda x: x["width"],
                )["width"],
            }
        )

    return playlist_infos


def enrich_with_release_dates(playlist_infos, headers, tracks_col, overwrite):
    """Enriches track items with correct release dates via ISRC lookup."""
    playlist_infos["items"] = enrich_tracks_with_correct_release_dates(
        playlist_infos["items"],
        headers,
        tracks_collection=tracks_col,
        overwrite=overwrite,
    )
    return playlist_infos


def enrich_with_artist_infos(playlist_infos, headers):
    """Fetches artist metadata (genres, followers, popularity, images) and merges it into each track."""
    artist_ids = list(
        {
            artist["id"]
            for track in playlist_infos["items"]
            for artist in track["artists"]
        }
    )
    artists_infos = fetch_artists_batch(artist_ids, headers)

    for i, track in enumerate(playlist_infos["items"]):
        for j, artist in enumerate(track["artists"]):
            playlist_infos["items"][i]["artists"][j] = artists_infos[artist["id"]]

    return playlist_infos


def enrich_with_musicbrainz(playlist_infos, tracks_col, artists_col):
    """Enriches tracks and artists with MusicBrainz fixed metadata (fetched once per entity)."""
    playlist_infos["items"] = enrich_tracks_with_musicbrainz(playlist_infos["items"], tracks_col)
    playlist_infos["items"] = enrich_artists_with_musicbrainz(playlist_infos["items"], artists_col)

    return playlist_infos


def persist_playlist(playlist_infos, dataPath, WRITE_TO_DATABASE):
    """Persists playlist data to MongoDB or a local JSON file."""
    print("Playlist infos fetched and enriched successfully!")
    if WRITE_TO_DATABASE:
        print("Writing to database...")
        add_to_database(playlist_infos)
        print("Song infos inserted in database.")
    else:
        print("Saving to file...")
        with open(dataPath, "w", encoding="utf-8") as f:
            json.dump(playlist_infos, f, indent=4, ensure_ascii=False)
        print(f"Song infos saved in {dataPath}")


def fetch_playlist_infos(dataPath, WRITE_TO_DATABASE, dateKey, overwrite=False):
    if WRITE_TO_DATABASE:
        if check_playlist_header_from_mongo(dateKey):
            print(f"Playlist infos already fetched in database")
            return
    else:
        if os.path.exists(dataPath):
            print(f"Playlist infos already fetched in {dataPath}")
            return

    playlist_infos = fetch_raw_playlist()
    playlist_infos["items"] = playlist_infos["items"]

    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    playlist_infos = enrich_with_release_dates(
        playlist_infos,
        headers,
        tracks_col=tracks_collection if WRITE_TO_DATABASE else None,
        overwrite=overwrite,
    )

    playlist_infos = enrich_with_artist_infos(playlist_infos, headers)

    playlist_infos = enrich_with_musicbrainz(
        playlist_infos,
        tracks_col=tracks_collection if WRITE_TO_DATABASE else None,
        artists_col=artists_collection if WRITE_TO_DATABASE else None,
    )

    persist_playlist(playlist_infos, dataPath, WRITE_TO_DATABASE)
