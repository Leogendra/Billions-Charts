from backend.database import tracks_collection, playlists_collection, MONGO_DB_NAME, DRY_RUN
from backend.utils import create_folder
import json
import os


MISSING_TRACKS_PATH = "data/analysis/missing_tracks.json"
DUPLICATED_ISRC_PATH = "data/analysis/duplicated_isrc.json"


def get_all_tracks() -> list[dict]:
    """Every DB track, its artists resolved to their names."""
    return list(tracks_collection.aggregate([
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
            "isrc": 1,
            "added_at": 1,
            "artists": {"$map": {"input": "$artists_details", "as": "a", "in": "$$a.name"}},
        }},
    ]))


def get_latest_playlist_header() -> dict:
    header = playlists_collection.find_one({}, {"_id": 0, "date": 1, "items.id": 1}, sort=[("date", -1)])
    if (header is None):
        raise LookupError(f"No playlist header found in database {MONGO_DB_NAME!r}.")
    return header


def find_tracks_missing_from_playlist(tracks: list[dict], playlist_track_ids: set[str]) -> list[dict]:
    return [track for track in tracks if track["id"] not in playlist_track_ids]


def find_tracks_with_duplicated_isrc(tracks: list[dict]) -> list[dict]:
    tracks_by_isrc = {}
    for track in tracks:
        if track.get("isrc"):
            tracks_by_isrc.setdefault(track["isrc"], []).append(track)
    return [track for group in tracks_by_isrc.values() if len(group) > 1 for track in group]


def find_tracks_to_delete(missing_tracks: list[dict], duplicated_isrc_tracks: list[dict]) -> list[dict]:
    """Tracks absent from the latest header whose ISRC is shared with another track."""
    duplicated_isrc_ids = {track["id"] for track in duplicated_isrc_tracks}
    return [track for track in missing_tracks if track["id"] in duplicated_isrc_ids]


def sort_key(track: dict) -> tuple[str, str]:
    return (track.get("isrc") or "", (track.get("name") or "").casefold())


def save_tracks(tracks: list[dict], path: str, label: str) -> None:
    create_folder(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(tracks, key=sort_key), f, ensure_ascii=False, indent=4)
    print(f"{len(tracks)} track(s) {label}, saved to {path}")


def format_track(track: dict) -> str:
    artists = ", ".join(track.get("artists") or [])
    return f"{track['id']}  {track.get('name')} - {artists}  (isrc: {track.get('isrc')}, added_at: {track.get('added_at')})"


def delete_tracks(track_ids: list[str]) -> None:
    if (DRY_RUN):
        print(f"[Dry run] not deleting {len(track_ids)} track(s) from the database")
    else:
        result = tracks_collection.delete_many({"id": {"$in": track_ids}})
        print(f"{result.deleted_count} track(s) deleted from playlist_tracks")


def purge_duplicate_tracks(tracks_to_delete: list[dict]) -> None:
    print(f"\n{len(tracks_to_delete)} track(s) absent from the latest header and sharing their ISRC:")
    for track in sorted(tracks_to_delete, key=sort_key):
        print(f"  {format_track(track)}")
    if not(tracks_to_delete):
        return

    track_ids = [track["id"] for track in tracks_to_delete]
    headers_count = playlists_collection.count_documents({"items.id": {"$in": track_ids}})
    print(f"\nWarning: {headers_count} older playlist header(s) still reference these tracks.")
    print(f"Database: {MONGO_DB_NAME}{' (DRY_RUN: nothing will be deleted)' if DRY_RUN else ''}")
    answer = input(f"Type 'delete' to delete these {len(track_ids)} track(s) from playlist_tracks: ")
    if (answer.strip() == "delete"):
        delete_tracks(track_ids)
    else:
        print("Nothing deleted.")


def find_duplicate_tracks() -> None:
    tracks = get_all_tracks()
    header = get_latest_playlist_header()
    playlist_track_ids = {item["id"] for item in header["items"]}
    print(f"Database: {MONGO_DB_NAME}")
    print(f"{len(tracks)} track(s) in playlist_tracks, {len(playlist_track_ids)} in the playlist header of {header['date']}\n")

    missing_tracks = find_tracks_missing_from_playlist(tracks, playlist_track_ids)
    duplicated_isrc_tracks = find_tracks_with_duplicated_isrc(tracks)
    save_tracks(missing_tracks, MISSING_TRACKS_PATH, "absent from the latest header")
    save_tracks(duplicated_isrc_tracks, DUPLICATED_ISRC_PATH, "with a duplicated ISRC")

    purge_duplicate_tracks(find_tracks_to_delete(missing_tracks, duplicated_isrc_tracks))




if __name__ == "__main__":
    find_duplicate_tracks()
