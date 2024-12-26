async function animateCounter(id, targetValue, duration, addString = "") {
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with id '${id}' not found.`);
        return;
    }

    let startValue = 0;
    let startTime = null;

    function easeOut(x) {
        return Math.sin((x * Math.PI) / 2);
    }

    function updateCounter(timestamp) {
        if (!startTime) startTime = timestamp;
        const elapsedTime = timestamp - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        const easedProgress = easeOut(progress);

        const currentValue = Math.floor(startValue + easedProgress * (targetValue - startValue));
        element.textContent = `${currentValue.toLocaleString()}${addString}`;

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }

    requestAnimationFrame(updateCounter);
}


async function main() {
    const report = await get_report("data/report.json");
    animateCounter("total-tracks", report.total_tracks, 3000);
    animateCounter("total-artists", report.total_artists, 3500);
    animateCounter("total-streams", report.total_streams/1_000_000_000, 4000, "B");
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
