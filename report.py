from collections import defaultdict
import json

MAX_TOP_SONGS = 10




def aggregate_general(tracks):
    total_tracks = len(tracks)
    total_artists = len(set(artist['name'] for track in tracks for artist in track['artists']))
    total_streams = sum(track['playcount'] for track in tracks)
    return total_tracks, total_artists, total_streams


def aggregate_artists(tracks):
    artists_count = defaultdict(int)
    artists_playcount = defaultdict(int)
    artists_length = defaultdict(int)

    for track in tracks:
        for artist in track['artists']:
            artist_name = artist['name']
            artists_count[artist_name] += 1
            artists_playcount[artist_name] += track['playcount']
            artists_length[artist_name] += track['duration_ms']

    artists_count_array = sorted(artists_count.items(), key=lambda x: x[1], reverse=True)[:MAX_TOP_SONGS]
    artists_playcount_array = sorted(artists_playcount.items(), key=lambda x: x[1], reverse=True)[:MAX_TOP_SONGS]
    artists_length_array = sorted(artists_length.items(), key=lambda x: x[1], reverse=True)[:MAX_TOP_SONGS]

    return artists_count_array, artists_playcount_array, artists_length_array


def aggregate_dates(tracks):
    normalized_tracks = []
    for track in tracks:
        release_date = track['release_date']
        precision = track['release_date_precision']

        if precision == "month":
            release_date += "-01"
        elif precision == "year":
            release_date += "-01-01"

        normalized_tracks.append({
            "name": track['name'],
            "artists": [artist['name'] for artist in track['artists']],
            "playcount": track['playcount'],
            "release_date": release_date
        })

    sorted_tracks = sorted(normalized_tracks, key=lambda x: x['release_date'])
    oldest_tracks = sorted_tracks[:MAX_TOP_SONGS]
    newest_tracks = sorted_tracks[-MAX_TOP_SONGS:][::-1]

    return oldest_tracks, newest_tracks


def aggregate_playcount(tracks):
    sorted_tracks = sorted(tracks, key=lambda x: x['playcount'], reverse=True)

    most_streamed_tracks = sorted_tracks[:MAX_TOP_SONGS]
    least_streamed_tracks = sorted_tracks[-MAX_TOP_SONGS:][::-1]

    return most_streamed_tracks, least_streamed_tracks


def aggregate_popularity(tracks):
    sorted_tracks = sorted(tracks, key=lambda x: (x['popularity'], x['playcount']), reverse=True)

    most_popular_tracks = sorted_tracks[:MAX_TOP_SONGS]
    least_popular_tracks = sorted_tracks[-MAX_TOP_SONGS:][::-1]

    return most_popular_tracks, least_popular_tracks


def aggregate_length(tracks):
    sorted_tracks = sorted(tracks, key=lambda x: x['duration_ms'], reverse=True)

    most_long_tracks = sorted_tracks[:MAX_TOP_SONGS]
    most_short_tracks = sorted_tracks[-MAX_TOP_SONGS:][::-1]

    return most_long_tracks, most_short_tracks


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


def generate_report(playlist_file, output_report_file):
    with open(playlist_file, 'r', encoding='utf-8') as f:
        playlist = json.load(f)

    tracks = playlist['items']

    total_tracks, total_artists, total_streams = aggregate_general(tracks)
    artists_counts, artists_playcounts, artists_length = aggregate_artists(tracks)
    oldest_tracks, newest_tracks = aggregate_dates(tracks)
    most_streamed_tracks, least_streamed_tracks = aggregate_playcount(tracks)
    most_popular_tracks, least_popular_tracks = aggregate_popularity(tracks)
    most_long_tracks, most_short_tracks = aggregate_length(tracks)
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
        "most_streamed_tracks": most_streamed_tracks,
        "least_streamed_tracks": least_streamed_tracks,
        "most_popular_tracks": most_popular_tracks,
        "least_popular_tracks": least_popular_tracks,
        "most_long_tracks": most_long_tracks,
        "most_short_tracks": most_short_tracks,
        "year_count": year_count,
        "month_count": month_count
    }

    with open(output_report_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=4)