from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
from backend.utils import correct_uncertain_date
import requests
import time

MB_BASE = "https://musicbrainz.org/ws/2"
MB_HEADERS = {
    "User-Agent": "BillionsCharts/1.3.0 ( contact@billions-charts.com )",
    "Accept": "application/json",
}
RATE_LIMIT_DELAY = 1.0




class MusicBrainzError(Exception):
    """Technical failure like network or repeated 503."""


@dataclass
class EnrichmentProgress:
    """Tracks a lookup run across all checkpoint batches, so the counter and ETA cover the whole run and not a single batch."""
    label: str
    total: int
    done: int = 0
    matched: int = 0
    unmatched: int = 0
    failed: int = 0
    start_time: float = field(default_factory=time.time)

    def print_progress(self) -> None:
        eta = (time.time() - self.start_time) / self.done * (self.total - self.done) if (self.done > 0) else 0
        print(f"  MB {self.label} lookup {self.done + 1}/{self.total} (ETA: {eta:.1f}s)...   ", end="\r")

    def record_result(self, mb_data: dict) -> None:
        self.done += 1
        if mb_data.get("mb_id"):
            self.matched += 1
        else:
            self.unmatched += 1

    def record_failure(self, item_id: str, error: MusicBrainzError) -> None:
        self.done += 1
        self.failed += 1
        print(f"\n  [ERROR] MB {self.label} {item_id}: {error}")

    def print_checkpoint(self) -> None:
        print(f"\n  Checkpoint saved: {self.done}/{self.total} {self.label}s processed")

    def print_summary(self) -> None:
        print(f"MB {self.label} enrichment done: {self.matched} matched, {self.unmatched} unmatched, {self.failed} failed (retried on next run)")


def mb_api_get(path: str, params: dict = {}, max_retries: int = 3) -> Optional[dict]:
    """Returns the JSON response, or None when MusicBrainz answers 404 (the resource does not exist). Raises MusicBrainzError on any technical failure."""
    url = f"{MB_BASE}/{path}"
    params = {**params, "fmt": "json"}
    start = time.time()

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=MB_HEADERS, params=params, timeout=10)
        except requests.RequestException as e:
            time.sleep(RATE_LIMIT_DELAY)
            raise MusicBrainzError(f"{path}: {e}")

        if (response.status_code == 503):
            backoff = RATE_LIMIT_DELAY * (2 ** (attempt + 1))
            print(f"\n  [503] MB rate limited: retry {attempt+1}/{max_retries} in {backoff:.0f}s...")
            time.sleep(backoff)
            continue

        elapsed = time.time() - start
        time.sleep(max(0, RATE_LIMIT_DELAY - elapsed))

        if (response.status_code == 404):
            return None
        if not(response.ok):
            raise MusicBrainzError(f"{path}: HTTP {response.status_code}")

        try:
            return response.json()
        except ValueError as e:
            raise MusicBrainzError(f"{path}: invalid JSON ({e})")

    raise MusicBrainzError(f"{path}: too many 503s after {max_retries} attempts")


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
            return {"mb_unmatched": True}

        recording = data["recordings"][0]
        mbid = recording.get("id")
        if not(mbid):
            return {"mb_unmatched": True}

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
        "mb_unmatched": False,
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


def lookup_artist_by_spotify_url(spotify_artist_id: str) -> Optional[dict]:
    data = mb_api_get("url/", {
        "query": f"url:https://open.spotify.com/artist/{spotify_artist_id}",
        "targettype": "artist",
    })
    if not(data and data.get("urls")):
        return None

    try:
        mbid = data["urls"][0]["relation-list"][0]["relations"][0]["artist"]["id"]
    except (KeyError, IndexError):
        return None

    detail = mb_api_get(f"artist/{mbid}", {"inc": "aliases+tags+genres+url-rels"})
    if detail:
        return build_artist_result(mbid, detail)
    else:
        return None


def search_artist_by_name(spotify_artist_id: str, artist_name: Optional[str]) -> Tuple[dict, bool]:
    """Returns the MB result and whether it is confirmed by a Spotify link on the MB artist page."""
    if not(artist_name):
        return {"mb_unmatched": True}, False

    search_data = mb_api_get("artist/", {"query": f'artist:"{artist_name}"', "limit": 5})
    candidates = (search_data or {}).get("artists", [])

    # candidates are sorted by descending score
    if (not(candidates) or (candidates[0].get("score", 0) < 90)):
        return {"mb_unmatched": True}, False

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
                return build_artist_result(candidate["id"], artist_detail, nameMatched=True), True

    # no Spotify match found, take top candidate
    top = candidates[0]
    if ((top.get("score") == 100)
            and ((len(candidates) == 1) or (candidates[1].get("score", 0) < 90))
            and (top_candidate_detail is not None)):
        topCandidateMbid, artist_detail = top_candidate_detail
        return build_artist_result(topCandidateMbid, artist_detail, nameMatched=True), False
    else:
        return {"mb_unmatched": True}, False


def fetch_artist_mb_data(spotify_artist_id: str, artist_name: str = None) -> dict:
    url_lookup_error = None
    try:
        url_match = lookup_artist_by_spotify_url(spotify_artist_id)
    except MusicBrainzError as e:
        url_match, url_lookup_error = None, e

    if url_match:
        return url_match

    # fallback with name search
    name_result, spotify_confirmed = search_artist_by_name(spotify_artist_id, artist_name)
    if ((url_lookup_error is not None) and not(spotify_confirmed)):
        # The failed URL lookup could have found another artist: only a Spotify-confirmed match is trustworthy enough to keep.
        raise url_lookup_error
    else:
        return name_result


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
    if (tracks_collection is None):
        return set(track_ids)
    try:
        already = tracks_collection.find(
            {
                "id": {"$in": track_ids},
                "$or": [{"mb_id": {"$exists": True}}, {"mb_unmatched": True}],
            },
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


def select_tracks_to_enrich(
    playlist_items: List[Dict],
    tracks_collection=None,
) -> List[Dict]:
    """Returns the track dicts themselves (not copies), so the lookups enrich the playlist in place."""
    track_ids = [track["id"] for track in playlist_items]
    needs_enrichment = get_tracks_needing_mb_enrichment(track_ids, tracks_collection)
    to_enrich = [
        track for track in playlist_items
        if (track["id"] in needs_enrichment) and track.get("isrc") and not track.get("mb_id")
    ]

    skipped = len(track_ids) - len(needs_enrichment)
    print(f"{len(to_enrich)} tracks needing MB lookups ({skipped} already enriched, {len(needs_enrichment) - len(to_enrich)} missing ISRC).")
    return to_enrich


def select_artists_to_enrich(
    artists_dict: Dict[str, dict],
    artists_collection=None,
) -> List[Dict]:
    """Returns the artist dicts themselves (not copies), so the lookups enrich the playlist in place."""
    artist_ids = list(artists_dict.keys())
    need_full, status_checks = get_artists_needing_mb_enrichment(artist_ids, artists_collection)
    # need_full, status_checks = get_artists_needing_mb_enrichment(artist_ids, None) # debug for querying all artists
    # TODO: status_checks (fetch_artist_mb_status) are off for now since many artists are still active. Search for heuristics to avoid redundant lookups.

    print(f"{len(need_full)} artists needing MB full lookups.")
    return [artists_dict[artistId] for artistId in need_full]


def enrich_batch(
    items: List[Dict],
    fetch_mb_data: Callable[[Dict], dict],
    progress: EnrichmentProgress,
) -> None:
    """Merges the MB fields into each item in place. An item whose lookup failed is left untouched, so it stays 'to do' for the next run."""
    for item in items:
        progress.print_progress()
        try:
            mb_data = fetch_mb_data(item)
        except MusicBrainzError as e:
            progress.record_failure(item["id"], e)
            continue
        item.update(mb_data)
        progress.record_result(mb_data)


def enrich_tracks_batch(tracks: List[Dict], progress: EnrichmentProgress) -> None:
    enrich_batch(tracks, lambda track: fetch_track_mb_data(track["isrc"]), progress)


def enrich_artists_batch(artists: List[Dict], progress: EnrichmentProgress) -> None:
    enrich_batch(artists, lambda artist: fetch_artist_mb_data(artist["id"], artist_name=artist.get("name")), progress)


def is_mb_processed(track: Dict) -> bool:
    return bool(track.get("mb_id") or track.get("mb_unmatched"))


def backfill_mb_release_dates(
    playlist_items: List[Dict],
    tracks_collection=None,
) -> None:
    """Fetches mb_id, mb_unmatched and mb_release_date from DB for uncertain tracks MB-processed in a prior run."""
    id_to_index = {track["id"]: i for i, track in enumerate(playlist_items)}
    uncertain_ids_to_fetch = [
        track["id"] for track in playlist_items
        if track.get("release_date_uncertain")
        and not(is_mb_processed(track))
    ]

    if (uncertain_ids_to_fetch and (tracks_collection is not None)):
        try:
            docs = tracks_collection.find(
                {"id": {"$in": uncertain_ids_to_fetch}},
                {"id": 1, "mb_id": 1, "mb_unmatched": 1, "mb_release_date": 1, "_id": 0},
            )
            for doc in docs:
                idx = id_to_index.get(doc["id"])
                if (idx is None):
                    continue
                for field in ("mb_id", "mb_unmatched", "mb_release_date"):
                    if (field in doc):
                        playlist_items[idx][field] = doc[field]
        except Exception as e:
            raise RuntimeError(f"Error backfilling MB fields for uncertain tracks: {e}")


def correct_uncertain_release_dates(
    playlist_items: List[Dict],
    tracks_collection=None,
) -> List[Dict]:
    """Applies MB release date corrections to uncertain tracks, fallback to downgrade to year precision. Must run after all MB lookups."""
    backfill_mb_release_dates(playlist_items, tracks_collection) # updates playlist_items in place

    changed = 0
    deferred = 0
    for i in range(len(playlist_items)):
        if not playlist_items[i].get("release_date_uncertain"):
            continue
        track = playlist_items[i]

        # leave the date unvalidated for a later run
        if not(is_mb_processed(track)):
            playlist_items[i]["corrected_release_date"] = False
            deferred += 1
            continue

        new_date, new_precision = correct_uncertain_date(track.get("release_date"), track.get("release_date_precision"), track.get("mb_release_date"))
        playlist_items[i]["release_date"] = new_date
        playlist_items[i]["release_date_precision"] = new_precision
        playlist_items[i]["corrected_release_date"] = True
        changed += 1

    if (changed > 0):
        print(f"Uncertain date correction: {changed} tracks corrected.")
    else:
        print("No uncertain date correction made.")
    if (deferred > 0):
        print(f"Uncertain date correction: {deferred} tracks deferred until MusicBrainz has processed them.")

    return playlist_items
