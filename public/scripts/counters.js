// Counters
const steams_counter = document.querySelector("#total-streams");
const artists_counter = document.querySelector("#total-artists");
const tracks_counter = document.querySelector("#total-tracks");




function createOdometer(el, value) {
    const odometer = new Odometer({
        el: el,
        value: 0,
    });

    odometer.update(value);
}


function update_counters(report) {
    createOdometer(steams_counter, Math.round(report.total_streams / 1_000_000_000));
    createOdometer(artists_counter, report.total_artists);
    createOdometer(tracks_counter, report.total_tracks);
}