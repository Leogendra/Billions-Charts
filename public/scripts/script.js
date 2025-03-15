const div_title = document.querySelector(".title");

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
    });
    odometer.update(value);
}


function update_counters(report) {
    createOdometer(steams_counter, Math.round(report.total_streams / 1_000_000_000), "B");
    createOdometer(artists_counter, report.total_artists);
    createOdometer(tracks_counter, report.total_tracks);
}


function update_playlist_infos(report) {
    // last update date
    let lastUpdateDate = new Date(report.generatedTimeStamp);
    lastUpdateDate = lastUpdateDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    update_date_global.textContent = lastUpdateDate;

    // playlist image and description
    playlist_cover.src = report.coverUrl;
    playlist_description.textContent = report.description.replace(/<[^>]*>|{[^}]*}/g, '');
    cover_container.style.boxShadow = report.coverHex;
}


function add_scrolling_cards() {
    document.querySelectorAll(".music-title, .music-artist").forEach(el => {
        const container = el.parentElement;
        const textWidth = el.scrollWidth + 10; // Add margin to not cut the text in the shadow
        const containerWidth = container.clientWidth;

        if (textWidth > containerWidth) {
            const scrollDistance = textWidth - containerWidth + 10; // Add a little margin
            el.style.setProperty("--scroll-distance", `${scrollDistance}px`);
            el.classList.add("auto-scroll");
        }
    });
}


async function toggle_all_details() {
    all_details_open = !all_details_open;
    details_sections.forEach(details => {
        details.open = all_details_open;
    });
}


function display_artists_bars(artists_infos, containerId) {
    const maxStreams = Math.max(...artists_infos.map(artists_infos => artists_infos.data));
    const container = document.getElementById(containerId);

    const minWidth = 250; // Min width in pixels
    const maxWidth = 100; // Max width in percentage

    artists_infos.forEach(artist => {
        const bar = document.createElement("div");
        bar.classList.add("bar-artist");

        let calculatedWidth = (artist.data / maxStreams) * maxWidth;
        let finalWidth = Math.max(calculatedWidth, (minWidth / container.offsetWidth) * 100); // Convert minWidth to percentage

        bar.style.width = `${finalWidth}%`;

        const text = document.createElement("span");
        text.innerHTML = `<a class="cta-link" href="${artist.url}" target="_blank">${artist.name}</a> (${artist.data_dislay})`;
        bar.appendChild(text);

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

    // Fake data
    // artists.push({
    //     name: "Ariana Grande (fake)",
    //     data: 1_000_000_000,
    //     url: `https://open.spotify.com/`,
    //     image: "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae",
    // });

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




div_title.addEventListener("click", toggle_all_details);

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
        update_artists_most_time(report),

        // Charts sections
        create_histogram_month(report),
        create_histogram_year(report),
    ]);
    
    await Promise.all([
        add_scrolling_cards(),
        place_arrow(),
    ]);

    update_pills(),
    get_key_features(report);
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
