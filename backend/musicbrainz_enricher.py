from typing import Dict, List, Optional, Tuple
import requests
import time

MB_BASE = "https://musicbrainz.org/ws/2"
MB_HEADERS = {
    "User-Agent": "BillionsCharts/1.3.0 ( contact@billions-charts.com )",
    "Accept": "application/json",
}
RATE_LIMIT_DELAY = 1.0




def mb_get(path: str, params: dict = {}, max_retries: int = 3) -> Optional[dict]:
    url = f"{MB_BASE}/{path}"
    params = {**params, "fmt": "json"}
    start = time.time()

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=MB_HEADERS, params=params, timeout=10)
        except Exception as e:
            print(f"  [ERROR] MB {path}: {e}")
            time.sleep(RATE_LIMIT_DELAY)
            return None

        if (response.status_code == 503):
            backoff = RATE_LIMIT_DELAY * (2 ** (attempt + 1))
            print(f"  [503] MB rate limited: retry {attempt+1}/{max_retries} in {backoff:.0f}s...")
            time.sleep(backoff)
            continue

        elapsed = time.time() - start
        time.sleep(max(0, RATE_LIMIT_DELAY - elapsed))

        if not(response.ok):
            print(f"  [HTTP {response.status_code}] MB {path}")
            return None

        return response.json()

    print(f"  [FAIL] MB {path}: too many 503s after {max_retries} attempts")
    return None


def get_language_from_releases(releases: list) -> Tuple[Optional[str], Optional[str]]:
    official = [r for r in releases if r.get("status") == "Official"]
    candidates = official if official else releases
    candidates.sort(key=lambda r: r.get("date") or "9999")
    for release in candidates:
        text_rep = release.get("text-representation", {})
        language = text_rep.get("language")
        script = text_rep.get("script")
        if language:
            return language, script
    return None, None


def fetch_track_mb_data(isrc: str) -> dict:
    data = mb_get(f"isrc/{isrc}", {"inc": "artist-credits"})
    if(not(data) or not(data.get("recordings"))):
        return {}

    recording = data["recordings"][0]
    mbid = recording.get("id")
    if not(mbid):
        return {}

    rec_detail = mb_get(f"recording/{mbid}", {"inc": "releases"})
    releases = rec_detail.get("releases", []) if rec_detail else []

    language, script = get_language_from_releases(releases)

    official = [r for r in releases if r.get("status") == "Official"] or releases
    dates = [r.get("date") for r in official if r.get("date")]

    return {
        "mb_id": mbid,
        "mb_language": language,
        "mb_script": script,
        "mb_release_date": min(dates) if dates else None,
    }


def fetch_artist_mb_data(spotify_artist_id: str) -> dict:
    data = mb_get("url/", {
        "query": f"url:https://open.spotify.com/artist/{spotify_artist_id}",
        "targettype": "artist",
    })
    if not(data and data.get("urls")):
        return {"mb_unmatched": True}

    try:
        mbid = data["urls"][0]["relation-list"][0]["relations"][0]["artist"]["id"]
    except (KeyError, IndexError):
        return {"mb_unmatched": True}

    detail = mb_get(f"artist/{mbid}", {"inc": "aliases+tags+genres+url-rels"})
    if not detail:
        return {}

    life_span = detail.get("life-span", {})
    is_ended = life_span.get("ended", False)
    artist_type = detail.get("type")

    return {
        "mb_id": mbid,
        "mb_type": artist_type,
        "mb_gender": detail.get("gender"),
        "mb_country": detail.get("country"),
        "mb_area": detail.get("area", {}).get("name") if detail.get("area") else None,
        "mb_begin_date": life_span.get("begin"),
        "mb_end_date": life_span.get("end"),
        "mb_is_ended": is_ended,
        "mb_sort_name": detail.get("sort-name"),
        "mb_disambiguation": detail.get("disambiguation"),
        "mb_genres": [g["name"] for g in detail.get("genres", [])],
    }


def fetch_artist_mb_status(mb_id: str) -> dict:
    """Fetches only life-span status for an already-matched artist."""
    detail = mb_get(f"artist/{mb_id}")
    if not detail:
        return {}

    life_span = detail.get("life-span", {})
    is_ended = life_span.get("ended", False)

    return {
        "mb_end_date": life_span.get("end"),
        "mb_is_ended": is_ended,
    }


def get_tracks_needing_mb_enrichment(track_ids: list, tracks_collection) -> set:
    try:
        already = tracks_collection.find(
            {"id": {"$in": track_ids}, "mb_id": {"$exists": True}},
            {"id": 1, "_id": 0},
        )
        return set(track_ids) - {doc["id"] for doc in already}
    except Exception as e:
        print(f"Error querying MB-enriched tracks: {e}")
        return set(track_ids)


def get_artists_needing_mb_enrichment(
    artist_ids: list,
    artists_collection,
) -> Tuple[set, Dict[str, str]]:
    """
    Returns:
    - need_full: artist IDs with no mb_id and not mb_unmatched (need name lookup)
    - status_checks: {artist_id: mb_id} for matched but still-active artists/bands
    """
    if artists_collection is None:
        return set(artist_ids), {}
    try:
        docs = list(artists_collection.find(
            {"id": {"$in": artist_ids}},
            {"id": 1, "mb_id": 1, "mb_unmatched": 1, "mb_is_ended": 1, "_id": 0},
        ))
        need_full = set(artist_ids)
        status_checks: Dict[str, str] = {}

        for doc in docs:
            artistId = doc["id"]
            mb_id = doc.get("mb_id")
            if (doc.get("mb_unmatched") or mb_id):
                need_full.discard(artistId)
            if mb_id:
                is_ended = doc.get("mb_is_ended")
                if not(is_ended):
                    status_checks[artistId] = mb_id

        return need_full, status_checks
    except Exception as e:
        print(f"Error querying MB-enriched artists: {e}")
        return set(artist_ids), {}


def enrich_tracks_with_musicbrainz(
    playlist_items: List[Dict],
    tracks_collection=None,
) -> List[Dict]:
    print("\n=== Starting track enrichment via MusicBrainz ===")

    track_ids = [track["id"] for track in playlist_items]
    needs_enrichment = get_tracks_needing_mb_enrichment(track_ids, tracks_collection)
    to_enrich = [track for track in playlist_items if ((track["id"] in needs_enrichment) and track.get("isrc"))]

    skipped = len(track_ids) - len(needs_enrichment)
    print(f"{len(to_enrich)} MB track needing lookups ({skipped} already enriched, {len(needs_enrichment) - len(to_enrich)} missing ISRC).")

    id_to_index = {t["id"]: i for i, t in enumerate(playlist_items)}
    enriched_count = 0
    startTime = time.time()

    # lookups for tracks with ISRCs
    for count, track in enumerate(to_enrich, 1):
        print(f"  MB track lookup {count}/{len(to_enrich)} ({time.time() - startTime:.1f}s)...   ", end="\r")
        mb_data = fetch_track_mb_data(track["isrc"])
        if mb_data.get("mb_id"):
            playlist_items[id_to_index[track["id"]]].update(mb_data)
            enriched_count += 1

    print(f"\nMB track enrichment done: {enriched_count}/{len(to_enrich)} matched")
    return playlist_items


def enrich_artists_with_musicbrainz(
    playlist_items: List[Dict],
    artists_collection=None,
) -> List[Dict]:
    print("\n=== Starting artist enrichment via MusicBrainz ===")

    artist_map: Dict[str, dict] = {}
    for track in playlist_items:
        for artist in track["artists"]:
            artistId = artist["id"]
            if (artistId not in artist_map):
                artist_map[artistId] = artist

    artist_ids = list(artist_map.keys())
    need_full, status_checks = get_artists_needing_mb_enrichment(artist_ids, artists_collection)

    # print(f"MB artist lookups needed: {len(need_full)} full, {len(status_checks)} status updates") # off for now
    print(f"MB artist lookups needed: {len(need_full)} full.")

    mb_results: Dict[str, dict] = {}
    startTime = time.time()

    # full lookup in musicbrainz
    for count, artistId in enumerate(need_full):
        print(f"  MB artist full lookup {count+1}/{len(need_full)} ({time.time() - startTime:.1f}s)...   ", end="\r")
        mb_data = fetch_artist_mb_data(artistId)
        if mb_data:
            mb_results[artistId] = mb_data

    # status lookup for currently active
    if False: # TODO: off for now since many artists are still active. Search for heuristics to avoid redundant lookups.
        for count, (artistId, mb_id) in enumerate(status_checks.items()):
            print(f"  MB artist status check {count+1}/{len(status_checks)} ({time.time() - startTime:.1f}s)...   ", end="\r")
            status = fetch_artist_mb_status(mb_id)
            if status.get("mb_is_ended"):
                mb_results[artistId] = status

    # merge results
    for i, track in enumerate(playlist_items):
        for j, artist in enumerate(track["artists"]):
            artistId = artist["id"]
            if (artistId in mb_results):
                playlist_items[i]["artists"][j].update(mb_results[artistId])

    nbFullMatched = sum(1 for v in mb_results.values() if ((v.get("mb_id") and not v.get("mb_unmatched"))))
    print(f"\nMB artist enrichment done: {nbFullMatched}/{len(need_full)} matched")
    return playlist_items


if __name__ == "__main__":
    import json

    """
    test_isrc = "QM4TX1817912"  # Fake love - BTS
    track_data = fetch_track_mb_data(test_isrc)
    # print(f"Track data for ISRC {test_isrc}: {track_data}")
    with open("test_track_mb_data.json", "w", encoding="utf-8") as f:
        json.dump(track_data, f, indent=4, ensure_ascii=False)
    """
    
    # artist_id = "4GJ6xDCF5jaUqD6avOuQT6" # fifty fifty
    artist_id = "5YBSzuCs7WaFKNr7Bky0Uf" # Olivia (pas rodrigo)
    artist_data = fetch_artist_mb_data(artist_id)
    with open("test_artist_mb_data.json", "w", encoding="utf-8") as f:
        json.dump(artist_data, f, indent=4, ensure_ascii=False)