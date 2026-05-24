from typing import Dict, List, Optional
import datetime
import requests
import time




def fetch_track_via_isrc(
    track_id: str,
    isrc: Optional[str],
    headers: Dict[str, str],
) -> Dict:
    try:
        params = {"q": f"isrc:{isrc}", "type": "track", "limit": 10}
        response = requests.get(
            "https://api.spotify.com/v1/search", headers=headers, params=params
        )
        response.raise_for_status()
        results = response.json().get("tracks", {}).get("items", [])

        if not(results):
            # No results found, return original data
            return None

        # Find the result with the earliest release date across all matches
        best_date = None
        best_result = None

        for result in results:
            album = result.get("album", {})
            release_date = album.get("release_date", "")
            release_date_precision = album.get("release_date_precision", "")

            if release_date_precision == "month":
                release_date = release_date + "-01"
            elif release_date_precision == "year":
                release_date = release_date + "-01-01"

            try:
                release_date = datetime.date.fromisoformat(release_date)
            except ValueError:
                continue

            if ((best_date is None) or (release_date < best_date)):
                best_date = release_date
                best_result = result

        if (best_result is None):
            return None

        album = best_result.get("album", {})
        return {
            "id": best_result["id"],
            "name": best_result["name"],
            "popularity": best_result["popularity"],
            "release_date": album["release_date"],
            "release_date_precision": album["release_date_precision"],
            "isrc": isrc,
            "corrected_release_date": True,
        }

    except Exception as e:
        print(f"Error fetching ISRC {isrc} for track {track_id}: {e}")
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
    print("\n=== Starting track enrichment via ISRC search ===")

    track_ids = [track["id"] for track in playlist_items]

    already_corrected = set()
    if (tracks_collection is not None and not overwrite):
        already_corrected = get_tracks_already_corrected(track_ids, tracks_collection)

    tracks_to_enrich = [
        track for track 
        in playlist_items 
        if track["id"] not in already_corrected
    ]

    if not tracks_to_enrich:
        print("All tracks already corrected. Skipping ISRC enrichment.")
        return playlist_items

    print(f"Enriching {len(tracks_to_enrich)}/{len(playlist_items)} tracks via ISRC search...")

    track_lookup = {track["id"]: track["name"] for track in tracks_to_enrich}

    isrc_data = fetch_isrc_codes_batch(track_ids, headers)

    # enrich each track with ISRC search
    enriched_count = 0
    for i, track in enumerate(tracks_to_enrich):
        print(f"Enriching track {i+1}/{len(tracks_to_enrich)}: {track.get('name', 'Unknown')}...   ", end="\r")

        track_id = track["id"]
        track_name = track_lookup.get(track_id)

        isrc = isrc_data.get(track_id)

        # Create original track data dict (fallback)
        original_data = {
            "id": track_id,
            "name": track_name,
            "popularity": track.get("popularity"),
            "release_date": track.get("release_date"),
            "release_date_precision": track.get("release_date_precision"),
            "isrc": isrc,
        }

        corrected_data = fetch_track_via_isrc(track_id, isrc, headers)
        if (corrected_data is None):
            corrected_data = original_data
        if corrected_data.get("corrected_release_date"):
            enriched_count += 1

        track_idx = next(
            (j for j, item in enumerate(playlist_items) if item["id"] == track_id), None
        )
        if (track_idx is not None):
            playlist_items[track_idx]["popularity"] = corrected_data["popularity"]
            playlist_items[track_idx]["release_date"] = corrected_data["release_date"]
            playlist_items[track_idx]["release_date_precision"] = corrected_data["release_date_precision"]
            playlist_items[track_idx]["corrected_release_date"] = corrected_data.get("corrected_release_date", False)
            if "isrc" in corrected_data:
                playlist_items[track_idx]["isrc"] = corrected_data["isrc"]

        # Rate limiting: add small delay to avoid hitting Spotify rate limits
        if (i > 50):
            time.sleep(0.1)

    print(f"\nSuccessfully found {enriched_count} singles with correct release dates")

    return playlist_items


def fetch_isrc_codes_batch(
    track_ids: List[str], headers: Dict[str, str]
) -> Dict[str, str]:
    isrc_data = {}

    print("Fetching ISRC codes for tracks...")
    for i in range(0, len(track_ids), 50):
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
                    isrc = track.get("external_ids", {}).get("isrc")
                    if (track_id and isrc):
                        isrc_data[track_id] = isrc

        except Exception as e:
            print(f"Error fetching ISRC batch at {i}: {e}")

    print(f"Retrieved ISRC codes for {len(isrc_data)} tracks")
    return isrc_data


def fetch_artists_batch(artist_ids: List[str], headers: Dict[str, str]) -> Dict:
    artists_infos = {}

    print(f"Fetching {len(artist_ids)} artists...")
    for i in range(0, len(artist_ids), 50):
        print(f"Fetching artists {i}/{len(artist_ids)}...", end="\r")
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

    print(f"Fetching artists {len(artist_ids)}/{len(artist_ids)} done!")
    return artists_infos