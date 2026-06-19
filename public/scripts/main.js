// Counters
const steams_counter = document.querySelector("#total-streams");
const artists_counter = document.querySelector("#total-artists");
const tracks_counter = document.querySelector("#total-tracks");

// Playlist image and description
const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const update_date_global = document.querySelector(".update-date");
const cover_container = document.querySelector(".cover-container");

// What's new section
const whats_new_section = document.getElementById("whats-new-section");
const whats_new_toggle = document.getElementById("whats-new-toggle");


const IS_MOBILE = window.innerWidth <= 800;




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
        format: "( ddd).dd",
    });
    odometer.update(value);
}


function update_counters(report) {
    createOdometer(tracks_counter, report.total_tracks);
    createOdometer(steams_counter, Math.round(report.total_streams / 1_000_000_000), suffix="B");
    createOdometer(artists_counter, report.total_artists);
}


function update_playlist_infos(report) {
    // last update date
    let lastUpdateDate = new Date(report.generatedTimeStamp);
    lastUpdateDate = lastUpdateDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    update_date_global.textContent = lastUpdateDate;

    // playlist image and description
    playlist_cover.src = report.coverUrl;
    cover_container.style.boxShadow = report.coverHex;
    playlist_description.textContent = report.description.replace(/<[^>]*>|{[^}]*}/g, '');
    cover_container.onclick = () => open_popup_card_image_zoom(report.coverUrl);
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
        bar.addEventListener("click", (e) => {
            if (!e.target.closest("a") && !e.target.closest(".bar-artist-image")) fetch_and_display_artist_card(artist.id);
        });

        const barContent = document.createElement("div");
        barContent.classList.add("bar-artist-content");
        bar.appendChild(barContent);

        const divArtistName = document.createElement("div");
        divArtistName.classList.add("bar-artist-text");
        divArtistName.innerHTML = `<a class="cta-link" href="#" onclick="event.preventDefault(); fetch_and_display_artist_card('${artist.id}')">${artist.name}</a>&nbsp;(${artist.data_dislay})`;
        barContent.appendChild(divArtistName);

        const img = document.createElement("img");
        img.src = artist.image;
        img.classList.add("bar-artist-image");
        img.addEventListener("click", (e) => {
            e.stopPropagation();
            open_popup_card_image_zoom(artist.image);
        });
        bar.appendChild(img);

        container.appendChild(bar);
    });
}


async function update_artists_most_streamed(report) {
    const artists = [];
    report.artists_playcounts.forEach(artist => {
        artists.push({
            id: artist[2],
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
            id: artist[2],
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
            id: artist[2],
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
            id: artist[2],
            name: artist[0],
            data: artist[1],
            data_dislay: `${String(Math.floor(artist[1] / 60000)).padStart(2, '0')}:${String(Math.floor((artist[1] % 60000) / 1000)).padStart(2, '0')}`,
            url: `https://open.spotify.com/artist/${artist[2]}`,
            image: artist[3]
        });
    });
    display_artists_bars(artists, "artists-most-time");
}


function init_whats_new() {
    if (!whats_new_section || !whats_new_toggle) { return; }

    if (localStorage.getItem("billions_charts_whats_new_collapsed") === "1") {
        whats_new_section.classList.add("collapsed");
    }

    whats_new_toggle.addEventListener("click", () => {
        const isCollapsed = whats_new_section.classList.toggle("collapsed");
        if (isCollapsed) {
            localStorage.setItem("billions_charts_whats_new_collapsed", "1");
        } 
        else {
            localStorage.removeItem("billions_charts_whats_new_collapsed");
        }
    });
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
        update_streams_per_day(report),

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
    init_search();
    init_whats_new();
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
