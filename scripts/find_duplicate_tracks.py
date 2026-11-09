from backend.database import get_tracks_collection, get_playlists_collection, MONGO_DB_NAME, DRY_RUN
from backend.utils import create_folder
import argparse
import json
import os


MISSING_TRACKS_PATH = "data/analysis/missing_tracks.json"
DUPLICATED_ISRC_PATH = "data/analysis/duplicated_isrc.json"
REFERENCING_HEADERS_PATH = "data/analysis/headers_referencing_duplicates.json"


def get_all_tracks() -> list[dict]:
    """Every DB track, its artists resolved to their names."""
    return list(get_tracks_collection().aggregate([
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
    header = get_playlists_collection().find_one({}, {"_id": 0, "date": 1, "items.id": 1}, sort=[("date", -1)])
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


def save_referencing_headers(tracks: list[dict], path: str) -> int:
    """Headers still referencing the given tracks, keyed by date, with the tracks each one references."""
    tracks_by_id = {track["id"]: track for track in tracks}
    headers = get_playlists_collection().find({"items.id": {"$in": list(tracks_by_id)}}, {"_id": 0, "date": 1, "items.id": 1}).sort("date", -1)
    referencing_headers = {}
    for header in headers:
        referenced_tracks = [tracks_by_id[item["id"]] for item in header["items"] if item["id"] in tracks_by_id]
        referencing_headers[header["date"]] = {"count": len(referenced_tracks), "tracks": sorted(referenced_tracks, key=sort_key)}
    create_folder(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(referencing_headers, f, ensure_ascii=False, indent=4)
    return len(referencing_headers)


def format_track(track: dict) -> str:
    artists = ", ".join(track.get("artists") or [])
    return f"{track['id']}  {track.get('name')} - {artists}  (isrc: {track.get('isrc')}, added_at: {track.get('added_at')})"


def delete_tracks(track_ids: list[str]) -> None:
    if (DRY_RUN):
        print(f"[Dry run] not deleting {len(track_ids)} track(s) from the database")
    else:
        result = get_tracks_collection().delete_many({"id": {"$in": track_ids}})
        print(f"{result.deleted_count} track(s) deleted from playlist_tracks")


def purge_tracks(tracks_to_delete: list[dict], label: str) -> None:
    if not tracks_to_delete:
        print(f"0 track {label}.")
        return
    print(f"\n{len(tracks_to_delete)} track(s) {label}:")
    for track in sorted(tracks_to_delete, key=sort_key):
        print(f"  {format_track(track)}")
    if not(tracks_to_delete):
        return

    track_ids = [track["id"] for track in tracks_to_delete]
    header_count = save_referencing_headers(tracks_to_delete, REFERENCING_HEADERS_PATH)
    print(f"\nWarning: {header_count} older playlist header(s) still reference these tracks, saved to {REFERENCING_HEADERS_PATH}")
    print(f"Database: {MONGO_DB_NAME}{' (DRY_RUN: nothing will be deleted)' if DRY_RUN else ''}")
    answer = input(f"Type 'delete' to delete these {len(track_ids)} track(s) from playlist_tracks: ")
    if (answer.strip() == "delete"):
        delete_tracks(track_ids)
    else:
        print("Nothing deleted.")


def find_duplicate_tracks(force: bool) -> None:
    tracks = get_all_tracks()
    header = get_latest_playlist_header()
    playlist_track_ids = {item["id"] for item in header["items"]}
    print(f"Database: {MONGO_DB_NAME}")
    print(f"{len(tracks)} track(s) in playlist_tracks, {len(playlist_track_ids)} in the playlist header of {header['date']}\n")

    missing_tracks = find_tracks_missing_from_playlist(tracks, playlist_track_ids)
    duplicated_isrc_tracks = find_tracks_with_duplicated_isrc(tracks)
    save_tracks(missing_tracks, MISSING_TRACKS_PATH, "absent from the latest header (use --force to purge them all)")
    save_tracks(duplicated_isrc_tracks, DUPLICATED_ISRC_PATH, "with a duplicated ISRC")

    if (force):
        purge_tracks(missing_tracks, "absent from the latest header")
    else:
        purge_tracks(find_tracks_to_delete(missing_tracks, duplicated_isrc_tracks), "absent from the latest header and sharing their ISRC")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and purge tracks absent from the latest playlist header.")
    parser.add_argument("--force", action="store_true", help="purge every track absent from the latest header, not only those sharing their ISRC")
    find_duplicate_tracks(parser.parse_args().force)
