from typing import Dict, List, Optional, Tuple
import requests
import time
import json # debug

MB_BASE = "https://musicbrainz.org/ws/2"
MB_HEADERS = {
    "User-Agent": "BillionsCharts/1.3.0 ( contact@billions-charts.com )",
    "Accept": "application/json",
}
RATE_LIMIT_DELAY = 1.0




def mb_api_get(path: str, params: dict = {}, max_retries: int = 3) -> Optional[dict]:
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


def fetch_track_mb_data(isrc: str, existing_mb_id: str = None) -> dict:
    if existing_mb_id:
        mbid = existing_mb_id
    else:
        data = mb_api_get(f"isrc/{isrc}", {"inc": "artist-credits"})
        if(not(data) or not(data.get("recordings"))):
            return {}

        recording = data["recordings"][0]
        mbid = recording.get("id")
        if not(mbid):
            return {}

    rec_detail = mb_api_get(f"recording/{mbid}", {"inc": "releases"})
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


def build_artist_result(mbid: str, artist_details: dict, nameMatched: bool = False) -> dict:
    life_span = artist_details.get("life-span", {})
    return {
        "mb_id": mbid,
        "mb_type": artist_details.get("type"),
        "mb_gender": artist_details.get("gender"),
        "mb_country": artist_details.get("country"),
        "mb_area": artist_details.get("area", {}).get("name") if artist_details.get("area") else None,
        "mb_begin_date": life_span.get("begin"),
        "mb_end_date": life_span.get("end"),
        "mb_is_ended": life_span.get("ended", False),
        "mb_sort_name": artist_details.get("sort-name"),
        "mb_disambiguation": artist_details.get("disambiguation"),
        "mb_genres": [
            {
                "name": g["name"],
                "count": g["count"]
            }
            for g in artist_details.get("genres", [])
        ],
        "mb_name_matched": nameMatched,
        "mb_unmatched": False,
    }


def fetch_artist_mb_data(spotify_artist_id: str, artist_name: str = None) -> dict:
    # URL Spotify lookup
    data = mb_api_get("url/", {
        "query": f"url:https://open.spotify.com/artist/{spotify_artist_id}",
        "targettype": "artist",
    })
    if (data and data.get("urls")):
        try:
            mbid = data["urls"][0]["relation-list"][0]["relations"][0]["artist"]["id"]
            detail = mb_api_get(f"artist/{mbid}", {"inc": "aliases+tags+genres+url-rels"})
            if detail:
                return build_artist_result(mbid, detail)
        except (KeyError, IndexError):
            pass

    # fallback with name search
    if not(artist_name):
        return {"mb_unmatched": True}

    search_data = mb_api_get("artist/", {"query": f'artist:"{artist_name}"', "limit": 5})
    candidates = (search_data or {}).get("artists", [])

    # candidates are sorted by descending score
    if (not(candidates) or (candidates[0].get("score", 0) < 90)):
        return {"mb_unmatched": True}

    top_candidate_detail = None
    for candidate in candidates[:3]:
        if (candidate.get("score", 0) < 90):
            break
        artist_detail = mb_api_get(f"artist/{candidate['id']}", {"inc": "aliases+tags+genres+url-rels"})
        if not(artist_detail):
            continue
        if (top_candidate_detail is None):
            top_candidate_detail = (candidate["id"], artist_detail)
        for rel in artist_detail.get("relations", []):
            resource = rel.get("url", {}).get("resource", "")
            if (("open.spotify.com/artist/" in resource) and (spotify_artist_id in resource)):
                return build_artist_result(candidate["id"], artist_detail, nameMatched=True)

    # no Spotify match found, take top candidate
    top = candidates[0]
    if ((top.get("score") == 100)
            and ((len(candidates) == 1) or (candidates[1].get("score", 0) < 90))
            and (top_candidate_detail is not None)):
        topCandidateMbid, artist_detail = top_candidate_detail
        return build_artist_result(topCandidateMbid, artist_detail, nameMatched=True)

    return {"mb_unmatched": True}


def fetch_artist_mb_status(mb_id: str) -> dict:
    """Fetches only life-span status for an already-matched artist."""
    detail = mb_api_get(f"artist/{mb_id}")
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
    if (artists_collection is None):
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
    track_ids = [track["id"] for track in playlist_items]
    needs_enrichment = get_tracks_needing_mb_enrichment(track_ids, tracks_collection)
    to_enrich = [
        track for track in playlist_items
        if (track["id"] in needs_enrichment) and track.get("isrc") and not track.get("mb_id")
    ]

    if not(to_enrich):
        return playlist_items

    print("\n=== Starting track enrichment via MusicBrainz ===")
    skipped = len(track_ids) - len(needs_enrichment)
    print(f"{len(to_enrich)} track needing lookups ({skipped} already enriched, {len(needs_enrichment) - len(to_enrich)} missing ISRC).")

    id_to_index = {t["id"]: i for i, t in enumerate(playlist_items)}
    enriched_count = 0
    startTime = time.time()

    # lookups for tracks with ISRCs
    for count, track in enumerate(to_enrich, 1):
        ETA = (time.time() - startTime) / (count + 1) * (len(to_enrich) - count - 1)
        print(f"  MB track lookup {count}/{len(to_enrich)} (ETA: {ETA:.1f}s)...   ", end="\r")
        mb_data = fetch_track_mb_data(track["isrc"], existing_mb_id=track.get("mb_id"))
        if mb_data.get("mb_id"):
            playlist_items[id_to_index[track["id"]]].update(mb_data)
            enriched_count += 1

    print(f"\nMB track enrichment done: {enriched_count}/{len(to_enrich)} matched")
    return playlist_items


def enrich_artists_with_musicbrainz(
    playlist_items: List[Dict],
    artists_collection=None,
) -> List[Dict]:
    artist_map: Dict[str, dict] = {}
    for track in playlist_items:
        for artist in track["artists"]:
            artistId = artist["id"]
            if (artistId not in artist_map):
                artist_map[artistId] = artist

    artist_ids = list(artist_map.keys())
    # need_full, status_checks = get_artists_needing_mb_enrichment(artist_ids, artists_collection)
    need_full, status_checks = get_artists_needing_mb_enrichment(artist_ids, None) # debug for querying all artists

    if not need_full:
        return playlist_items

    print("\n=== Starting artist enrichment via MusicBrainz ===")
    # print(f"MB artist lookups needed: {len(need_full)} full, {len(status_checks)} status updates") # off for now
    print(f"MB artist lookups needed: {len(need_full)} full.")

    mb_results: Dict[str, dict] = {}
    startTime = time.time()

    # full lookup in musicbrainz
    for count, artistId in enumerate(need_full):
        ETA = (time.time() - startTime) / (count + 1) * (len(need_full) - count - 1)
        print(f"  MB artist full lookup {count+1}/{len(need_full)} (ETA: {ETA:.1f}s)...   ", end="\r")
        artist_name = artist_map[artistId].get("name")
        mb_data = fetch_artist_mb_data(artistId, artist_name=artist_name)
        if mb_data:
            mb_results[artistId] = mb_data

    # status lookup for currently active
    if False: # TODO: off for now since many artists are still active. Search for heuristics to avoid redundant lookups.
        for count, (artistId, mb_id) in enumerate(status_checks.items()):
            ETA = (time.time() - startTime) / (count + 1) * (len(status_checks) - count - 1)
            print(f"  MB artist status check {count+1}/{len(status_checks)} (ETA: {ETA:.1f}s)...   ", end="\r")
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