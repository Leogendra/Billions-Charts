const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
const primaryColorDarker = getComputedStyle(document.documentElement).getPropertyValue('--primary-color-darker').trim();
const backgroundDark = getComputedStyle(document.documentElement).getPropertyValue('--color-darker').trim();
const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();

const main_colors = [accentColor, "#215783ff", "#6a9b2f", "#f5d443", "#e52f18"];



// Utils
function get_month_name(monthNumber) {
    return new Date(2000, monthNumber - 1).toLocaleString("en-US", { month: "long" });
}


function format_time_label(unit) {
    const totalSeconds = unit * 10;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}


function generate_colors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(main_colors[i % main_colors.length]);
    }
    return colors;
}




// Histograms
async function create_histogram_release_month(report) {
    const monthCount = report.distribution_month_release_count;

    const months = Object.keys(monthCount).sort((a, b) => a - b);
    const values = months.map(month => monthCount[month]);

    const ctx = document.querySelector("#histo-plot-release-month").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: months.map(m => get_month_name(m)),
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
    const monthCount = report.distribution_year_release_count;

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
            labels: months,
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
    const monthCount = report.distribution_month_billion_count;

    // Sort the YYYY-MM keys
    let sortedMonths = Object.keys(monthCount).sort((a, b) => {
        const [yearA, monthA] = a.split("-");
        const [yearB, monthB] = b.split("-");
        return (yearA - yearB) || (monthA - monthB);
    });
    let sortedValues = sortedMonths.map(key => monthCount[key]);

    const [startYear, startMonth] = sortedMonths[0].split("-");
    const [endYear, endMonth] = sortedMonths[sortedMonths.length - 1].split("-");

    // Fill in missing months
    const startDate = new Date(startYear, startMonth - 1);
    const endDate = new Date(endYear, endMonth - 1);
    const allMonths = [];
    for (let d = new Date(startDate); d <= endDate; d.setMonth(d.getMonth() + 1)) {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const key = `${year}-${month}`;
        if (!sortedMonths.includes(key)) {
            sortedMonths.push(key);
            sortedValues.push(0);
        }
    }
    // Sort again
    const sortedData = sortedMonths
        .map((month, index) => ({ month, value: sortedValues[index] }))
        .sort((a, b) => {
            const [yearA, monthA] = a.month.split("-");
            const [yearB, monthB] = b.month.split("-");
            return (yearA - yearB) || (monthA - monthB);
        });
    sortedMonths = sortedData.map(item => item.month);
    sortedValues = sortedData.map(item => item.value);

    const ctx = document.querySelector("#histo-plot-billion-month").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: sortedMonths.map(m => {
                const [year, month] = m.split("-");
                return `${get_month_name(Number(month))} ${year}`;
            }),
            datasets: [{
                label: "Number of tracks",
                data: sortedValues,
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
    const monthCount = report.distribution_year_billion_count;

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
            labels: months,
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


async function create_histogram_streams_count(report) {
    const rawStreams = report.distribution_streams_count;

    let streams = Object.keys(rawStreams).map(k => Number(Number(k).toFixed(1)));
    let values = streams.map(stream => rawStreams[stream.toFixed(1)] || 0);
    const minStreams = 1.0;
    const maxStreams = Math.max(...streams);

    for (let s = minStreams; s < maxStreams; s += 0.1) {
        const rounded = Number(s.toFixed(1));
        if (!streams.includes(rounded)) {
            streams.push(rounded);
            values.push(0);
        }
    }

    const sortedData = streams
        .map((stream, index) => ({ stream: Number(stream), value: values[index] }))
        .sort((a, b) => a.stream - b.stream);

    streams = sortedData.map(d => d.stream.toFixed(1));
    values = sortedData.map(d => d.value);

    const ctx = document.querySelector("#histo-plot-streams-count").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: streams,
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
                        text: "Streams count (in billions)",
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


async function create_histogram_track_count(report) {
    const rawStreams = report.distribution_track_count;

    let trackCount = Object.keys(rawStreams).map(Number);
    let values = trackCount.map(stream => rawStreams[stream] || 0);
    const minStreams = 1;
    const maxStreams = Math.max(...trackCount);

    for (let s = minStreams; s < maxStreams; s += 1) {
        const rounded = Number(s.toFixed(1));
        if (!trackCount.includes(rounded)) {
            trackCount.push(rounded);
            values.push(0);
        }
    }

    const sortedData = trackCount
        .map((stream, index) => ({ stream: Number(stream), value: values[index] }))
        .sort((a, b) => a.stream - b.stream);

    trackCount = sortedData.map(d => d.stream);
    values = sortedData.map(d => d.value);

    const ctx = document.querySelector("#histo-plot-tracks-count").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: trackCount,
            datasets: [{
                label: "Number of artists",
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
                    type: "linear",
                    beginAtZero: true,
                    min: 0,
                    max: 140,
                    title: {
                        display: true,
                        text: "Number of artists",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor,
                        callback: function(value, index) {
                            const intVal = Math.round(value);
                            if (value >= 140) {
                                return "140+";
                            }
                            return intVal;
                        }
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Number of tracks",
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
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return context[0].label + " tracks in the Billions Club";
                        }
                    }
                }
            }
        }
    });
}


async function create_histogram_time_count(report) {
    const rawTimes = report.distribution_time_count;

    let timeCount = Object.keys(rawTimes).map(Number);
    let values = timeCount.map(time => rawTimes[time] || 0);
    const minTime = Math.min(...timeCount);
    const maxTime = Math.max(...timeCount);

    for (let s = minTime; s < maxTime; s += 1) {
        const rounded = Number(s.toFixed(1));
        if (!timeCount.includes(rounded)) {
            timeCount.push(rounded);
            values.push(0);
        }
    }

    const sortedData = timeCount
        .map((time, index) => ({ time: Number(time), value: values[index] }))
        .sort((a, b) => a.time - b.time);

    timeCount = sortedData.map(d => d.time);
    values = sortedData.map(d => d.value);

    const ctx = document.querySelector("#histo-plot-times-count").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: timeCount,
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
                        color: primaryColor,
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Track duration",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor,
                        callback: function (value, index) {
                            return format_time_label(this.getLabelForValue(value));
                        }
                    },
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function (tooltipItems) {
                            const val = tooltipItems[0].parsed.x + minTime;
                            return format_time_label(val);
                        },
                        label: function (tooltipItem) {
                            return `Number of tracks: ${tooltipItem.parsed.y}`;
                        }
                    }
                }
            }
        }
    });
}


async function create_histogram_featuring(report) {
    const rawFeats = report.distribution_featuring_count;

    const featCount = Object.keys(rawFeats).map(Number);
    const values = featCount.map(feat => rawFeats[feat] || 0);

    const ctx = document.querySelector("#histo-plot-featuring").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: featCount,
            datasets: [{
                label: "Number of tracks",
                data: values,
                backgroundColor: generate_colors(featCount.length),
                borderColor: accentColor,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    min: 0.8,
                    type: 'logarithmic',
                    title: {
                        display: true,
                        text: "Number of tracks",
                        color: primaryColor
                    },
                    ticks: {
                        color: primaryColor,
                        autoSkip: false,
                        callback: function (value) {
                            if (([1, 10, 100, 800].includes(value)) || ((value % 300) == 0)) { // manually keeping only some labels, may need adjustment if too many tracks
                                return value;
                            }
                            else {
                                return null;
                            }
                        }
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: "Number of artists featured",
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
                },
            }
        }
    });
}