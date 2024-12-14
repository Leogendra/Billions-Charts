const fs = require('fs');

const MAX_TOP_SONGS = 10;




async function agregate_general(tracks) {
    const total_tracks = tracks.length;
    const total_artists = new Set(tracks.flatMap(track => track.artists.map(artist => artist.name))).size;
    const total_streams = tracks.reduce((acc, track) => acc + track.playcount, 0);

    return [total_tracks, total_artists, total_streams];
}


async function agregate_artists(tracks) {
    let artists_count = {};
    let artists_playcount = {};
    let artists_lenght = {};

    tracks.forEach(track => {
        track.artists.forEach(artist => {
            const artistName = artist.name;
            artists_count[artistName] = (artists_count[artistName] || 0) + 1;
            artists_playcount[artistName] = (artists_playcount[artistName] || 0) + track.playcount;
            artists_lenght[artistName] = (artists_lenght[artistName] || 0) + track.duration_ms;
        });
    });

    let artists_count_array = Object.entries(artists_count).map(([name, count]) => ({ name, count }));
    artists_count_array.sort((a, b) => b.count - a.count)
        .splice(MAX_TOP_SONGS);

    let artists_playcount_array = Object.entries(artists_playcount).map(([name, count]) => ({ name, count }));
    artists_playcount_array.sort((a, b) => b.count - a.count)
        .splice(MAX_TOP_SONGS);

    let artists_lenght_array = Object.entries(artists_lenght).map(([name, count]) => ({ name, count }));
    artists_lenght_array.sort((a, b) => b.count - a.count)
        .splice(MAX_TOP_SONGS);

    return [artists_count_array, artists_playcount_array, artists_lenght_array];
}


async function agregate_dates(tracks) {
    const sortedTracks = tracks
        .map(track => {
            const { name, artists, playcount, release_date, release_date_precision } = track;

            let normalizedDate = release_date;
            if (release_date_precision === "month") {
                normalizedDate = `${release_date}-01`;
            }
            else if (release_date_precision === "year") {
                normalizedDate = `${release_date}-01-01`;
            }

            return {
                name,
                artists: artists.map(artist => artist.name),
                playcount,
                release_date: normalizedDate,
            };
        })
        .sort((a, b) => a.release_date.localeCompare(b.release_date));

    const oldest_tracks = sortedTracks.slice(0, MAX_TOP_SONGS);
    const newest_tracks = sortedTracks.slice(-MAX_TOP_SONGS).reverse();

    return [oldest_tracks, newest_tracks];
}


async function agregate_playcount(tracks) {
    const sorted_tracks = tracks.map(track => {
        const { name, artists, playcount } = track;
        return {
            name,
            artists: artists.map(artist => artist.name),
            playcount,
        };
    })
        .sort((a, b) => b.playcount - a.playcount);

    const most_streamed_tracks = sorted_tracks.slice(0, MAX_TOP_SONGS);
    const least_streamed_tracks = sorted_tracks.slice(-MAX_TOP_SONGS).reverse();

    return [most_streamed_tracks, least_streamed_tracks];
}


async function agregate_popularity(tracks) {
    const sorted_tracks = tracks.map(track => {
        const { name, artists, popularity, playcount } = track;
        return {
            name,
            artists: artists.map(artist => artist.name),
            popularity,
            playcount,
        };
    })
        .sort((a, b) => {
            if (b.popularity !== a.popularity) {
                return b.popularity - a.popularity;
            }
            return b.playcount - a.playcount;
        });

    const most_popular_tracks = sorted_tracks.slice(0, MAX_TOP_SONGS);
    const least_popular_tracks = sorted_tracks.slice(-MAX_TOP_SONGS).reverse();

    return [most_popular_tracks, least_popular_tracks];
}


async function agregate_lenght(tracks) {
    const sorted_tracks = tracks.map(track => {
        const { name, artists, duration } = track;
        return {
            name,
            artists: artists.map(artist => artist.name),
            duration,
        };
    })
        .sort((a, b) => b.duration - a.duration);

    const most_long_tracks = sorted_tracks.slice(0, MAX_TOP_SONGS);
    const most_short_tracks = sorted_tracks.slice(-MAX_TOP_SONGS).reverse();

    return [most_long_tracks, most_short_tracks];
}


async function agregate_periods(tracks) {
    let year_count = {};
    let month_count = {};

    tracks.forEach(track => {
        const { release_date, release_date_precision } = track;
        if (release_date_precision === "year") {
            year_count[release_date] = (year_count[release_date] || 0) + 1;
        }
        else {
            const releasedYear = release_date.split("-")[0];
            const releasedMonth = release_date.split("-")[1];
            year_count[releasedYear] = (year_count[releasedYear] || 0) + 1;
            month_count[releasedMonth] = (month_count[releasedMonth] || 0) + 1;
        }
    });

    return [year_count, month_count];
}



async function generate_report(playlistFile, outputReportFile) {
    const playlist = JSON.parse(fs.readFileSync(playlistFile, 'utf-8'));
    const tracks = playlist.items;

    const [
        [total_tracks, total_artists, total_streams],
        [artists_counts, artists_playcounts, artists_lenght],
        [oldest_tracks, newest_tracks],
        [most_streamed_tracks, least_streamed_tracks],
        [most_popular_tracks, least_popular_tracks],
        [most_long_tracks, most_short_tracks],
        [year_count, month_count],
    ] = await Promise.all([
        agregate_general(tracks),
        agregate_artists(tracks),
        agregate_dates(tracks),
        agregate_playcount(tracks),
        agregate_popularity(tracks),
        agregate_lenght(tracks),
        agregate_periods(tracks),
    ]);

    const final_report = {
        total_tracks,
        total_artists,
        total_streams,
        artists_counts,
        artists_playcounts,
        artists_lenght,
        oldest_tracks,
        newest_tracks,
        most_streamed_tracks,
        least_streamed_tracks,
        most_popular_tracks,
        least_popular_tracks,
        most_long_tracks,
        most_short_tracks,
        year_count,
        month_count,
    };

    fs.writeFileSync(outputReportFile, JSON.stringify(final_report, null, 4), 'utf-8');
}




module.exports = { generate_report };