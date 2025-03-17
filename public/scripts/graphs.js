const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
const backgroundDark = getComputedStyle(document.documentElement).getPropertyValue('--color-darker').trim();
const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();

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
                    title: {
                        display: true,
                        text: 'Year of release',
                        color: primaryColor
                    },
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


function getMonthName(monthNumber) {
    return new Date(2000, monthNumber - 1).toLocaleString("en-US", { month: "long" });
}


async function create_histogram_release_month(report) {
    const monthCount = report.month_release_count;

    const months = Object.keys(monthCount).sort((a, b) => a - b);
    const values = months.map(month => monthCount[month]);

    const ctx = document.querySelector("#histo-plot-release-month").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: months.map(m => getMonthName(m)),
            datasets: [{
                label: "Number of tracks",
                data: values,
                backgroundColor: accentColor,
                borderColor: accentColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Number of tracks",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Month",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

async function create_histogram_release_year(report) {
    const monthCount = report.year_release_count;

    let months = Object.keys(monthCount).map(Number);
    let values = months.map(year => monthCount[year] || 0);

    const minYear = Math.min(...months);
    const maxYear = Math.max(...months);
    for (let year = minYear; year <= maxYear; year++) {
        if (!months.includes(year)) {
            months.push(year);
            values.push(0);
        }
    }

    const sortedData = months
        .map((year, index) => ({ year, value: values[index] }))
        .sort((a, b) => a.year - b.year);

    months = sortedData.map(item => item.year);
    values = sortedData.map(item => item.value);

    const ctx = document.querySelector("#histo-plot-release-year").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: months.map(m => m),
            datasets: [{
                label: "Number of tracks",
                data: values,
                backgroundColor: accentColor,
                borderColor: accentColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Number of tracks",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Years",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}


async function create_histogram_billion_month(report) {
    const monthCount = report.month_billion_count;

    const months = Object.keys(monthCount).sort((a, b) => a - b);
    const values = months.map(month => monthCount[month]);

    const ctx = document.querySelector("#histo-plot-billion-month").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: months.map(m => getMonthName(m)),
            datasets: [{
                label: "Number of tracks",
                data: values,
                backgroundColor: accentColor,
                borderColor: accentColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Number of tracks",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Month",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

async function create_histogram_billion_year(report) {
    const monthCount = report.year_billion_count;

    let months = Object.keys(monthCount).map(Number);
    let values = months.map(year => monthCount[year] || 0);

    const minYear = Math.min(...months);
    const maxYear = Math.max(...months);
    for (let year = minYear; year <= maxYear; year++) {
        if (!months.includes(year)) {
            months.push(year);
            values.push(0);
        }
    }

    const sortedData = months
        .map((year, index) => ({ year, value: values[index] }))
        .sort((a, b) => a.year - b.year);

    months = sortedData.map(item => item.year);
    values = sortedData.map(item => item.value);

    const ctx = document.querySelector("#histo-plot-billion-year").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: months.map(m => m),
            datasets: [{
                label: "Number of tracks",
                data: values,
                backgroundColor: accentColor,
                borderColor: accentColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Number of tracks",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Years",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor
                    },
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}