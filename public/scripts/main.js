// Counters
const steams_counter = document.querySelector("#total-streams");
const artists_counter = document.querySelector("#total-artists");
const tracks_counter = document.querySelector("#total-tracks");

// Playlist image and description
const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const update_date_global = document.querySelector(".update-date");
const cover_container = document.querySelector(".cover-container");

// Details sections
const details_sections = document.querySelectorAll("details");
let all_details_open = true;




async function get_report(reportPath) {
    try {
        const response = await fetch(reportPath);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    }
    catch (error) {
        console.error('Erreur lors du chargement du JSON:', error);
    }
}


function createOdometer(el, value, suffix="") {
    const odometer = new Odometer({
        el: el,
        value: 0,
        suffix: suffix,
        format: '(ddd).dd',
    });
    odometer.update(value);
}


function update_counters(report) {
    createOdometer(steams_counter, Math.round(report.total_streams / 1_000_000_000), suffix="B");
    createOdometer(artists_counter, report.total_artists);
    createOdometer(tracks_counter, report.total_tracks);
}


function update_playlist_infos(report) {
    // last update date
    let lastUpdateDate = new Date(report.generatedTimeStamp);
    lastUpdateDate = lastUpdateDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    update_date_global.textContent = lastUpdateDate;

    // playlist image and description
    const playlist_cover = document.createElement("img");
    playlist_cover.src = report.coverUrl;
    playlist_cover.id = "playlist-cover";
    playlist_cover.alt = "Playlist Cover";

    cover_container.appendChild(playlist_cover);
    cover_container.style.boxShadow = report.coverHex;
    playlist_description.textContent = report.description.replace(/<[^>]*>|{[^}]*}/g, '');
}


function add_scrolling_cards() {
    async function check_scrolling(el, margin=0) {
        const container = el.parentElement;
        const textWidth = el.scrollWidth + margin; // Add margin to not cut the text in the shadow
        const containerWidth = container.clientWidth;

        if (textWidth > containerWidth) {
            const scrollDistance = textWidth - containerWidth + 10; // Add a little margin
            el.style.setProperty("--scroll-distance", `${scrollDistance}px`);
            el.classList.add("auto-scroll");
        }
    }
    document.querySelectorAll(".music-title, .music-artist").forEach(el => {
        check_scrolling(el, 10);
    });
    document.querySelectorAll(".bar-artist-text").forEach(el => {
        check_scrolling(el, 0);
    });
}


function display_artists_bars(artists_infos, containerId) {
    const maxStreams = Math.max(...artists_infos.map(artists_infos => artists_infos.data));
    const container = document.getElementById(containerId);

    // Width in percentage
    const basePx = window.matchMedia("(max-width: 800px)").matches ? 190 : 270;
    const minWidth = (basePx / container.offsetWidth) * 100;
    const maxWidth = 100; 

    const minItemValue = Math.min(...artists_infos.map(artist => artist.data));
    const maxItemValue = Math.max(...artists_infos.map(artist => artist.data));

    artists_infos.forEach(artist => {

        // Ratio between min and max
        const ratio = (artist.data - minItemValue) / (maxItemValue - minItemValue);
        const finalWidth = minWidth + (maxWidth - minWidth) * ratio;
        
        const bar = document.createElement("div");
        bar.classList.add("bar-artist");
        bar.style.width = `${finalWidth}%`;
        
        const barContent = document.createElement("div");
        barContent.classList.add("bar-artist-content");
        bar.appendChild(barContent);

        const divArtistName = document.createElement("div");
        divArtistName.classList.add("bar-artist-text");
        divArtistName.innerHTML = `<a class="cta-link" href="${artist.url}" target="_blank">${artist.name}</a>&nbsp;(${artist.data_dislay})`;
        barContent.appendChild(divArtistName);

        const img = document.createElement("img");
        img.src = artist.image;
        img.classList.add("bar-artist-image");
        bar.appendChild(img);

        container.appendChild(bar);
    });
}


async function update_artists_most_streamed(report) {
    const artists = [];
    report.artists_playcounts.forEach(artist => {
        artists.push({
            name: artist[0],
            data: artist[1],
            data_dislay: `${(artist[1]/1_000_000_000).toFixed(2)}B`,
            url: `https://open.spotify.com/artist/${artist[2]}`,
            image: artist[3]
        });
    });

    display_artists_bars(artists, "artists-most-streamed");
}


async function update_artists_most_songs(report) {
    const artists = [];
    report.artists_counts.forEach(artist => {
        artists.push({
            name: artist[0],
            data: artist[1],
            data_dislay: artist[1],
            url: `https://open.spotify.com/artist/${artist[2]}`,
            image: artist[3]
        });
    });
    display_artists_bars(artists, "artists-most-songs");
}


async function update_artists_most_popular(report) {
    const artists = [];
    report.artists_popularity.forEach(artist => {
        artists.push({
            name: artist[0],
            data: artist[1],
            data_dislay: artist[1],
            url: `https://open.spotify.com/artist/${artist[2]}`,
            image: artist[3]
        });
    });
    display_artists_bars(artists, "artists-most-popular");
}


async function update_artists_most_time(report) {
    const artists = [];
    report.artists_length.forEach(artist => {
        artists.push({
            name: artist[0],
            data: artist[1],
            data_dislay: `${String(Math.floor(artist[1] / 60000)).padStart(2, '0')}:${String(Math.floor((artist[1] % 60000) / 1000)).padStart(2, '0')}`,
            url: `https://open.spotify.com/artist/${artist[2]}`,
            image: artist[3]
        });
    });
    display_artists_bars(artists, "artists-most-time");
}




async function main() {
    const report = await get_report("data/report.json");
    await Promise.all([
        update_counters(report),
        update_playlist_infos(report),

        // Tracks sections
        update_new_entries(report),
        update_trendings(report),
        update_newest(report),
        update_oldest(report),
        update_fastest(report),
        update_most_streamed(report),
        update_least_streamed(report),
        update_most_long(report),
        update_most_short(report),

        // Artists sections
        update_artists_most_streamed(report),
        update_artists_most_songs(report),
        update_artists_most_popular(report),
        update_artists_most_time(report),

        // Charts sections
        create_histogram_release_month(report),
        create_histogram_release_year(report),
        create_histogram_billion_month(report),
        create_histogram_billion_year(report),
        create_histogram_streams_count(report),
        create_histogram_track_count(report),
        create_histogram_time_count(report),
        create_histogram_featuring(report),
    ]);
    
    await Promise.all([
        get_key_features(report),
        add_scrolling_cards(),
        place_arrow(),
    ]);

    update_pills();
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
