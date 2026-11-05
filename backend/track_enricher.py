from backend.utils import is_uncertain_date, is_new_date_preferred, infer_precision_from_date_string
from backend.database import retrieve_corrected_track_ids, retrieve_stored_isrcs, retrieve_manual_release_dates
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional
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
    """Returns (None, None) when no match is found. Raises when the request fails after retries."""
    def fetch_isrc():
        params = {"q": f"isrc:{isrc}", "type": "track", "limit": 10}
        response = requests.get(
            "https://api.spotify.com/v1/search", headers=headers, params=params, timeout=10
        )
        response.raise_for_status()
        return response.json().get("tracks", {}).get("items", [])

    results = request_with_retry(fetch_isrc)

    if not results:
        print(f"No search results found for ISRC {isrc}.")
        return None, None

    best_date_str = None
    best_precision = None

    for result in results:
        album = result.get("album", {})
        release_date = album.get("release_date", "")
        precision = album.get("release_date_precision", "")

        if not(release_date) or not(precision):
            continue

        if (best_date_str is None) or is_new_date_preferred(best_date_str, release_date):
            best_date_str = release_date
            best_precision = precision

    if best_date_str is None:
        print(f"No results with valid release date found for ISRC {isrc}.")
        return None, None

    return best_date_str, best_precision


def get_manual_release_dates(track_ids: List[str]) -> Dict[str, tuple[str, str]]:
    """{id: (date, precision)} for dates fixed by hand. Raises on error: an empty result would let a /search/ overwrite them."""
    try:
        docs = retrieve_manual_release_dates(track_ids)
        return {
            doc["id"]: (
                doc["manual_release_date"],
                doc.get("manual_release_date_precision") or infer_precision_from_date_string(doc["manual_release_date"]),
            )
            for doc in docs
        }
    except Exception as e:
        raise RuntimeError(f"Error querying manual release dates: {e}")


def enrich_tracks_with_correct_release_dates(
    playlist_items: List[Dict],
    headers: Dict[str, str],
    overwrite: bool = False,
) -> List[Dict]:
    print("\n=== Starting track enrichment via Spotify API search ===")

    track_ids = [track["id"] for track in playlist_items]

    # fetch API data for all tracks
    print(f"Fetching API data for {len(track_ids)} tracks...")
    tracks_data = fetch_tracks_infos_batch(track_ids, headers)

    # Tracks already corrected skip the ISRC date search but still get popularity updated
    already_corrected = set()
    if not(overwrite):
        already_corrected = retrieve_corrected_track_ids(track_ids)

    stored_isrcs = retrieve_stored_isrcs(track_ids)
    manual_dates = get_manual_release_dates(track_ids)

    # apply batch API data to all tracks
    for i, track in enumerate(playlist_items):
        track_id = track["id"]
        api_data = tracks_data[track_id]
        isrc = stored_isrcs.get(track_id) or api_data.get("isrc") # use stored ISRC first

        playlist_items[i]["popularity"] = api_data.get("popularity")
        playlist_items[i]["release_date"] = api_data.get("release_date")
        playlist_items[i]["release_date_precision"] = api_data.get("release_date_precision")
        playlist_items[i]["corrected_release_date"] = False
        playlist_items[i]["isrc"] = isrc

        # a manual date always wins
        if (track_id in manual_dates):
            manual_date, manual_precision = manual_dates[track_id]
            playlist_items[i]["release_date"] = manual_date
            playlist_items[i]["release_date_precision"] = manual_precision
            playlist_items[i]["manual_release_date"] = manual_date
            playlist_items[i]["corrected_release_date"] = True
        elif (track_id in already_corrected):
            playlist_items[i]["corrected_release_date"] = "already_corrected"
        # # cannot be trusted anymore since Spotify sometimes returns wrong release dates for singles
        # elif ((api_data.get("album_type") == "single") and isrc): 
        #     playlist_items[i]["corrected_release_date"] = True

    # parallel ISRC lookups for tracks that still need date correction
    to_lookup = [
        (i, playlist_items[i]["isrc"])
        for i in range(len(playlist_items))
        if (playlist_items[i]["corrected_release_date"] is False) and playlist_items[i]["isrc"]
    ]
    
    isrc_search_count = len(to_lookup)
    if (isrc_search_count > 0):
        print(f"ISRC date correction needed for {isrc_search_count} tracks.")

    def isrc_lookup_process(idx, isrc):
        date_str, precision = fetch_release_date_via_isrc(isrc, headers)
        return idx, date_str, precision

    enriched_count = 0
    error_count = 0
    completed = 0
    nb_workers = 3 # 5 workers yield 429 errors
    with ThreadPoolExecutor(max_workers=nb_workers) as executor:
        futures = {executor.submit(isrc_lookup_process, idx, isrc): idx for idx, isrc in to_lookup}
        for future in as_completed(futures):
            completed += 1
            print(f"ISRC lookup {completed}/{len(to_lookup)}...   ", end="\r")
            try:
                idx, isrc_date, isrc_precision = future.result()
            except Exception as e:
                # the track keeps corrected_release_date=False, so the next run retries it
                error_count += 1
                print(f"Error fetching release date for track ID {playlist_items[futures[future]]['id']}: {e}")
                continue

            if (isrc_date is None):
                print(f"No ISRC enrichment found for track ID {playlist_items[idx]['id']}.")
                continue

            old_date_str = playlist_items[idx].get("release_date")
            old_precision = playlist_items[idx].get("release_date_precision")

            if (old_date_str and old_precision):
                enriched_count += 1

                if is_new_date_preferred(old_date_str, isrc_date):
                    playlist_items[idx]["release_date"] = isrc_date
                    playlist_items[idx]["release_date_precision"] = isrc_precision
                    playlist_items[idx]["corrected_release_date"] = not(is_uncertain_date(isrc_date))
                else:
                    playlist_items[idx]["corrected_release_date"] = True

    if (enriched_count > 0):
        print(f"\nSuccessfully found {enriched_count} singles with correct release dates")

    if (error_count > 0):
        print(f"\nWARNING: {error_count}/{isrc_search_count} ISRC lookups failed.")

    for i in range(len(playlist_items)):
        track = playlist_items[i]
        if (track.get("corrected_release_date") != "already_corrected"
                and not(track.get("manual_release_date"))
                and is_uncertain_date(track.get("release_date"))):
            playlist_items[i]["release_date_uncertain"] = True

    return playlist_items


def fetch_spotify_batches(
    url: str,
    response_key: str,
    ids: List[str],
    headers: Dict[str, str],
    parse_item: Callable[[Dict], Dict],
    label: str,
) -> Dict[str, Dict]:
    """Fetches ids by chunks of 50, keyed by Spotify id"""
    items_infos = {}
    error_count = 0
    total_batches = 0

    for i in range(0, len(ids), 50):
        print(f"Fetching {label}s {i}/{len(ids)}...   ", end="\r")
        chunk = ids[i : i + 50]
        params = {"ids": ",".join(chunk)}
        total_batches += 1

        try:
            def fetch_chunk():
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response.json().get(response_key, [])

            # An item without id raises KeyError: the whole chunk counts as failed
            for item in request_with_retry(fetch_chunk):
                if item:
                    items_infos[item["id"]] = parse_item(item)

        except Exception as e:
            error_count += 1
            print(f"Error fetching {label} batch at {i}: {e}")

    if (error_count > 0):
        print(f"WARNING: {error_count}/{total_batches} {label} batches failed.")

    # An item without API data would be persisted incomplete: abort, the next /search/ retries
    missing_ids = [item_id for item_id in ids if (item_id not in items_infos)]
    if missing_ids:
        raise RuntimeError(
            f"Spotify returned no data for {len(missing_ids)}/{len(ids)} {label}s "
            f"(first ones: {', '.join(missing_ids[:10])}). Aborting pipeline."
        )

    return items_infos


def parse_track_infos(track: Dict) -> Dict:
    album = track.get("album", {})
    return {
        "isrc": track.get("external_ids", {}).get("isrc"),
        "name": track.get("name"),
        "popularity": track.get("popularity"),
        "album_type": album.get("album_type"),
        "release_date": album.get("release_date"),
        "release_date_precision": album.get("release_date_precision"),
    }


def parse_artist_infos(artist: Dict) -> Dict:
    return {
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


def fetch_tracks_infos_batch(
    track_ids: List[str], headers: Dict[str, str]
) -> Dict[str, Dict]:
    track_data = fetch_spotify_batches(
        "https://api.spotify.com/v1/tracks", "tracks", track_ids, headers, parse_track_infos, "track",
    )

    isrc_count = sum(1 for v in track_data.values() if v.get("isrc"))
    print(f"Retrieved tracks infos for {isrc_count}/{len(track_data)} tracks")
    return track_data


def fetch_artists_batch(artist_ids: List[str], headers: Dict[str, str]) -> Dict:
    print(f"Fetching {len(artist_ids)} artists...")
    artists_infos = fetch_spotify_batches(
        "https://api.spotify.com/v1/artists", "artists", artist_ids, headers, parse_artist_infos, "artist",
    )

    print(f"Fetching {len(artist_ids)} artists done!")
    return artists_infos