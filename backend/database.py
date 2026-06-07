from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    client.admin.command("ping")
except Exception as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}")

db = client.billions
playlists_collection = db.playlists_headers
tracks_collection = db.playlist_tracks
artists_collection = db.playlist_artists

# one-time index creation
playlists_collection.create_index("date", unique=True)
tracks_collection.create_index("id", unique=True)
artists_collection.create_index("id", unique=True)




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
        ],
    }

    if (DRY_RUN):        
        print(f"Dry run mode - not writing {len(playlist_data['items'])} tracks to the database")
    else:
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
            "contentRating": track["contentRating"],
            "duration_ms": track["duration_ms"],
            "artists": [{"id": artist["id"]} for artist in track["artists"]],
            "image": track["image"],
            "image_size": track["image_size"],
        }

        if ("isrc" in track):
            track_data["isrc"] = track["isrc"]

        correctedFlag = track.get("corrected_release_date")
        if (correctedFlag == "already_corrected"): # Date was corrected in a previous run
            continue
        elif (correctedFlag == True): # Date was corrected in this run
            set_fields = {
                "release_date": track["release_date"],
                "release_date_precision": track["release_date_precision"],
                "corrected_release_date": True,
            }
            set_on_insert_fields = {"added_at": track["added_at"]}
        else:
            set_fields = {"corrected_release_date": False}
            set_on_insert_fields = {
                "added_at": track["added_at"],
                "release_date": track["release_date"],
                "release_date_precision": track["release_date_precision"],
            }

        update = {
            "$set": set_fields,
            "$setOnInsert": track_data | set_on_insert_fields,
        }

        operations.append(UpdateOne({"id": track["id"]}, update, upsert=True))

    if (DRY_RUN):        
        print(f"Dry run mode - not writing {len(operations)} tracks to the database")
    elif operations:
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
                "image": (
                    artist.get("image").get("url") if artist.get("image") else None
                ),
                "image_size": (
                    artist.get("image").get("width") if artist.get("image") else None
                ),
            }

            operations.append(
                UpdateOne(
                    {"id": artist["id"]},
                    {"$set": artist_data},
                    upsert=True,
                )
            )

    if (DRY_RUN):
        print(f"Dry run mode - not writing {len(operations)} artists to the database")
    elif operations:
        artists_collection.bulk_write(operations)


def add_to_database(playlist_data):
    insert_or_update_tracks(playlist_data)
    print("Tracks added to the database")
    insert_or_update_artists(playlist_data)
    print("Artists added to the database")
    insert_or_update_playlist_header(playlist_data)
    print("Playlist header added to the database")


def check_playlist_header_from_mongo(date: str) -> bool:
    # check a playlists headers where the field "date" matches the input date
    return playlists_collection.count_documents({"date": date}) > 0


def retrieve_playlist_infos_from_mongo(date: str) -> dict:
    # retrieve the playlists headers data where the field "date" matches the input date
    data_count = playlists_collection.count_documents({"date": date})
    if data_count == 0:
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
        if track_id in track_details_dict:
            track.update(track_details_dict[track_id])
        del track["_id"]

    # Retrieve the artists details from the artists collection
    artist_ids = list(
        {
            artist["id"]
            for track in playlist_data["items"]
            for artist in track["artists"]
        }
    )
    artists_details = list(artists_collection.find({"id": {"$in": artist_ids}}))
    artist_details_dict = {artist["id"]: artist for artist in artists_details}

    for track in playlist_data["items"]:
        for artist in track["artists"]:
            artist_id = artist["id"]
            if artist_id in artist_details_dict:
                artist.update(artist_details_dict[artist_id])
            del artist["_id"]

    return playlist_data