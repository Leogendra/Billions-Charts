from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.billions
global_collections = db.spotify_data
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
        "tracks": [{"id": track["id"], "playcount": track["playcount"]} for track in playlist_data["items"]]
    }

    # Upsert based on the date
    playlists_collection.update_one(
        {"date": playlist_data["date"]},
        {"$set": header_data},
        upsert=True,
    )

    with open("test.json", "w", encoding="utf-8") as f:
        json.dump(header_data, f, default=convert_objectid)


def insert_or_update_tracks(playlist_data):
    operations = []
    for track in playlist_data["items"]:
        track_data = {
            "id": track["id"],
            "name": track["name"],
            "added_at": track["added_at"],
            "playcount": track["playcount"],
            "contentRating": track["contentRating"],
            "duration_ms": track["duration_ms"],
            "artists": track["artists"],
            "image": track["image"],
            "image_size": track["image_size"],
            "popularity": track["popularity"],
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





def retrieve_global_from_mongo(date):
    # Retrieve the global_collections data where the field "date" matches the input date
    gloal_data = global_collections.find({"date": date})
    global_data = list(gloal_data)[0] 
    global_data["uri"] = str(global_data["_id"])
    del global_data["_id"]

    return global_data


def retrieve_playlist_from_mongo(date):
    # Retrieve the playlists headers data where the field "date" matches the input date
    playlist_data = playlists_collection.find({"date": date})
    playlist_data = list(playlist_data)[0]
    playlist_data["uri"] = str(playlist_data["_id"])
    del playlist_data["_id"]

    return playlist_data


import datetime, json

if __name__ == "__main__":
    # DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    DATE_KEY = "2025-01-16"
    global_data = retrieve_global_from_mongo(DATE_KEY)

    add_to_database(global_data)
    print("Data added to the database.")