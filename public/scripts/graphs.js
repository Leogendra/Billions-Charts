const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
const backgroundDark = getComputedStyle(document.documentElement).getPropertyValue('--color-darker').trim();

// POC
async function create_point_graph(report) {
    const songs = [
        { name: "Have you ever seen the rain", date: "1971-01-05" }
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

    const ctx = document.querySelector('#scatter-plot-tracks').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Songs',
                data: dataPoints,
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 255, 255, 1)',
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: { display: true, text: 'Year of release', color: primaryColor }, // 🟡 Correction
                    ticks: {
                        callback: (val) => parseInt(val),
                        color: primaryColor
                    },
                    grid: {
                        color: backgroundDark,
                    }
                },
                y: {
                    ticks: {
                        display: false,
                        color: primaryColor
                    },
                    grid: {
                        color: backgroundDark,
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const song = songs[context.dataIndex];
                            return `${song.name} - ${song.date}`;
                        }
                    }
                }
            }
        }
    });
}


/*
<details class="chart-container" open>
    <summary class="chart-title">Tracks streamcount by release date</span>
    </summary>
    <canvas class="scatter-plot" id="scatter-plot-tracks"></canvas>
</details>
*/