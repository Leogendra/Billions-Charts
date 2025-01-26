// Playlist image and description
const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const update_date_global = document.querySelector(".update-date");
const cover_container = document.querySelector(".cover-container");


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



async function main() {
    const report = await get_report("data/report.json");
    update_counters(report);
    update_playlist_infos(report);
    update_new_entries(report);
    update_trendings(report);

    place_arrow();

    // Caroussel
    // window.addEventListener("mousemove", handleMouseMove);
    // window.addEventListener("mousedown", handleMouseDown);
    // window.addEventListener("mouseup", handleMouseUp);
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
