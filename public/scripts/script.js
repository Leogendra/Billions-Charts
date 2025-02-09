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


async function display_artists() {
    const artists = [
        { name: "The Weeknd", streams: 12000_000, image: "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae" },
        { name: "Taylor Swift", streams: 100_000, image: "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae" },
        { name: "Drake", streams: 80000, image: "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae" },
        { name: "Ariana Grande", streams: 100, image: "https://i.scdn.co/image/ab6761610000e5eb9e528993a2820267b97f6aae" },
    ];

    const maxStreams = Math.max(...artists.map(artist => artist.streams)); // Trouve le plus grand nombre de streams
    const container = document.getElementById("bar-container");

    // Largeurs min et max
    const minWidth = 120; // Largeur minimale pour les petites valeurs
    const maxWidth = 100; // Largeur max en pourcentage du conteneur

    // Génération dynamique des barres
    artists.forEach(artist => {
        const bar = document.createElement("div");
        bar.classList.add("bar");

        // Calcule la largeur proportionnelle avec un minimum
        let calculatedWidth = (artist.streams / maxStreams) * maxWidth;
        let finalWidth = Math.max(calculatedWidth, (minWidth / container.offsetWidth) * 100); // Min 120px converti en %

        bar.style.width = `${finalWidth}%`;

        const text = document.createElement("span");
        text.textContent = artist.name;
        bar.appendChild(text);

        const img = document.createElement("img");
        img.src = artist.image;
        img.classList.add("artist-image");
        bar.appendChild(img);

        container.appendChild(bar);
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
        update_oldest(report),
        update_most_streamed(report),
        update_least_streamed(report),
        update_most_long(report),
        update_most_short(report),
        place_arrow()
    ]);

    // await all
    add_scrolling_cards();

    // display_artists();

    // POC
    const songs = [
        { name: "Have you ever see the rain", date: "1971-01-05" }
    ];
    report.oldest_tracks.forEach(song => {
        songs.push({ name: song.name, date: song.release_date });
    });
    report.newest_tracks.forEach(song => {
        songs.push({ name: song.name, date: song.release_date });
    });

    const dataPoints = songs.map(song => {
        const date = new Date(song.date);
        const year = date.getFullYear();
        const dayOfYear = (Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) - Date.UTC(date.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24);
        return { x: year, y: dayOfYear };
    });

    const ctx = document.getElementById('scatterChart').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Songs',
                data: dataPoints,
                backgroundColor: 'rgba(148, 75, 211, 0.8)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: { display: true, text: 'Year of release' },
                    ticks: {
                        callback: (val) => parseInt(val)
                    }
                },
                y: {
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const song = songs[context.dataIndex];
                            return `${song.name} - ${song.date}`;
                        }
                    }
                }
            }
        }
    });
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
