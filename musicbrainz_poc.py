import time
import requests
from typing import Optional

MB_BASE = "https://musicbrainz.org/ws/2"
MB_HEADERS = {
    "User-Agent": "BillionsCharts/1.0 (gatien.haddad@pradeo.com)",
    "Accept": "application/json",
}
RATE_LIMIT_DELAY = 0.1  # secondes entre chaque requête — ajuster selon rate limit réel

# ISRCs reels depuis la playlist Billions Club
TEST_ISRCS = [
    "USSM19902991",  # Billie Jean - Michael Jackson (decede)
    "GBAYE0501671",  # Put Your Records On - Corinne Bailey Rae
    "USAT21101961",  # Good Feeling - Flo Rida
    "USQX91802457",  # Babydoll - Dominic Fike
]

TEST_ARTISTS = [
    "Michael Jackson",   # Person - decede
    "Destiny's Child",   # Group - dissous
    "Corinne Bailey Rae",
    "Flo Rida",
]


def mb_get(path: str, params: dict = {}) -> Optional[dict]:
    url = f"{MB_BASE}/{path}"
    params = {**params, "fmt": "json"}
    try:
        response = requests.get(url, headers=MB_HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"  [HTTP {response.status_code}] {path}")
        return None
    except Exception as e:
        print(f"  [ERROR] {path}: {e}")
        return None
    finally:
        time.sleep(RATE_LIMIT_DELAY)


def get_language_from_releases(releases: list) -> tuple:
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


def lookup_recording_by_isrc(isrc: str) -> dict:
    # Step 1: ISRC → recording MBID + artistes
    data = mb_get(f"isrc/{isrc}", {"inc": "artist-credits"})
    if not data or not data.get("recordings"):
        return {"error": "Aucun recording trouve"}

    recording = data["recordings"][0]
    mbid = recording.get("id")

    artists = []
    for credit in recording.get("artist-credit", []):
        if isinstance(credit, dict) and "artist" in credit:
            artists.append(credit["artist"]["name"])

    # Step 2: recording MBID → releases avec langue (endpoint distinct)
    rec_detail = mb_get(f"recording/{mbid}", {"inc": "releases"})
    releases = rec_detail.get("releases", []) if rec_detail else []

    language, script = get_language_from_releases(releases)

    official = [r for r in releases if r.get("status") == "Official"] or releases
    dates = [r.get("date") for r in official if r.get("date")]
    earliest_date = min(dates) if dates else None

    return {
        "mbid": mbid,
        "title": recording.get("title"),
        "length_ms": recording.get("length"),
        "artists": artists,
        "language": language,
        "script": script,
        "earliest_release_date": earliest_date,
        "release_count": len(releases),
    }


def lookup_artist_by_name(name: str) -> dict:
    search = mb_get("artist", {"query": f'artist:"{name}"', "limit": 1})
    if not search or not search.get("artists"):
        return {"error": f"Aucun artiste trouvé pour '{name}'"}

    artist_stub = search["artists"][0]
    mbid = artist_stub.get("id")

    detail = mb_get(f"artist/{mbid}", {"inc": "aliases+tags+genres+url-rels"})
    if not detail:
        return {"error": f"Échec du détail pour MBID {mbid}"}

    genres = [g["name"] for g in detail.get("genres", [])]
    tags = sorted(detail.get("tags", []), key=lambda t: -t.get("count", 0))
    top_tags = [t["name"] for t in tags[:5]]

    wikipedia_url = None
    for rel in detail.get("relations", []):
        resource = rel.get("url", {}).get("resource", "")
        if "wikipedia.org" in resource:
            wikipedia_url = resource
            break

    life_span = detail.get("life-span", {})
    is_ended = life_span.get("ended", False)
    artist_type = detail.get("type")

    return {
        "mbid": mbid,
        "name": detail.get("name"),
        "type": artist_type,
        "gender": detail.get("gender"),
        "country": detail.get("country"),
        "area": detail.get("area", {}).get("name") if detail.get("area") else None,
        "begin_date": life_span.get("begin"),
        "end_date": life_span.get("end"),
        "is_deceased": is_ended and artist_type == "Person",
        "is_disbanded": is_ended and artist_type in ("Group", "Orchestra", "Choir"),
        "genres": genres,
        "top_tags": top_tags,
        "disambiguation": detail.get("disambiguation"),
        "wikipedia": wikipedia_url,
    }


SEP = "-" * 56


def print_track_report(isrc: str, data: dict):
    print(f"\n{SEP}")
    print(f"  ISRC      : {isrc}")
    if "error" in data:
        print(f"  [ERREUR]  : {data['error']}")
        return
    print(f"  Titre     : {data['title']}")
    print(f"  Artiste(s): {' / '.join(data['artists']) if data['artists'] else '-'}")
    print(f"  Langue    : {data['language'] or '-'}  (script: {data['script'] or '-'})")
    print(f"  1ere sortie officielle : {data['earliest_release_date'] or '-'}")
    if data.get("length_ms"):
        mins, secs = divmod(data["length_ms"] // 1000, 60)
        print(f"  Duree     : {mins}:{secs:02d}")
    print(f"  Releases MB: {data['release_count']}")
    print(f"  MBID      : {data['mbid']}")


def print_artist_report(name: str, data: dict):
    print(f"\n{SEP}")
    print(f"  Artiste   : {name}")
    if "error" in data:
        print(f"  [ERREUR]  : {data['error']}")
        return
    print(f"  Type      : {data['type'] or '-'}  |  Genre: {data['gender'] or '-'}")
    print(f"  Pays      : {data['area'] or data['country'] or '-'}")

    status_parts = []
    if data["is_deceased"]:
        status_parts.append(f"Decede ({data['end_date']})")
    elif data["is_disbanded"]:
        status_parts.append(f"Dissous ({data['end_date']})")
    else:
        status_parts.append("Actif")
    if data["begin_date"]:
        status_parts.append(f"Debut: {data['begin_date']}")
    print(f"  Statut    : {' | '.join(status_parts)}")

    if data.get("disambiguation"):
        print(f"  Note      : {data['disambiguation']}")
    if data["genres"]:
        print(f"  Genres    : {', '.join(data['genres'])}")
    if data["top_tags"]:
        print(f"  Tags      : {', '.join(data['top_tags'])}")
    if data["wikipedia"]:
        print(f"  Wikipedia : {data['wikipedia']}")
    print(f"  MBID      : {data['mbid']}")


if __name__ == "__main__":
    print("=" * 56)
    print("  POC MusicBrainz - Billions Charts")
    print(f"  Rate limit : {RATE_LIMIT_DELAY}s entre chaque requete")
    print("=" * 56)

    print("\n\n=== SONS (via ISRC) ===")
    for isrc in TEST_ISRCS:
        print(f"\n  > Fetching ISRC {isrc}...", end="", flush=True)
        data = lookup_recording_by_isrc(isrc)
        print_track_report(isrc, data)

    print("\n\n=== ARTISTES ===")
    for name in TEST_ARTISTS:
        print(f"\n  > Fetching artiste '{name}'...", end="", flush=True)
        data = lookup_artist_by_name(name)
        print_artist_report(name, data)

    print(f"\n\n{'=' * 56}")
    print("  POC termine.")
    print("=" * 56)
