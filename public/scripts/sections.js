const pills_containers = document.querySelectorAll(".pill-container");
const pill_tracks = document.querySelector("#pills-tracks");
const pill_artists = document.querySelector("#pills-artists");
const pills_graphs = document.querySelector("#pills-graphs");

// New entries
const new_entries_date = document.querySelector(".new-entries-date");
const new_entries_section = document.querySelector("#new-entries");
const fastest_section = document.querySelector("#fastest-tracks");

// Trendings
const trendings_section = document.querySelector("#trending-tracks");

// Date
const newest_section = document.querySelector("#newest-tracks");
const oldest_section = document.querySelector("#oldest-tracks");

// Number of streams
const most_streamed_section = document.querySelector("#most-streamed");
const least_streamed_section = document.querySelector("#least-streamed");

// Track duration
const most_long_section = document.querySelector("#most-long");
const most_short_section = document.querySelector("#most-short");



function format_milliseconds(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = seconds % 60;
    return `${minutes}:${remaining_seconds.toString().padStart(2, '0')}`;
}


function create_music_card(track, position, additionalInfo = "") {
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
        const nb_days_ago = Math.floor((new Date() - new Date(entry.added_at)) / (1000 * 60 * 60 * 24));
        const new_entry = create_music_card(entry, i + 1, `Added<br>${nb_days_ago} days ago`);
        if (cardColor) { new_entry.classList.add(`card-color-${cardColor}`); }
        new_entries_section.appendChild(new_entry);
    }
}


async function display_pill_section(sections, all_pills, active_pill, scrollToTop = false) {
    all_pills.forEach(p => p.classList.remove("active"));
    active_pill.classList.add("active");

    const target = active_pill.getAttribute("data-target");

    sections.forEach(section => {
        section.style.display = section.id === target ? "block" : "none";
    });

    // Scroll to the top of the pill section + 10px
    if (scrollToTop) {
        const targetSection = document.getElementById(target);
        const targetSectionTop = targetSection.getBoundingClientRect().top + window.scrollY - 150; // 15px for padding
        window.scrollTo({
            top: targetSectionTop,
            behavior: "smooth"
        });
    }
}


async function update_pills() {

    // for tracks, artists and graph sections
    pills_containers.forEach(pills_container => {
        // Get the sections that needs to be in the pills
        const sectionName = pills_container.id.replace("pills-", "");
        const all_sections = document.querySelectorAll(`.section-${sectionName}`);

        // Create a pill for all sections
        let isFirstPill = true;
        let firstPill = null;
        all_sections.forEach(section => {
            const pill = document.createElement("div");
            pill.classList.add("pill");
            pill.classList.add(`pill-${sectionName}`);
            if (isFirstPill) {
                firstPill = pill;
                isFirstPill = false;
            }
            pill.setAttribute("data-target", section.id);
            let sectionText = section.firstElementChild.textContent;
            sectionText = sectionText.replace(/:/g, "").replace(/"/g, "");
            pill.textContent = sectionText;
            pills_container.appendChild(pill);
        });
    
        const all_pills = document.querySelectorAll(`.pill-${sectionName}`);
        // Add first item after 1s to let the page load
        setTimeout(() => {
            firstPill.classList.add("active");
            display_pill_section(all_sections, all_pills, firstPill, scrollToTop = false);
        }, 1000);
    
        // Add event listeners to all pills
        all_pills.forEach(pill => {
            pill.addEventListener("click", function () {
                display_pill_section(all_sections, all_pills, this);
            });
        });
    });
}


async function update_trendings(report) {
    for (let i = 0; i < report.most_popular_tracks.length; i++) {
        const trending = report.most_popular_tracks[i];
        const trending_entry = create_music_card(trending, i + 1, `Popularity<br>${trending.popularity}`);
        trendings_section.appendChild(trending_entry);
    }
}


async function update_newest(report) {
    for (let i = 0; i < report.newest_tracks.length; i++) {
        const track = report.newest_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Release<br>${track.release_date}`);
        newest_section.appendChild(track_entry);
    }
}


async function update_oldest(report) {
    for (let i = 0; i < report.oldest_tracks.length; i++) {
        const track = report.oldest_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Release<br>${track.release_date}`);
        oldest_section.appendChild(track_entry);
    }
}


async function update_fastest(report) {
    for (let i = 0; i < report.fastest_billions.length; i++) {
        const track = report.fastest_billions[i];
        const track_entry = create_music_card(track, i + 1, `Days took<br>${track.billion_time}`);
        fastest_section.appendChild(track_entry);
    }
}


async function update_most_streamed(report) {
    for (let i = 0; i < report.most_streamed_tracks.length; i++) {
        const track = report.most_streamed_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Streams<br>${(track.playcount / 1_000_000_000).toFixed(2)}B`);
        most_streamed_section.appendChild(track_entry);
    }
}


async function update_least_streamed(report) {
    for (let i = 0; i < report.least_streamed_tracks.length; i++) {
        const track = report.least_streamed_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Streams<br>${(track.playcount / 1_000_000_000).toFixed(4)}B`);
        least_streamed_section.appendChild(track_entry);
    }
}


async function update_most_long(report) {
    for (let i = 0; i < report.most_long_tracks.length; i++) {
        const track = report.most_long_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Duration<br>${format_milliseconds(track.duration_ms)}`);
        most_long_section.appendChild(track_entry);
    }
}


async function update_most_short(report) {
    for (let i = 0; i < report.most_short_tracks.length; i++) {
        const track = report.most_short_tracks[i];
        const track_entry = create_music_card(track, i + 1, `Duration<br>${format_milliseconds(track.duration_ms)}`);
        most_short_section.appendChild(track_entry);
    }
}