const div_key_features = document.querySelector(".div-key-features");-1

const key_feature_templates = [
    "There is {two_billion_count} songs that have been streamed over 2 billion times, that's {two_billion_percentage}% of all songs.",
    "This number goes down to {three_billion_percentage}% for songs over 3 billion streams.",
    "Only {four_billion_count} songs have been streamed over 4 billion times! The last one is {four_billion_song} by {four_billion_artist}.",
    "The latest song to receive over a billion streams is {latest_song} by {latest_artist}, released on {latest_date}.",
    "The oldest song to receive over a billion streams is {oldest_song} by {oldest_artist}, released in {oldest_date}.",
    "The shortest song is {shortest_song} by {shortest_artist}, at {shortest_duration}.",
    "The longest song is {longest_song} by {longest_artist}, at {longest_duration}.",
];




function format_key_feature(template, data) {
    return template.replace(/\{(\w+)\}/g, (_, key) => data[key] ?? "N/A");
}


async function get_key_features() {
    const max_elements = key_feature_templates.length;
    const data = key_feature_templates;
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
        const template = key_feature_templates[i];
        const formattedText = format_key_feature(template, data);

        const slider_item = document.createElement("div");
        slider_item.classList.add("slider-item");
        slider_item.style.setProperty("--position", i + 1);
        slider_item.textContent = formattedText;

        slider_list.appendChild(slider_item);
    }

    slider_element.appendChild(slider_list);
    div_key_features.appendChild(slider_element);
}
