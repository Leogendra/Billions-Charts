// Playlist image and description
const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const update_date_global = document.querySelector(".update-date");
const cover_container = document.querySelector(".cover-container");

// New entries
const new_entries_date = document.querySelector(".new-entries-date");
const new_entries_section = document.querySelector("#new-entries");

// Trendings
const trendings_section = document.querySelector("#trendings");


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



function create_music_card(track) {
    const trackName = track.name.replace(/\([^)]*\)/g, "").trim()
    const music_card = document.createElement("div");
    music_card.classList.add("music-card");
    let artists = track.artists;
    // check if artists type are string or dict
    if (typeof artists[0] === "object") {
        artists = artists.map(artist => artist.name);
    }
    music_card.innerHTML = `
    <a href="https://open.spotify.com/track/${track.id}" target="_blank">
        <img src="${track.image}" alt="${trackName}">
    </a>
    <div class="music-card-content">
        <div class="music-title">${trackName}</div>
        <div class="music-artist">${artists.join(", ")}</div>
    </div>
    `;
    return music_card;
}


function update_new_entries(report) {
    let last_entry_date = "";
    for (const entry of report.newest_billions) {
        if (last_entry_date === "") {
            // Update the date of the last entries
            last_entry_date = entry.added_at;
            new_entries_date.textContent = new Date(last_entry_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
        }
        else if (last_entry_date !== entry.added_at) {
            break;
        }

        const new_entry = create_music_card(entry);
        new_entries_section.appendChild(new_entry);
    }
}


async function update_trendings(report) {
    for (const trending of report.most_popular_tracks) {
        const trending_entry = create_music_card(trending);
        trendings_section.appendChild(trending_entry);
    }
}



async function main() {
    const report = await get_report("data/report.json");
    update_counters(report);
    update_playlist_infos(report);
    update_new_entries(report);
    update_trendings(report);

    place_arrow();
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
