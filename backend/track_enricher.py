from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.utils import normalize_date_for_comparison
from typing import Dict, List, Optional
import datetime
import requests
import time




def request_with_retry(func, max_attempts: int = 3):
    """Calls fn() up to max_attempts times with exponential backoff (1s, 2s, 4s, ...)."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt + 1 == max_attempts:
                raise
            delay = 2 ** attempt
            print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)


def fetch_release_date_via_isrc(
    isrc: Optional[str],
    headers: Dict[str, str],
) -> tuple[Optional[str], Optional[str]]:
    try:
        def fetch_isrc():
            params = {"q": f"isrc:{isrc}", "type": "track", "limit": 10}
            response = requests.get(
                "https://api.spotify.com/v1/search", headers=headers, params=params
            )
            response.raise_for_status()
            return response.json().get("tracks", {}).get("items", [])

        results = request_with_retry(fetch_isrc)

        if not results:
            print(f"No search results found for ISRC {isrc}.")
            return None, None

        best_date_obj = None
        best_date_str = None
        best_precision = None

        for result in results:
            album = result.get("album", {})
            release_date = album.get("release_date", "")
            precision = album.get("release_date_precision", "")

            if not release_date:
                continue

            normalized = normalize_date_for_comparison(release_date, precision)

            try:
                date_obj = datetime.date.fromisoformat(normalized)
            except ValueError:
                print(f"Result for ISRC {isrc} has invalid release date. Skipping.")
                continue

            if ((best_date_obj is None) or (date_obj < best_date_obj)):
                best_date_obj = date_obj
                best_date_str = release_date
                best_precision = precision

        if best_date_str is None:
            print(f"No results with valid release date found for ISRC {isrc}.")
            return None, None

        return best_date_str, best_precision

    except Exception as e:
        print(f"Error fetching track with ISRC {isrc}: {e}")
        return None, None


def get_tracks_already_corrected(track_ids: List[str], tracks_collection) -> set:
    try:
        already_corrected = tracks_collection.find(
            {"id": {"$in": track_ids}, "corrected_release_date": True}
        )
        return {doc["id"] for doc in already_corrected}
    except Exception as e:
        print(f"Error querying corrected tracks: {e}")
        return set()


def enrich_tracks_with_correct_release_dates(
    playlist_items: List[Dict],
    headers: Dict[str, str],
    tracks_collection=None,
    overwrite: bool = False,
) -> List[Dict]:
    print("\n=== Starting track enrichment via Spotify API search ===")

    track_ids = [track["id"] for track in playlist_items]

    # Tracks already corrected skip the ISRC date search but still get popularity updated
    already_corrected = set()
    if ((tracks_collection is not None) and (not overwrite)):
        already_corrected = get_tracks_already_corrected(track_ids, tracks_collection)

    # fetch API data for all tracks
    print(f"Fetching API data for {len(track_ids)} tracks...")
    tracks_data = fetch_tracks_infos_batch(track_ids, headers)

    isrc_search_count = len(track_ids) - len(already_corrected)
    print(f"ISRC date correction needed for {isrc_search_count} tracks ({len(already_corrected)} already corrected)...")

    # apply batch API data to all tracks
    for i, track in enumerate(playlist_items):
        track_id = track["id"]
        api_data = tracks_data.get(track_id, {})
        isrc = api_data.get("isrc")

        playlist_items[i]["popularity"] = api_data.get("popularity")
        playlist_items[i]["release_date"] = api_data.get("release_date")
        playlist_items[i]["release_date_precision"] = api_data.get("release_date_precision")
        playlist_items[i]["corrected_release_date"] = False
        playlist_items[i]["isrc"] = isrc

        if (track_id in already_corrected):
            playlist_items[i]["corrected_release_date"] = "already_corrected"
        elif (api_data.get("album_type") == "single" and isrc):
            playlist_items[i]["corrected_release_date"] = True

    # parallel ISRC lookups for tracks that still need date correction
    to_lookup = [
        (i, playlist_items[i]["isrc"], tracks_data.get(playlist_items[i]["id"], {}).get("name"))
        for i in range(len(playlist_items))
        if playlist_items[i]["corrected_release_date"] is False
    ]

    def isrc_lookup(idx, isrc, name):
        date_str, precision = fetch_release_date_via_isrc(isrc, headers)
        return idx, name, date_str, precision

    enriched_count = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(isrc_lookup, idx, isrc, name): idx for idx, isrc, name in to_lookup}
        for future in as_completed(futures):
            completed += 1
            print(f"ISRC lookup {completed}/{len(to_lookup)}...   ", end="\r")
            idx, name, isrc_date, isrc_precision = future.result()

            if isrc_date is None:
                print(f"No ISRC enrichment found for track ID {playlist_items[idx]['id']} ({name}).")
                continue

            old_date_str = playlist_items[idx].get("release_date")
            old_precision = playlist_items[idx].get("release_date_precision")

            if old_date_str and old_precision:
                old_date_obj = datetime.date.fromisoformat(normalize_date_for_comparison(old_date_str, old_precision))
                isrc_date_obj = datetime.date.fromisoformat(normalize_date_for_comparison(isrc_date, isrc_precision))

                playlist_items[idx]["corrected_release_date"] = True
                enriched_count += 1

                if isrc_date_obj < old_date_obj:
                    # ISRC found a genuinely earlier date — store with its actual precision
                    playlist_items[idx]["release_date"] = isrc_date
                    playlist_items[idx]["release_date_precision"] = isrc_precision
                # else: original is earlier — keep original date and precision unchanged

    print(f"\nSuccessfully found {enriched_count} singles with correct release dates")
    return playlist_items


def fetch_tracks_infos_batch(
    track_ids: List[str], headers: Dict[str, str]
) -> Dict[str, Dict]:
    track_data = {}
    error_count = 0
    total_batches = 0

    for i in range(0, len(track_ids), 50):
        print(f"Fetching tracks {i}/{len(track_ids)}...   ", end="\r")
        chunk = track_ids[i : i + 50]
        params = {"ids": ",".join(chunk)}
        total_batches += 1

        try:
            def fetch_tracks():
                response = requests.get(
                    "https://api.spotify.com/v1/tracks", headers=headers, params=params
                )
                response.raise_for_status()
                return response.json().get("tracks", [])

            tracks_data = request_with_retry(fetch_tracks)

            for track in tracks_data:
                if track:
                    track_id = track.get("id")
                    if not(track_id):
                        continue

                    album = track.get("album", {})
                    track_data[track_id] = {
                        "isrc": track.get("external_ids", {}).get("isrc"),
                        "name": track.get("name"),
                        "popularity": track.get("popularity"),
                        "album_type": album.get("album_type"),
                        "release_date": album.get("release_date"),
                        "release_date_precision": album.get("release_date_precision"),
                    }

        except Exception as e:
            error_count += 1
            print(f"Error fetching tracks infos batch at {i}: {e}")

    if (error_count > 0):
        print(f"WARNING: {error_count}/{total_batches} track batches failed.")
        if (error_count > (total_batches / 2)):
            raise RuntimeError(
                f"Majority of track batches failed ({error_count}/{total_batches}). Aborting pipeline."
            )

    isrc_count = sum(1 for v in track_data.values() if v.get("isrc"))
    print(f"Retrieved tracks infos for {isrc_count}/{len(track_data)} tracks")
    return track_data


def fetch_artists_batch(artist_ids: List[str], headers: Dict[str, str]) -> Dict:
    artists_infos = {}
    error_count = 0
    total_batches = 0

    print(f"Fetching {len(artist_ids)} artists...")
    for i in range(0, len(artist_ids), 50):
        print(f"Fetching artists {i}/{len(artist_ids)}...   ", end="\r")
        batch = artist_ids[i : i + 50]
        params = {"ids": ",".join(batch)}
        total_batches += 1

        try:
            def fetch_artists():
                response = requests.get(
                    "https://api.spotify.com/v1/artists", headers=headers, params=params
                )
                response.raise_for_status()
                return response.json()["artists"]

            artists_batch = request_with_retry(fetch_artists)

            for artist in artists_batch:
                if artist:
                    artists_infos[artist["id"]] = {
                        "id": artist["id"],
                        "name": artist["name"],
                        "genres": artist["genres"],
                        "followers": artist["followers"]["total"],
                        "popularity": artist["popularity"],
                        "image": (
                            max(artist["images"], key=lambda x: x["width"])
                            if artist["images"]
                            else None
                        ),
                    }

        except Exception as e:
            error_count += 1
            print(f"Error fetching artist batch {i}: {e}")

    if (error_count > 0):
        print(f"WARNING: {error_count}/{total_batches} artist batches failed.")
        if (error_count > (total_batches / 2)):
            raise RuntimeError(
                f"Majority of artist batches failed ({error_count}/{total_batches}). Aborting pipeline."
            )

    print(f"Fetching {len(artist_ids)} artists done!")
    return artists_infos