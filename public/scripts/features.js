const div_slider = document.querySelector(".div-slider");
const slider_features = document.querySelector("#slider-features");

let sliderItemWidth = 0;
let sliderItemGap = 0;

const KEY_FEATURES_TEMPLATE = [
    "There is {two_billion_count} songs that have been streamed over 2 billion times, that's %{two_billion_percentage}% of all Billions songs 🎵",
    "This number goes down to {three_billion_count} for songs over 3 billion streams (%{three_billion_percentage}%) 🎶",
    "Only {four_billion_count} songs have been streamed over 4 billion times! The most streamed one is {{four_billion_song}} by {{four_billion_artist}} 🥇",
    "Want to listen to every single one of these songs? Well, you'd need {total_time} hours. With each track averaging {average_track_lenght} minutes, hope you're ready for a marathon! 🕒",
    "The latest song to receive over a billion streams is {{latest_song}} by {{latest_artist}}, reaching the milestone on {latest_date} 🆕",
    "This year, {this_year_count} songs have already joined the Billions Club 🚀",
    "The current most popular song is {{most_popular_song}} by {{most_popular_artist}}, with {most_popular_streams} streams 🔥",
    "The fastest song to receive over a billion streams is {{fastest_song}} by {{fastest_artist}}, in only {fastest_days} days! ⚡",
    "A total of {count_artists_2plus_tracks} artists have achieved the rare feat of hitting it big with 2 tracks or more, which represents %{percent_artists_2plus_tracks}% of all artists 🏅🏅",
    "But only %{percent_artists_5plus_tracks}% of artists can claim the ultimate bragging rights with 5 songs or more in the Billions Club, props to all {count_artists_5plus_tracks} of them! 🏆",
    "The shortest song is {{shortest_song}} by {{shortest_artist}}, with a duration of {shortest_duration} ⏳",
    "{{longest_artist}} have the longest song with {{longest_song}}, running for {longest_duration} 🥵",
    "Among all these songs, %{percent_explicit}% contain explicit lyrics 🙉",
    "%{percent_solo_tracks}% of the tracks are made by solo artists, while the rest are shared by multiple collaborators, with the highest number of artists on a single track being {highest_featuring_count}! 🤝"
];




function format_key_features(data) {
    return KEY_FEATURES_TEMPLATE.map(template =>
        template
            .replace(/\{\{(\w+)\}\}/g, (_, key) => // Double curly braces for links
                `<a class="important-link" href="${data[key + "_link"] || key}" target="_blank">${data[key] || "#"}</a>`
            )
            .replace(/\%\{(\w+)\}\%/g, (_, key) => // Percentages for '%' to be highlighted
                `<span class="important-text">${data[key] || "0"}%</span>`
            )
            .replace(/\{(\w+)\}/g, (_, key) => // Single curly braces for regular text
                `<span class="important-text">${data[key] || "0"}</span>`
            )
    );
}


async function get_key_features(report) {
    const key_features = format_key_features(report.template_data);

    // Add the key features to the slider
    key_features.forEach((feature) => {
        const slider_text = document.createElement("div");
        slider_text.classList.add("slider-text");
        slider_text.innerHTML = feature;

        const slider_item = document.createElement("div");
        slider_item.classList.add("slider-item");
        slider_item.appendChild(slider_text);

        slider_features.appendChild(slider_item);
    });

    const totalItems = key_features.length;
    const sliderContainerWitdh = div_slider.getBoundingClientRect().width;
    const sliderItemWidth = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--slider-item-width").trim());
    const sliderItemGap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--slider-items-gap").trim());
    const itemWidth = sliderItemWidth + sliderItemGap;

    slider_features.style.transform = `translateX(${(sliderContainerWitdh - itemWidth) / 2}px)`;

    // Move the slider
    let currentIndex = 0;
    function move_slider(direction) {
        currentIndex = (currentIndex + direction + totalItems) % totalItems;
        const translation = (sliderContainerWitdh - itemWidth) / 2 - currentIndex * itemWidth;

        slider_features.style.transition = "transform .5s ease-in-out";
        slider_features.style.transform = `translateX(${translation}px)`;
    }

    // Add event listeners to the left/right buttons
    document.querySelector(".slider-button-left").addEventListener("click", () => move_slider(-1));
    document.querySelector(".slider-button-right").addEventListener("click", () => move_slider(1));
}