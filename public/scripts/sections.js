// New entries
const new_entries_date = document.querySelector(".new-entries-date");
const new_entries_section = document.querySelector("#new-entries");

// Trendings
const trendings_section = document.querySelector("#trendings");

// Newest
const newest_section = document.querySelector("#newest");

// Most streamed
const most_streamed_section = document.querySelector("#most-streamed");

// Least streamed
const least_streamed_section = document.querySelector("#least-streamed");

// Most long
const most_long_section = document.querySelector("#most-long");

// Most Short
const most_short_section = document.querySelector("#most-short");



function format_milliseconds(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = seconds % 60;
    return `${minutes}:${remaining_seconds.toString().padStart(2, '0')}`;
}


function create_music_card(track, position, additionalInfo="") {
    const trackName = track.name.replace(/\([^)]*\)/g, "").trim()
    const music_card = document.createElement("div");
    music_card.classList.add("music-card");
    music_card.classList.add("item");
    music_card.style.setProperty("--position", position);
    
    // Generate artists links
    const artistsLinks = track.artists
        .map(artist => `<a class="cta-link" href="https://open.spotify.com/artist/${artist.id}" target="_blank">${artist.name}</a>`)
        .join(", ");

    const additionalInfoDiv = additionalInfo === "" ? "" : `<div class="music-infos">${additionalInfo}</div>`;

    music_card.innerHTML = `
    <a href="https://open.spotify.com/track/${track.id}" target="_blank">
        <img src="${track.image}" alt="${trackName}">
    </a>
    <div class="music-card-content">
        <div class="music-title">
            <a class="cta-link" href="https://open.spotify.com/track/${track.id}" target="_blank">${trackName}</a>
        </div>
        <div class="music-artist">
            ${artistsLinks}
        </div>
    </div>
    ${additionalInfoDiv}
    `;
    return music_card;
}


function update_new_entries(report) {
    let lastEntryDate = "";
    let cardColor = 0;
    for (let i = 0; i < report.newest_billions.length; i++) {
        const entry = report.newest_billions[i];
        if (lastEntryDate === "") {
            // Update the date of the last entries
            lastEntryDate = entry.added_at;
            new_entries_date.textContent = new Date(lastEntryDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
        }
        else if (lastEntryDate !== entry.added_at) {
            cardColor = (cardColor + 1) % 2;
            lastEntryDate = entry.added_at;
            // break; // Only if display the last entries
        }

        const new_entry = create_music_card(entry, i+1, `Entry<br>${entry.added_at}`);
        if (cardColor) { new_entry.classList.add(`card-color-${cardColor}`); }
        new_entries_section.appendChild(new_entry);
    }
}


async function update_trendings(report) {
    for (let i = 0; i < report.most_popular_tracks.length; i++) {
        const trending = report.most_popular_tracks[i];
        const trending_entry = create_music_card(trending, i+1, `Popularity<br>${trending.popularity}`);
        trendings_section.appendChild(trending_entry);
    }
}


async function update_newest(report) {
    for (let i = 0; i < report.newest_tracks.length; i++) {
        const newest = report.newest_tracks[i];
        const newest_entry = create_music_card(newest, i+1, `Release<br>${newest.release_date}`);
        newest_section.appendChild(newest_entry);
    }
}


async function update_most_streamed(report) {
    for (let i = 0; i < report.most_streamed_tracks.length; i++) {
        const track = report.most_streamed_tracks[i];
        const track_entry = create_music_card(track, i+1, `Streams<br>${(track.playcount/1_000_000_000).toFixed(2)}B`);
        most_streamed_section.appendChild(track_entry);
    }
}


async function update_least_streamed(report) {
    for (let i = 0; i < report.least_streamed_tracks.length; i++) {
        const track = report.least_streamed_tracks[i];
        const track_entry = create_music_card(track, i+1, `Streams<br>${(track.playcount/1_000_000_000).toFixed(4)}B`);
        least_streamed_section.appendChild(track_entry);
    }
}


async function update_most_long(report) {
    for (let i = 0; i < report.most_long_tracks.length; i++) {
        const track = report.most_long_tracks[i];
        const track_entry = create_music_card(track, i+1, `Duration<br>${format_milliseconds(track.duration_ms)}`);
        most_long_section.appendChild(track_entry);
    }
}


async function update_most_short(report) {
    for (let i = 0; i < report.most_short_tracks.length; i++) {
        const track = report.most_short_tracks[i];
        const track_entry = create_music_card(track, i+1, `Duration<br>${format_milliseconds(track.duration_ms)}`);
        most_short_section.appendChild(track_entry);
    }
}