from typing import Dict, List, Optional
import datetime
import requests
import time




def fetch_release_date_via_isrc(
    isrc: Optional[str],
    headers: Dict[str, str],
) -> Optional[str]:
    try:
        params = {"q": f"isrc:{isrc}", "type": "track", "limit": 10}
        response = requests.get(
            "https://api.spotify.com/v1/search", headers=headers, params=params
        )
        response.raise_for_status()
        results = response.json().get("tracks", {}).get("items", [])

        if not(results):
            print(f"No search results found for ISRC {isrc}.")
            return None

        best_date = None

        for result in results:
            album = result.get("album", {})
            release_date = album.get("release_date", "")
            release_date_precision = album.get("release_date_precision", "")

            if not(release_date):
                continue

            if release_date_precision == "month":
                release_date = release_date + "-01"
            elif release_date_precision == "year":
                release_date = release_date + "-01-01"

            try:
                release_date = datetime.date.fromisoformat(release_date)
            except ValueError:
                print(f"Result for ISRC {isrc} and track has invalid release date. Skipping.")
                continue

            if ((best_date is None) or (release_date < best_date)):
                best_date = release_date

        if (best_date is None):
            print(f"No results with valid release date found for ISRC {isrc}.")
            return None

        return best_date.isoformat()

    except Exception as e:
        print(f"Error fetching track with ISRC {isrc}: {e}")
        return None


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
    print("\n=== Starting track enrichment via API search ===")

    track_ids = [track["id"] for track in playlist_items]

    # Tracks already corrected skip the ISRC date search but still get popularity updated
    already_corrected = set()
    if (tracks_collection is not None and not overwrite):
        already_corrected = get_tracks_already_corrected(track_ids, tracks_collection)

    # fetch API data for all tracks
    print(f"Fetching API data for {len(track_ids)} tracks...")
    tracks_data = fetch_tracks_infos_batch(track_ids, headers)

    enriched_count = 0
    isrc_search_count = len(track_ids) - len(already_corrected)
    print(f"ISRC date correction needed for {isrc_search_count} tracks ({len(already_corrected)} already corrected)...")

    for i, track in enumerate(playlist_items):
        print(f"Enriching track {i+1}/{len(playlist_items)}...   ", end="\r")

        track_id = track["id"]
        api_data = tracks_data.get(track_id, {})
        isrc = api_data.get("isrc")

        playlist_items[i]["popularity"] = api_data.get("popularity")
        playlist_items[i]["release_date"] = api_data.get("release_date")
        playlist_items[i]["release_date_precision"] = api_data.get("release_date_precision")
        playlist_items[i]["corrected_release_date"] = False
        playlist_items[i]["isrc"] = isrc

        # already in DB with a corrected date: don't overwrite it
        if (track_id in already_corrected):
            playlist_items[i]["corrected_release_date"] = "already_corrected"
            continue

        # API release date is already the right one with singles
        if (api_data.get("album_type") == "single"):
            playlist_items[i]["corrected_release_date"] = True
            continue

        corrected_release_date = fetch_release_date_via_isrc(isrc, headers)
        if (corrected_release_date is None):
            print(f"No ISRC enrichment found for track ID {track_id} ({api_data.get("name")}).")

        else:
            enriched_count += 1

            # comapre old and new release dates and keep the earliest one
            old_date = playlist_items[i].get("release_date")
            old_precision = playlist_items[i].get("release_date_precision")

            if (old_date and old_precision):
                if old_precision == "month":
                    old_date = old_date + "-01"
                elif old_precision == "year":
                    old_date = old_date + "-01-01"

                old_date = datetime.date.fromisoformat(old_date)
                corrected_release_date = datetime.date.fromisoformat(corrected_release_date)

                playlist_items[i]["release_date_precision"] = "day"
                playlist_items[i]["corrected_release_date"] = True
                
                if (old_date < corrected_release_date):
                    playlist_items[i]["release_date"] = old_date.isoformat()
                else:
                    playlist_items[i]["release_date"] = corrected_release_date.isoformat()

        if (i > 50):
            time.sleep(0.1)

    print(f"\nSuccessfully found {enriched_count} singles with correct release dates")
    return playlist_items


def fetch_tracks_infos_batch(
    track_ids: List[str], headers: Dict[str, str]
) -> Dict[str, Dict]:
    track_data = {}

    for i in range(0, len(track_ids), 50):
        print(f"Fetching tracks {i}/{len(track_ids)}...   ", end="\r")
        chunk = track_ids[i : i + 50]
        params = {"ids": ",".join(chunk)}

        try:
            response = requests.get(
                "https://api.spotify.com/v1/tracks", headers=headers, params=params
            )
            response.raise_for_status()
            tracks_data = response.json().get("tracks", [])

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
            print(f"Error fetching tracks infos batch at {i}: {e}")

    isrc_count = sum(1 for v in track_data.values() if v.get("isrc"))
    print(f"Retrieved tracks infos for {isrc_count}/{len(track_data)} tracks")
    return track_data


def fetch_artists_batch(artist_ids: List[str], headers: Dict[str, str]) -> Dict:
    artists_infos = {}

    print(f"Fetching {len(artist_ids)} artists...")
    for i in range(0, len(artist_ids), 50):
        print(f"Fetching artists {i}/{len(artist_ids)}...   ", end="\r")
        batch = artist_ids[i : i + 50]
        params = {"ids": ",".join(batch)}

        try:
            response = requests.get(
                "https://api.spotify.com/v1/artists", headers=headers, params=params
            )
            response.raise_for_status()
            artists_batch = response.json()["artists"]

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
            print(f"Error fetching artist batch {i}: {e}")

    print(f"Fetching {len(artist_ids)} artists done!")
    return artists_infos