const div_title = document.querySelector(".title");

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
        const textWidth = el.scrollWidth;
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




div_title.addEventListener("click", toggle_all_details);

async function main() {
    const report = await get_report("data/report.json");
    await Promise.all([
        update_counters(report),
        update_playlist_infos(report),
        update_new_entries(report),
        update_trendings(report),
        update_newest(report),
        update_most_streamed(report),
        update_least_streamed(report),
        update_most_long(report),
        update_most_short(report),
        place_arrow()
    ]);
    
    // await all
    add_scrolling_cards();
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
