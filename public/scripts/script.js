// Playlist image and description
const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const update_date = document.querySelector(".update-date");
const cover_container = document.querySelector(".cover-container");

const new_entries_section = document.querySelector("#new-entries");




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
    update_date.textContent = lastUpdateDate;

    // playlist image and description
    playlist_cover.src = report.coverUrl;
    playlist_description.textContent = report.description.replace(/<[^>]*>|{[^}]*}/g, '');
    cover_container.style.boxShadow = report.coverHex;
}


function update_new_entries(report) {
    let last_entry_date = "";
    for (const entry of report.newest_billions) {
        if (last_entry_date === "") {
            last_entry_date = entry.added_at;
        }
        else if (last_entry_date !== entry.added_at) {
            break;
        }

        const trackName = entry.name.replace(/\([^)]*\)/g, "").trim()
        const new_entry = document.createElement("div");
        new_entry.classList.add("counter-container");
        new_entry.classList.add("new-entries-container");
        new_entry.innerHTML = `
         <img src="${entry.image}" alt="${trackName}" id="new-cover">
         <h2 class="new-entry-name limited-text-3"><a href="https://open.spotify.com/track/${entry.id}" target="_blank">${trackName}</a></h2>
        <h2 class="new-entry-artists limited-text-2">by ${entry.artists.join(", ")}</h2>
         `;
        new_entries_section.appendChild(new_entry);
    }
}




async function main() {
    const report = await get_report("data/report.json");
    update_counters(report);
    update_playlist_infos(report);
    update_new_entries(report);
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
