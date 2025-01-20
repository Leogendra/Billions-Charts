const playlist_cover = document.querySelector("#playlist-cover");
const playlist_description = document.querySelector("#playlist-description");

const steams_counter = document.querySelector("#total-streams");
const artists_counter = document.querySelector("#total-artists");
const tracks_counter = document.querySelector("#total-tracks");




function format_numbers(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "'");
}



function createOdometer(el, value) {
    const odometer = new Odometer({
        el: el,
        value: 0,
    });

    odometer.update(value);
}



async function main() {
    const report = await get_report("data/report.json");

    createOdometer(steams_counter, Math.round(report.total_streams / 1_000_000_000));
    createOdometer(artists_counter, report.total_artists);
    createOdometer(tracks_counter, report.total_tracks);

    playlist_cover.src = report.coverUrl;
    playlist_description.textContent = report.description.replace(/<[^>]*>|{[^}]*}/g, '');
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
