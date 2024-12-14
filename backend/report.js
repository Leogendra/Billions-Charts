const fs = require('fs');

const MAX_TOP_SONGS = 10;




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

    return [artists_count_array, artists_playcount_array];
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
                                .sort((a, b) => b.duration - a.duration );
    
    const most_long_tracks = sorted_tracks.slice(0, MAX_TOP_SONGS);
    const most_short_tracks = sorted_tracks.slice(-MAX_TOP_SONGS).reverse();

    return [most_long_tracks, most_short_tracks];
}



async function generate_report(playlistFile, outputReportFile) {
    const playlist = JSON.parse(fs.readFileSync(playlistFile, 'utf-8'));
    const tracks = playlist.items;

    const [artists_counts, artists_playcounts] = await agregate_artists(tracks);
    const [oldest_tracks, newest_tracks] = await agregate_dates(tracks);
    const [most_streamed_tracks, least_streamed_tracks] = await agregate_playcount(tracks);
    const [most_popular_tracks, least_popular_tracks] = await agregate_popularity(tracks);
    const [most_long_tracks, most_short_tracks] = await agregate_lenght(tracks);

    final_report = {
        total_tracks: tracks.length,
        total_artists: artists_counts.length,
        total_streams: tracks.reduce((acc, track) => acc + track.playcount, 0),
        artists_counts: artists_counts,
        artists_playcounts: artists_playcounts,
        oldest_tracks: oldest_tracks,
        newest_tracks: newest_tracks,
        most_streamed_tracks: most_streamed_tracks,
        least_streamed_tracks: least_streamed_tracks,
        most_popular_tracks: most_popular_tracks,
        least_popular_tracks: least_popular_tracks,
        most_long_tracks: most_long_tracks,
        most_short_tracks: most_short_tracks,
    }

    fs.writeFileSync(outputReportFile, JSON.stringify(final_report, null, 4), 'utf-8');
}




module.exports = { generate_report };