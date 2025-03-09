const div_key_features = document.querySelector(".div-key-features");-1

const KEY_FEATURES_TEMPLATE = [
    "There is {two_billion_count} songs that have been streamed over 2 billion times, that's {two_billion_percentage}% of all songs.",
    "This number goes down to {three_billion_count} for songs over 3 billion streams ({three_billion_percentage}%).",
    "Only {four_billion_count} songs have been streamed over 4 billion times! The higher one is {four_billion_song} by {four_billion_artist}.",
    "The latest song to receive over a billion streams is {latest_song} by {latest_artist}, released on {latest_date}.",
    "The oldest song to receive over a billion streams is {oldest_song} by {oldest_artist}, released in {oldest_date}.",
    "The shortest song is {shortest_song} by {shortest_artist}, at {shortest_duration}.",
    "The longest song is {longest_song} by {longest_artist}, at {longest_duration}.",
];




function format_key_features(data) {
    return KEY_FEATURES_TEMPLATE.map(template => 
        template.replace(/\{(\w+)\}/g, (_, key) => 
            `<span class="important-link">${data[key] || "???"}</span>`
        )
    );
}


async function get_key_features(report) {
    const key_features = format_key_features(report.template_data);
    const max_elements = key_features.length;
    let animation_duration = max_elements * 3 + "s";

    let slider_element = document.createElement("div");
    slider_element.classList.add("div-slider");
    slider_element.style.setProperty("--duration", animation_duration);
    slider_element.style.setProperty("--quantity", max_elements);

    // Create the slider list
    const slider_list = document.createElement("div");
    slider_list.classList.add("slider");
    slider_list.id = "slider-features";

    // Generate the cards with the data
    for (let i = 0; i < max_elements; i++) {
        const currentFeature = key_features[i];

        const slider_text = document.createElement("div");
        slider_text.classList.add("slider-text");
        slider_text.innerHTML = currentFeature;

        const slider_item = document.createElement("div");
        slider_item.classList.add("slider-item");
        slider_item.style.setProperty("--position", i + 1);
        slider_item.appendChild(slider_text);

        slider_list.appendChild(slider_item);
    }

    slider_element.appendChild(slider_list);
    div_key_features.appendChild(slider_element);
}
