from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")
if not MONGO_DB_NAME:
    raise RuntimeError("MONGO_DB_NAME environment variable is not set")
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    client.admin.command("ping")
except Exception as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}")

db = client[MONGO_DB_NAME]
playlists_collection = db.playlists_headers
tracks_collection = db.playlist_tracks
artists_collection = db.playlist_artists

# one-time index creation
playlists_collection.create_index("date", unique=True)
tracks_collection.create_index("id", unique=True)
artists_collection.create_index("id", unique=True)

MB_TRACK_FIELDS = ["mb_id", "mb_language", "mb_script", "mb_release_date", "mb_unmatched"]
MB_ARTIST_FIELDS = ["mb_id", "mb_type", "mb_gender", "mb_country", "mb_area", "mb_begin_date", "mb_end_date", "mb_is_ended", "mb_sort_name", "mb_disambiguation", "mb_genres"] + ["mb_name_matched", "mb_unmatched"]



def extract_mb_fields(entity: dict, mb_fields: list) -> dict:
    return {k: entity[k] for k in mb_fields if (k in entity)}


def write_mb_checkpoint(collection, operations: list, label: str):
    if (DRY_RUN):
        print(f"\n[Dry run] not writing MB checkpoint for {len(operations)} {label}")
    elif operations:
        collection.bulk_write(operations, ordered=False)


def save_tracks_mb_checkpoint(tracks: list):
    """Persists only the MB fields of tracks already in the database. No upsert on purpose: a track created here would skip its $setOnInsert fields (name, image, dates...) at the final save, so new tracks wait in memory for that final save."""
    operations = []
    for track in tracks:
        mb_data = extract_mb_fields(track, MB_TRACK_FIELDS)
        if mb_data:
            operations.append(UpdateOne({"id": track["id"]}, {"$set": mb_data}))
    write_mb_checkpoint(tracks_collection, operations, "tracks")


def save_artists_mb_checkpoint(artists: list):
    """Persists only the MB fields of artists. Upsert is safe here: every non-MB artist field is $set (not $setOnInsert) by the final save."""
    operations = []
    for artist in artists:
        mb_data = extract_mb_fields(artist, MB_ARTIST_FIELDS)
        if mb_data:
            operations.append(UpdateOne({"id": artist["id"]}, {"$set": mb_data}, upsert=True))
    write_mb_checkpoint(artists_collection, operations, "artists")


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
        "items": [
            {
                "id": track["id"],
                "playcount": track["playcount"],
                "popularity": track["popularity"],
            }
            for track in playlist_data["items"]
        ],
        "artists": [
            {
                "id": artist["id"],
                "followers": artist.get("followers", -1),
                "popularity": artist.get("popularity", -1),
            }
            for artist in playlist_data["artists"].values()
        ],
    }

    if (DRY_RUN):        
        print(f"[Dry run] not writing {len(playlist_data['items'])} tracks to the database")
    else:
        playlists_collection.update_one(
            {"date": playlist_data["date"]},
            {"$set": header_data},
            upsert=True,
        )
        print("   Playlist header added to the database")


def insert_or_update_tracks(playlist_data):
    operations = []
    for track in playlist_data["items"]:
        track_fixed_data = {
            "id": track["id"],
            "name": track["name"],
            "contentRating": track["contentRating"],
            "duration_ms": track["duration_ms"],
            "artists": [{"id": aid} for aid in track["artists"]],
            "image": track["image"],
            "image_size": track["image_size"],
            "added_at": track["added_at"],
        }

        if ("isrc" in track):
            track_fixed_data["isrc"] = track["isrc"]

        set_fields = {}
        corrected_dates_fields = {}

        correctedFlag = track.get("corrected_release_date")
        if (correctedFlag == "already_corrected"): # Date was corrected in a previous run
            pass
        elif (correctedFlag == True): # Date was corrected in this run
            set_fields = {
                "release_date": track["release_date"],
                "release_date_precision": track["release_date_precision"],
                "corrected_release_date": True,
            }
        else: # Date was never corrected, set it only on insert
            set_fields = {"corrected_release_date": False}
            corrected_dates_fields = {
                "release_date": track["release_date"],
                "release_date_precision": track["release_date_precision"],
            }

        mb_data = extract_mb_fields(track, MB_TRACK_FIELDS)
        set_fields.update(mb_data)

        update = {
            "$set": set_fields,
            "$setOnInsert": track_fixed_data | corrected_dates_fields,
        }

        operations.append(UpdateOne({"id": track["id"]}, update, upsert=True))

    if (DRY_RUN):        
        print(f"[Dry run] not writing {len(operations)} tracks to the database")
    elif operations:
        tracks_collection.bulk_write(operations)
        print("   Tracks added to the database")


def insert_or_update_artists(playlist_data):
    operations = []
    for artist_id, artist in playlist_data["artists"].items():
        artist_fixed_data = {"id": artist_id}
        img = artist.get("image")
        set_fields = {
            "name": artist.get("name", "Unknown"),
            "genres": artist.get("genres", []),
            "followers": artist.get("followers", -1),
            "popularity": artist.get("popularity", -1),
            "image": img.get("url") if img else None,
            "image_size": img.get("width") if img else None,
        }

        mb_data = extract_mb_fields(artist, MB_ARTIST_FIELDS)
        set_fields.update(mb_data)
        update = {
            "$set": set_fields,
            "$setOnInsert": artist_fixed_data
        }

        operations.append(UpdateOne({"id": artist["id"]}, update, upsert=True))

    if (DRY_RUN):
        print(f"[Dry run] not writing {len(operations)} artists to the database")
    elif operations:
        artists_collection.bulk_write(operations)
        print("   Artists added to the database")


def add_to_database(playlist_data):
    insert_or_update_tracks(playlist_data)
    insert_or_update_artists(playlist_data)
    insert_or_update_playlist_header(playlist_data)


def retrieve_track_by_id(track_id: str) -> dict | None:
    track = tracks_collection.find_one({"id": track_id})
    if track is None:
        return None
    del track["_id"]

    artist_ids = [a["id"] for a in track.get("artists", [])]
    if artist_ids:
        artists_docs = list(artists_collection.find({"id": {"$in": artist_ids}}))
        artist_map = {a["id"]: a for a in artists_docs}
        for artist in track["artists"]:
            doc = artist_map.get(artist["id"], {})
            artist.update(doc)
            artist.pop("_id", None)

    latest_header = playlists_collection.find_one(
        {},
        sort=[("date", -1)],
        projection={"items": 1, "_id": 0},
    )
    if latest_header:
        for item in latest_header.get("items", []):
            if item["id"] == track_id:
                track["playcount"] = item["playcount"]
                track["popularity"] = item["popularity"]
                break

    return track


def retrieve_artist_by_id(artist_id: str) -> dict | None:
    artist = artists_collection.find_one({"id": artist_id})
    if artist is None:
        return None
    artist.pop("_id", None)

    tracks = list(tracks_collection.find(
        {"artists.id": artist_id},
        projection={"id": 1, "name": 1, "image": 1, "duration_ms": 1, "_id": 0},
    ))

    latest_header = playlists_collection.find_one(
        {},
        sort=[("date", -1)],
        projection={"items": 1, "_id": 0},
    )
    playcount_map = {}
    if latest_header:
        for item in latest_header.get("items", []):
            playcount_map[item["id"]] = item["playcount"]

    for track in tracks:
        track["playcount"] = playcount_map.get(track["id"], 0)

    tracks.sort(key=lambda t: t["playcount"], reverse=True)

    artist["track_count"] = len(tracks)
    artist["total_playcount"] = sum(t["playcount"] for t in tracks)
    artist["total_duration_ms"] = sum(t.get("duration_ms", 0) for t in tracks)
    artist["tracks"] = tracks

    return artist


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
    for artist in artists_details:
        artist.pop("_id", None)
    artists_dict = {artist["id"]: artist for artist in artists_details}

    playlist_data["artists"] = artists_dict
    for track in playlist_data["items"]:
        track["artists"] = [a["id"] for a in track["artists"]]

    return playlist_data


def retrieve_search_ids():
    tracks = list(tracks_collection.aggregate([
        {"$lookup": {
            "from": "playlist_artists",
            "localField": "artists.id",
            "foreignField": "id",
            "as": "artists_details",
        }},
        {"$project": {
            "_id": 0,
            "id": 1,
            "name": 1,
            "artists": {"$map": {"input": "$artists_details", "as": "a", "in": "$$a.name"}},
        }},
    ]))
    artists = list(artists_collection.find({}, {"_id": 0, "id": 1, "name": 1}))
    
    return {"tracks": tracks, "artists": artists}




# TESTS
def clone_database_for_testing():
    BATCH_SIZE = 1000
    source_name = MONGO_DB_NAME
    target_name = f"{MONGO_DB_NAME}_test"

    print(f"Cloning database '{source_name}' into '{target_name}'.")
    input("Press Enter to confirm...")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    source = client[source_name]
    target = client[target_name]

    for name in source.list_collection_names():
        if name.startswith("system."):
            continue

        # delete all documents in the collection
        target[name].delete_many({})

        batch = []
        count = 0
        for doc in source[name].find():
            batch.append(doc)
            if len(batch) >= BATCH_SIZE:
                target[name].insert_many(batch)
                count += len(batch)
                batch = []
        if batch:
            target[name].insert_many(batch)
            count += len(batch)

        for index in source[name].list_indexes():
            if index["name"] == "_id_":
                continue
            options = {k: v for k, v in index.items() if k in ("unique", "sparse", "expireAfterSeconds")}
            target[name].create_index(list(index["key"].items()), name=index["name"], **options)

        print(f"{name}: {count} docs copied")
    
    print(f"Clone complete. Use MONGO_DB_NAME={target_name} to run against the clone.")