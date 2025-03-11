from backend.database import retrieve_playlist_infos_from_mongo
from backend.utils import create_folder
from collections import defaultdict
from datetime import datetime
import json

MAX_TOP_SONGS = 10 # TODO: Dynamic backend limit for top songs




def aggregate_general(tracks):
    total_tracks = len(tracks)
    total_artists = len(set(artist['name'] for track in tracks for artist in track['artists']))
    total_streams = sum(track['playcount'] for track in tracks)
    return total_tracks, total_artists, total_streams


def aggregate_artists(tracks):
    artists_data = defaultdict(lambda: {"count": 0, "playcount": 0, "length": 0, "id": None, "image": None})

    # Aggregate data for each artist
    for track in tracks:
        for artist in track['artists']:
            artist_name = artist['name']
            artists_data[artist_name]["count"] += 1
            artists_data[artist_name]["playcount"] += track['playcount']
            artists_data[artist_name]["length"] += track['duration_ms']
            # Get the first artist id and image if still None
            if (not(artists_data[artist_name]["id"]) or not(artists_data[artist_name]["image"])):
                artists_data[artist_name]["id"] = artist.get('id')
                artists_data[artist_name]["image"] = artist.get('image')

    # Sort artists by count, playcount and length
    artists_count_array = sorted(
        ((artist, data["count"], data["id"], data["image"]) for artist, data in artists_data.items()),
        key=lambda x: x[1],
        reverse=True
    )[:MAX_TOP_SONGS]

    artists_playcount_array = sorted(
        ((artist, data["playcount"], data["id"], data["image"]) for artist, data in artists_data.items()),
        key=lambda x: x[1],
        reverse=True
    )[:MAX_TOP_SONGS]

    artists_length_array = sorted(
        ((artist, data["length"], data["id"], data["image"]) for artist, data in artists_data.items()),
        key=lambda x: x[1],
        reverse=True
    )[:MAX_TOP_SONGS]

    return artists_count_array, artists_playcount_array, artists_length_array


def aggregate_dates(tracks):
    normalized_tracks = []
    for track in tracks:
        release_date = track["release_date"]
        precision = track["release_date_precision"]

        if precision == "month":
            release_date += "-01"
        elif precision == "year":
            release_date += "-01-01"

        normalized_tracks.append({
            "id": track['id'],
            "name": track['name'],
            "artists": [{
                    "id": artist.get('id'),
                    "name": artist['name'],
                    "image": artist.get('image')
                } 
                for artist in track['artists']
            ],
            "image": track['image'],
            "release_date": release_date
        })

    sorted_tracks = sorted(normalized_tracks, key=lambda x: x['release_date'])
    oldest_tracks = sorted_tracks[:MAX_TOP_SONGS]
    newest_tracks = sorted_tracks[-MAX_TOP_SONGS:][::-1]

    return oldest_tracks, newest_tracks


def agregate_billions(tracks):
    normalized_tracks = []
    for track in tracks:
        release_date = track["release_date"] 
        if track["release_date_precision"] == "year":
            release_date += "-01-01"
        elif track["release_date_precision"] == "month":
            release_date += "-01"
        billion_date = track['added_at'].split("T")[0] # format : "2022-07-27T16:32:16.167Z"
        normalized_tracks.append({
            "id": track['id'],
            "name": track['name'],
            "artists": [{
                    "id": artist.get('id'),
                    "name": artist['name'],
                    "image": artist.get('image')
                } 
                for artist in track['artists']
            ],
            "popularity": track['popularity'],
            "image": track['image'],
            "added_at": billion_date,
            "billion_time": (datetime.strptime(billion_date, "%Y-%m-%d") - datetime.strptime(release_date, "%Y-%m-%d")).days
        })

    newest_billions = sorted(normalized_tracks, key=lambda x: x['added_at'], reverse=True)[:MAX_TOP_SONGS]
    fastest_billions = sorted(normalized_tracks, key=lambda x: x['billion_time'], reverse=False)[:MAX_TOP_SONGS]

    return newest_billions, fastest_billions


def aggregate_by_key(tracks, agregateKey):
    sorted_tracks = sorted(tracks, key=lambda x: x[agregateKey], reverse=True)

    mapped_tracks = [
        {
            "id": track['id'],
            "name": track['name'],
            "artists": [{
                    "id": artist.get('id'), 
                    "name": artist['name'], 
                    "image": artist.get('image')
                } 
                for artist in track['artists']
            ],
            "playcount": track['playcount'],
            "popularity": track['popularity'],
            "duration_ms": track['duration_ms'],
            "image": track['image']
        }
        for track in sorted_tracks
    ]

    descending_tracks = mapped_tracks[:MAX_TOP_SONGS]
    ascending_tracks = mapped_tracks[-MAX_TOP_SONGS:][::-1]

    return descending_tracks, ascending_tracks


def aggregate_periods(tracks):
    year_count = defaultdict(int)
    month_count = defaultdict(int)

    for track in tracks:
        release_date = track['release_date']
        precision = track['release_date_precision']

        if precision == "year":
            year_count[release_date] += 1
        else:
            year, month, *_ = release_date.split("-")
            year_count[year] += 1
            if month:
                month_count[month] += 1

    return dict(year_count), dict(month_count)


def get_template_data(tracks, report):
    total_tracks = report["total_tracks"]
    
    two_billion_count = int(sum(1 for track in tracks if (track["playcount"] >= 2_000_000_000)))
    three_billion_count = int(sum(1 for track in tracks if (track["playcount"] >= 3_000_000_000)))
    four_billion_count = int(sum(1 for track in tracks if (track["playcount"] >= 4_000_000_000)))

    two_billion_percentage = round(100*(two_billion_count / total_tracks), 2)
    three_billion_percentage = round(100*(three_billion_count / total_tracks), 2)
    
    latest_billion = report["newest_billions"][0]
    fastest_billion = report["fastest_billions"][0]
    shortest_song = report["most_short_tracks"][0]
    longest_song = report["most_long_tracks"][0]

    current_year = datetime.now().year
    year_count = sum(1 for track in tracks if (track["release_date"].startswith(str(current_year))))

    most_popular_song = report["most_popular_tracks"][0]
    most_popular_artist = most_popular_song["artists"][0]["name"]

    return {
        "two_billion_count": two_billion_count,
        "two_billion_percentage": two_billion_percentage,
        "three_billion_count": three_billion_count,
        "three_billion_percentage": three_billion_percentage,
        "four_billion_count": four_billion_count,
        "four_billion_song": report["most_streamed_tracks"][0]["name"],
        "four_billion_song_link": f"https://open.spotify.com/track/{report['most_streamed_tracks'][0]['id']}",
        "four_billion_artist": report["most_streamed_tracks"][0]["artists"][0]["name"],
        "four_billion_artist_link": f"https://open.spotify.com/artist/{report['most_streamed_tracks'][0]['artists'][0]['id']}",
        "latest_song": latest_billion["name"],
        "latest_song_link": f"https://open.spotify.com/track/{latest_billion['id']}",
        "latest_artist": latest_billion["artists"][0]["name"],
        "latest_artist_link": f"https://open.spotify.com/artist/{latest_billion['artists'][0]['id']}",
        "latest_date": datetime.strptime(latest_billion["added_at"], "%Y-%m-%d").strftime("%B %d, %Y"),
        "this_year_count": year_count,
        "most_popular_song": most_popular_song["name"],
        "most_popular_song_link": f"https://open.spotify.com/track/{most_popular_song['id']}",
        "most_popular_artist": most_popular_artist,
        "most_popular_artist_link": f"https://open.spotify.com/artist/{most_popular_song['artists'][0]['id']}",
        "most_popular_streams": f"{most_popular_song['playcount'] // 1_000_000_000:.2f}B",
        "fastest_song": fastest_billion["name"],
        "fastest_song_link": f"https://open.spotify.com/track/{fastest_billion['id']}",
        "fastest_artist": fastest_billion["artists"][0]["name"],
        "fastest_artist_link": f"https://open.spotify.com/artist/{fastest_billion['artists'][0]['id']}",
        "fastest_days": fastest_billion["billion_time"],
        "shortest_song": shortest_song["name"],
        "shortest_song_link": f"https://open.spotify.com/track/{shortest_song['id']}",
        "shortest_artist": shortest_song["artists"][0]["name"],
        "shortest_artist_link": f"https://open.spotify.com/artist/{shortest_song['artists'][0]['id']}",
        "shortest_duration": f"{shortest_song['duration_ms'] // 60000}:{(shortest_song['duration_ms'] // 1000) % 60:02d}",
        "longest_song": longest_song["name"],
        "longest_song_link": f"https://open.spotify.com/track/{longest_song['id']}",
        "longest_artist": longest_song["artists"][0]["name"],
        "longest_artist_link": f"https://open.spotify.com/artist/{longest_song['artists'][0]['id']}",
        "longest_duration": f"{longest_song['duration_ms'] // 60000}:{(longest_song['duration_ms'] // 1000) % 60:02d}"
    }


def generate_report(dataPath, outputReportPath, WRITE_TO_DATABASE):
    if WRITE_TO_DATABASE:
        dateKey = dataPath.split("_")[-1].split(".")[0]
        playlist = retrieve_playlist_infos_from_mongo(dateKey)
        if not(playlist):
            raise Exception(f"No data found for {dateKey} in database.")
    else:
        with open(dataPath, 'r', encoding='utf-8') as f:
            playlist = json.load(f)

    create_folder("data/reports/")
    create_folder("public/data/")

    tracks = playlist['items']

    total_tracks, total_artists, total_streams = aggregate_general(tracks)
    artists_counts, artists_playcounts, artists_length = aggregate_artists(tracks)
    oldest_tracks, newest_tracks = aggregate_dates(tracks)
    newest_billions, fastest_billions = agregate_billions(tracks)
    most_streamed_tracks, least_streamed_tracks = aggregate_by_key(tracks, "playcount")
    most_popular_tracks, least_popular_tracks = aggregate_by_key(tracks, "popularity")
    most_long_tracks, most_short_tracks = aggregate_by_key(tracks, "duration_ms")
    year_count, month_count = aggregate_periods(tracks)

    final_report = {
        "name": playlist['name'],
        "description": playlist['description'],
        "generatedTimeStamp": playlist['generatedTimeStamp'],
        "followers": playlist['followers'],
        "coverUrl": playlist['coverUrl'],
        "coverHex": playlist['coverHex'],
        "total_tracks": total_tracks,
        "total_artists": total_artists,
        "total_streams": total_streams,
        "artists_counts": artists_counts,
        "artists_playcounts": artists_playcounts,
        "artists_length": artists_length,
        "oldest_tracks": oldest_tracks,
        "newest_tracks": newest_tracks,
        "newest_billions": newest_billions,
        "fastest_billions": fastest_billions,
        "most_streamed_tracks": most_streamed_tracks,
        "least_streamed_tracks": least_streamed_tracks,
        "most_popular_tracks": most_popular_tracks,
        "least_popular_tracks": least_popular_tracks,
        "most_long_tracks": most_long_tracks,
        "most_short_tracks": most_short_tracks,
        "year_count": year_count,
        "month_count": month_count,
    }
    final_report["template_data"] = get_template_data(tracks, final_report)

    with open(outputReportPath, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=4)

    print(f"Report successfully generated in {outputReportPath}.")


def generate_leaderboard(dataPath, WRITE_TO_DATABASE):
    create_folder("data/analysis/")

    if WRITE_TO_DATABASE:
        dateKey = dataPath.split("_")[-1].split(".")[0]
        tracks_data = retrieve_playlist_infos_from_mongo(dateKey)
    else:
        with open(dataPath, "r", encoding="utf-8") as f:
            tracks_data = json.load(f)

    artists = {}
    streams = {}
    tracks = {}
    for track in tracks_data["items"]:
        for artist in track["artists"]:
            artists[artist["name"]] = artists.get(artist["name"], 0) + 1
            streams[artist["name"]] = streams.get(artist["name"], 0) + track["playcount"]
        tracks[track["name"]] = track["playcount"]

    leaderboard_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)
    leaderboard_streams = sorted(streams.items(), key=lambda x: x[1], reverse=True)
    leaderboard_tracks = sorted(tracks.items(), key=lambda x: x[1], reverse=True)

    with open("data/analysis/leaderboard_artists.txt", "w", encoding="utf-8") as f:
        for i, (artist, count) in enumerate(leaderboard_artists):
            f.write(f"{i+1}. {artist}: {count} tracks\n")

    with open("data/analysis/leaderboard_streams.txt", "w", encoding="utf-8") as f:
        for i, (artist, count) in enumerate(leaderboard_streams):
            f.write(f"{i+1}. {artist}: {count/1_000_000_000:.2f}B streams\n")

    with open("data/analysis/leaderboard_tracks.txt", "w", encoding="utf-8") as f:
        for i, (track, count) in enumerate(leaderboard_tracks):
            f.write(f"{i+1}. {track}: {count/1_000_000_000:.2f}B streams\n")

    print("Leaderboards updated.")