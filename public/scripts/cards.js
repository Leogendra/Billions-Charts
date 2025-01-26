// New entries
const new_entries_date = document.querySelector(".new-entries-date");
const new_entries_section = document.querySelector("#new-entries");

// Trendings
const trendings_section = document.querySelector("#trendings");




function create_music_card(track, position, additionalInfo="") {
    const trackName = track.name.replace(/\([^)]*\)/g, "").trim()
    const music_card = document.createElement("div");
    music_card.classList.add("music-card");
    music_card.classList.add("item");
    music_card.style.setProperty("--position", position);
    
    // Generate artists links
    const artistsLinks = track.artists
        .map(artist => `<a href="https://open.spotify.com/artist/${artist.id}" target="_blank">${artist.name}</a>`)
        .join(", ");

    const additionalInfoDiv = additionalInfo === "" ? "" : `<div class="music-infos">${additionalInfo}</div>`;

    music_card.innerHTML = `
    <a href="https://open.spotify.com/track/${track.id}" target="_blank">
        <img src="${track.image}" alt="${trackName}">
    </a>
    <div class="music-card-content">
        <div class="music-title">
            <a href="https://open.spotify.com/track/${track.id}" target="_blank">${trackName}</a>
        </div>
        <div class="music-artist">
            ${artistsLinks}
        </div>
        ${additionalInfoDiv}
    </div>
    `;
    return music_card;
}


function update_new_entries(report) {
    let last_entry_date = "";
    for (let i = 0; i < report.newest_billions.length; i++) {
        const entry = report.newest_billions[i];
        if (last_entry_date === "") {
            // Update the date of the last entries
            last_entry_date = entry.added_at;
            new_entries_date.textContent = new Date(last_entry_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
        }
        else if (last_entry_date !== entry.added_at) {
            break;
        }

        const new_entry = create_music_card(entry, i+1);
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