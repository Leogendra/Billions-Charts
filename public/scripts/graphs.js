async function animateCounter(id, targetValue, addString="") {
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with id '${id}' not found.`);
        return;
    }

    let currentValue = 0;
    const increment = Math.ceil(targetValue / 100);
    const duration = 1500; // ms
    const intervalTime = duration / (targetValue / increment);

    const counterInterval = setInterval(() => {
        currentValue += increment;
        if (currentValue >= targetValue) {
            currentValue = targetValue;
            clearInterval(counterInterval);
        }
        element.textContent = `${currentValue.toFixed(0).toLocaleString()}${addString}`;
    }, intervalTime);
}

async function main() {
    const report = await get_report("data/report.json");
    console.log(report.total_streams);
    animateCounter("total-streams", report.total_streams/1_000_000_000, "B");
    animateCounter("total-tracks", report.total_tracks);
    animateCounter("total-artists", report.total_artists);
}


document.addEventListener("DOMContentLoaded", () => {
    main();
});
