from typing import Dict, List, Optional, Tuple
import time
import requests




def fetch_track_via_isrc(
    track_id: str,
    track_name: str,
    isrc: Optional[str],
    headers: Dict[str, str],
    original_track_data: Dict
) -> Dict:
    """
    Fetch corrected track info using ISRC search, filtering for singles.
    
    Args:
        track_id: Spotify track ID
        track_name: Track name to match
        isrc: ISRC code to search for
        headers: Spotify API headers with authorization
        original_track_data: Original batch-fetched track data (fallback)
    
    Returns:
        Dict with corrected track info (id, name, popularity, release_date, release_date_precision)
        Falls back to original data if no matching single found
    """
    
    if not isrc:
        # No ISRC available, return original data
        return original_track_data
    
    try:
        # Search using ISRC
        params = {"q": f"isrc:{isrc}", "type": "track", "limit": 50}
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        results = response.json().get("tracks", {}).get("items", [])
        
        if not results:
            # No results found, return original data
            return original_track_data
        
        # Find the first matching single with matching track name
        for result in results:
            album = result.get("album", {})
            album_type = album.get("album_type")
            result_name = album.get("name", "").lower().strip()
            target_name = track_name.lower().strip()
            
            # Match track name and ensure it's a single (not an album version)
            if (result_name == target_name and 
                album_type == "single"):
                
                return {
                    "id": result["id"],
                    "name": result["name"],
                    "popularity": result["popularity"],
                    "release_date": album["release_date"],
                    "release_date_precision": album["release_date_precision"],
                    "isrc": isrc,
                    "corrected_release_date": True
                }
        
        # No single match found, return original data
        return original_track_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ISRC {isrc} for track {track_id}: {e}")
        return original_track_data
    except Exception as e:
        print(f"Unexpected error processing ISRC {isrc}: {e}")
        return original_track_data


def get_tracks_already_corrected(track_ids: List[str], tracks_collection) -> set:
    """
    Query database to find tracks already corrected with ISRC lookup.
    
    Args:
        track_ids: List of Spotify track IDs
        tracks_collection: MongoDB tracks collection
    
    Returns:
        Set of track IDs that have been corrected
    """
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
    overwrite: bool = False
) -> List[Dict]:
    """
    Enrich tracks with correct release dates by searching for singles via ISRC.
    
    This function:
    1. First tries to get ISRC for each track (via batch API call)
    2. For each track, searches Spotify API for the ISRC
    3. Filters results to find the single (album_type == "single")
    4. Replaces release_date with the single's date
    5. Caches corrected tracks in the database to avoid re-fetching
    
    Args:
        playlist_items: List of track items with at least 'id' and 'name'
        headers: Spotify API headers with authorization
        tracks_collection: MongoDB tracks collection (optional, for caching)
        overwrite: If True, re-fetch all tracks. If False, skip already-corrected tracks
    
    Returns:
        List of tracks with corrected release date info
    """
    
    print("\n=== Starting track enrichment via ISRC search ===")
    
    # Determine which tracks to process
    track_ids = [track["id"] for track in playlist_items]
    
    # If caching is enabled, find already-corrected tracks
    already_corrected = set()
    if tracks_collection and not overwrite:
        already_corrected = get_tracks_already_corrected(track_ids, tracks_collection)
        print(f"Found {len(already_corrected)} already-corrected tracks, skipping them")
    
    # Determine which tracks need enrichment
    tracks_to_enrich = [
        track for track in playlist_items 
        if track["id"] not in already_corrected
    ]
    
    if not tracks_to_enrich:
        print("All tracks already corrected. Skipping ISRC enrichment.")
        return playlist_items
    
    print(f"Enriching {len(tracks_to_enrich)}/{len(playlist_items)} tracks via ISRC search...")
    
    # Build track_id -> track_name mapping for faster lookup
    track_lookup = {track["id"]: track["name"] for track in tracks_to_enrich}
    
    # First, fetch ISRC for all tracks via batch API call
    # This requires an additional batch fetch to get ISRC codes
    isrc_data = _fetch_isrc_codes_batch(track_ids, headers)
    
    # Now enrich each track with ISRC search
    enriched_count = 0
    for i, track in enumerate(tracks_to_enrich):
        print(f"Enriching track {i+1}/{len(tracks_to_enrich)}: {track.get('name', 'Unknown')}...", end="\r")
        
        track_id = track["id"]
        track_name = track_lookup.get(track_id)
        
        # Get ISRC for this track
        isrc = isrc_data.get(track_id)
        
        # Create original track data dict (fallback)
        original_data = {
            "id": track_id,
            "name": track_name,
            "popularity": track.get("popularity"),
            "release_date": track.get("release_date"),
            "release_date_precision": track.get("release_date_precision")
        }
        
        # Fetch via ISRC and get corrected data
        corrected_data = fetch_track_via_isrc(
            track_id, 
            track_name, 
            isrc, 
            headers, 
            original_data
        )
        
        # Update the original track item with corrected data
        if corrected_data.get("corrected_release_date"):
            enriched_count += 1
        
        # Update the track with corrected info
        idx = next((j for j, t in enumerate(playlist_items) if t["id"] == track_id), None)
        if idx is not None:
            playlist_items[idx]["popularity"] = corrected_data["popularity"]
            playlist_items[idx]["release_date"] = corrected_data["release_date"]
            playlist_items[idx]["release_date_precision"] = corrected_data["release_date_precision"]
            playlist_items[idx]["corrected_release_date"] = corrected_data.get("corrected_release_date", False)
            if "isrc" in corrected_data:
                playlist_items[idx]["isrc"] = corrected_data["isrc"]
        
        # Rate limiting: add small delay to avoid hitting Spotify rate limits
        time.sleep(0.1)
    
    print(f"Enriched track {len(tracks_to_enrich)}/{len(playlist_items)}: complete!          ")
    print(f"Successfully found {enriched_count} singles with correct release dates")
    
    return playlist_items


def _fetch_isrc_codes_batch(track_ids: List[str], headers: Dict[str, str]) -> Dict[str, str]:
    """
    Fetch ISRC codes for all tracks in batches.
    
    Args:
        track_ids: List of Spotify track IDs
        headers: Spotify API headers
    
    Returns:
        Dict mapping track_id -> ISRC code
    """
    
    isrc_data = {}
    
    print("Fetching ISRC codes for tracks...")
    for i in range(0, len(track_ids), 50):
        chunk = track_ids[i:i + 50]
        params = {"ids": ",".join(chunk)}
        
        try:
            response = requests.get(
                "https://api.spotify.com/v1/tracks",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            tracks_data = response.json().get("tracks", [])
            
            for track in tracks_data:
                if track:
                    track_id = track.get("id")
                    isrc = track.get("external_ids", {}).get("isrc")
                    if track_id and isrc:
                        isrc_data[track_id] = isrc
        
        except Exception as e:
            print(f"Error fetching ISRC batch at {i}: {e}")
    
    print(f"Retrieved ISRC codes for {len(isrc_data)} tracks")
    return isrc_data


def fetch_artists_batch(artist_ids: List[str], headers: Dict[str, str]) -> Dict:
    """
    Fetch artist information in batches from Spotify API.
    
    Args:
        artist_ids: List of Spotify artist IDs
        headers: Spotify API headers
    
    Returns:
        Dict mapping artist_id -> artist info
    """
    
    artists_infos = {}
    
    print(f"Fetching {len(artist_ids)} artists...")
    for i in range(0, len(artist_ids), 50):
        print(f"Fetching artists {i}/{len(artist_ids)}...", end="\r")
        batch = artist_ids[i:i + 50]
        params = {"ids": ",".join(batch)}
        
        try:
            response = requests.get(
                "https://api.spotify.com/v1/artists",
                headers=headers,
                params=params
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
                        "image": max(artist["images"], key=lambda x: x["width"]) if artist["images"] else None
                    }
        
        except Exception as e:
            print(f"Error fetching artist batch {i}: {e}")
    
    print(f"Fetching artists {len(artist_ids)}/{len(artist_ids)} done!")
    return artists_infos
