from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.billions
global_collections = db.spotify_data # to remove after migration
playlists_collection = db.playlists_headers
tracks_collection = db.playlist_tracks
artists_collection = db.playlist_artists




### Insert data into the database ###

def insert_or_update_playlist_header(playlist_data):
    header_data = {
        "uri": playlist_data["uri"],
        "date": playlist_data["date"],
        "name": playlist_data["name"],
        "description": playlist_data["description"],
        "followers": playlist_data["followers"],
        "totalCount": playlist_data["totalCount"],
        "generatedTimeStamp": playlist_data["generatedTimeStamp"],
        "coverUrl": playlist_data["coverUrl"],
        "coverHex": playlist_data["coverHex"],
        # Include only the track ids and playcounts
        "items": [
            {
                "id": track["id"], 
                "playcount": track["playcount"],
                "popularity": track["popularity"],
            } 
            for track in playlist_data["items"]
        ]
    }

    # Upsert based on the date
    playlists_collection.update_one(
        {"date": playlist_data["date"]},
        {"$set": header_data},
        upsert=True,
    )


def insert_or_update_tracks(playlist_data):
    operations = []
    for track in playlist_data["items"]:
        track_data = {
            "id": track["id"],
            "name": track["name"],
            "added_at": track["added_at"],
            "contentRating": track["contentRating"],
            "duration_ms": track["duration_ms"],
            "artists": [{"id": artist["id"]} for artist in track["artists"]],
            "image": track["image"],
            "image_size": track["image_size"],
            "release_date": track["release_date"],
            "release_date_precision": track["release_date_precision"],
        }

        # Prepare the bulk write operations
        operations.append(
            UpdateOne(
                {"id": track["id"]},  # Match the track id
                {"$set": track_data},  # Update or insert
                upsert=True,
            )
        )

    if operations:
        tracks_collection.bulk_write(operations)


def insert_or_update_artists(playlist_data):
    operations = []
    for track in playlist_data["items"]:
        for artist in track["artists"]:
            artist_data = {
                "id": artist["id"],
                "name": artist.get("name", "Unknown"),
                "genres": artist.get("genres", []),
                "followers": artist.get("followers", -1),
                "popularity": artist.get("popularity", -1),
                "image": artist.get("image").get("url") if artist.get("image") else None,
                "image_size": artist.get("image").get("width") if artist.get("image") else None,
            }

            operations.append(
                UpdateOne(
                    {"id": artist["id"]},
                    {"$set": artist_data},
                    upsert=True,
                )
            )

    if operations:
        artists_collection.bulk_write(operations)


def add_to_database(playlist_data):
    insert_or_update_tracks(playlist_data)
    print("Tracks added to the database")
    insert_or_update_artists(playlist_data)
    print("Artists added to the database")
    insert_or_update_playlist_header(playlist_data)
    print("Playlist header added to the database")


### Retrieve data from the database ###

def retrieve_playlist_infos_from_mongo(date):
    # Retrieve the playlists headers data where the field "date" matches the input date
    data_count = playlists_collection.count_documents({"date": date})
    if (data_count == 0):
        print(f"No playlist data found for the date {date}")
        return None
    
    playlist_data = list(playlists_collection.find({"date": date}))[0]
    del playlist_data["_id"]

    # Retrieve the details of the tracks from the tracks collection
    track_ids = [track["id"] for track in playlist_data["items"]]
    tracks_details = list(tracks_collection.find({"id": {"$in": track_ids}}))
    track_details_dict = {track["id"]: track for track in tracks_details}

    for track in playlist_data["items"]:
        track_id = track["id"]
        if (track_id in track_details_dict):
            track.update(track_details_dict[track_id])
        del track["_id"]

    # Retrieve the artists details from the artists collection
    artist_ids = list({artist["id"] for track in playlist_data["items"] for artist in track["artists"]})
    artists_details = list(artists_collection.find({"id": {"$in": artist_ids}}))
    artist_details_dict = {artist["id"]: artist for artist in artists_details}

    for track in playlist_data["items"]:
        for artist in track["artists"]:
            artist_id = artist["id"]
            if (artist_id in artist_details_dict):
                artist.update(artist_details_dict[artist_id])
            del artist["_id"]

    return playlist_data