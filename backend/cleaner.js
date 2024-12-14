const fs = require('fs');




async function clean_playlist(tracksRaw, cleanedTracks) {
    let playlist = JSON.parse(fs.readFileSync(tracksRaw, 'utf-8'));
    
    const tracks = playlist.items;
    const cleaned = tracks
                    .filter(track => (track.playcount) && (track.playcount > 999_999_999))
                    .map(track => {
                        return {
                            name: track.name,
                            artists: track.artists.map(artist => {
                                return {
                                    name: artist.name,
                                    id: artist.id,
                                }
                            }),
                            release_date: track.album.release_date,
                            release_date_precision: track.album.release_date_precision,
                            duration: track.duration_ms,
                            image: track.album.images[0].url,
                            popularity: track.popularity,
                            playcount: track.playcount,
                            duration_ms: track.duration_ms,
                            spotify_url: track.external_urls.spotify,
                            id: track.id,
                        }
                    });

    playlist.items = cleaned;
    if (playlist.total == cleaned.length) {
        console.log("Playlist fully cleaned.");
        fs.unlinkSync(tracksRaw);
    }
    playlist.total = cleaned.length;
    fs.writeFileSync(cleanedTracks, JSON.stringify(playlist, null, 4), 'utf-8');
    console.log(`Playlist cleaned and saved in ${cleanedTracks}`);
}




module.exports = { clean_playlist };