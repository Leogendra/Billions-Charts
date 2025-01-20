from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.billions
global_collections = db.spotify_data # to remove after migration
playlists_collection = db.playlists_headers
tracks_collection = db.playlist_tracks




def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


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
            "artists": track["artists"],
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

    # Execute the bulk write operations
    if operations:
        tracks_collection.bulk_write(operations)


def add_to_database(playlist_data):
    insert_or_update_playlist_header(playlist_data)
    insert_or_update_tracks(playlist_data)


def retrieve_playlist_infos_from_mongo(date):
    # Retrieve the playlists headers data where the field "date" matches the input date
    playlist_data = playlists_collection.find({"date": date})
    if (playlist_data.count() == 0):
        print(f"No playlist data found for the date {date}")
        return None
    
    playlist_data = list(playlist_data)[0]
    del playlist_data["_id"]

    # Retrieve the track ids from the playlist header
    track_ids = [track["id"] for track in playlist_data["items"]]

    # Retrieve the details of the tracks from the tracks collection
    tracks_details = list(tracks_collection.find({"id": {"$in": track_ids}}))

    track_details_dict = {track["id"]: track for track in tracks_details}

    for track in playlist_data["items"]:
        track_id = track["id"]
        if (track_id in track_details_dict):
            track.update(track_details_dict[track_id])
        del track["_id"]

    return playlist_data




import json
if __name__ == "__main__":
    dateKey = "2025-01-16"

    data = retrieve_playlist_infos_from_mongo(dateKey)
    with open("test.json", "w") as f:
        json.dump(data, f, default=convert_objectid, indent=4)