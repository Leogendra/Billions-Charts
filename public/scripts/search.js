const search_button = document.querySelector("#search-trigger-btn");
const floating_search_button = document.querySelector("#search-fab");

const search_overlay = document.querySelector("#search-overlay");
const search_input = document.querySelector("#search-input");
const search_results = document.querySelector("#search-results");
const search_footer_hint = document.querySelector(".search-footer-hint");


let fuse_tracks = null;
let fuse_artists = null;
let searchSelectedIndex = -1;
let search_current_results = [];


async function init_search() {
    const resp = await fetch("data/search_ids.json");
    const data = await resp.json();

    fuse_tracks = new Fuse(data.tracks || [], {
        keys: ["name"],
        threshold: 0.4,
        includeScore: true,
    });

    fuse_artists = new Fuse(data.artists || [], {
        keys: ["name"],
        threshold: 0.4,
        includeScore: true,
    });

    setup_search_events();
}


function open_search() {
    search_overlay.classList.add("active");
    search_overlay.setAttribute("aria-hidden", "false");
    search_input.value = "";
    render_search_results("");
    setTimeout(() => search_input.focus(), 50);
}


function close_search() {
    search_overlay.classList.remove("active");
    search_overlay.setAttribute("aria-hidden", "true");
    searchSelectedIndex = -1;
    search_current_results = [];
}


function render_search_results(query) {
    searchSelectedIndex = -1;

    let trackResults, artistResults;

    if (query.length === 0) {
        search_results.innerHTML = "";
        search_current_results = [];
        update_search_footer_hint();
        return;
    }

    trackResults = fuse_tracks ? fuse_tracks.search(query).slice(0, 6) : [];
    artistResults = fuse_artists ? fuse_artists.search(query).slice(0, 4) : [];

    // Merge and interleave: keep best matches from both
    const tracks = trackResults.map(r => ({ type: "track", id: r.item.id, name: r.item.name, artists: r.item.artists, score: r.score }));
    const artists = artistResults.map(r => ({ type: "artist", id: r.item.id, name: r.item.name, score: r.score }));

    // Sort all by score (lower = better in Fuse.js)
    const combined = [...tracks, ...artists].sort((a, b) => a.score - b.score).slice(0, 8);
    search_current_results = combined;

    if (combined.length === 0) {
        search_results.innerHTML = `<div class="search-no-results">No results for "<strong>${escape_html(query)}</strong>"</div>`;
        update_search_footer_hint();
        return;
    }

    search_results.innerHTML = combined.map((item, i) => render_search_item_html(item, i)).join("");

    search_results.querySelectorAll(".search-result-item").forEach((el, i) => {
        el.addEventListener("click", () => select_search_result(search_current_results[i]));
    });

    update_search_footer_hint();
}


function render_search_item_html(item, i) {
    const emoji = item.type === "track" ? "🎵" : "👤";
    const phClass = `search-result-img-placeholder${item.type === "artist" ? " artist-placeholder" : ""}`;

    const imgHtml = `<div class="${phClass}">${emoji}</div>`;

    const sub = item.type === "track" && item.artists?.length
        ? `<div class="search-result-sub">${item.artists.map(escape_html).join(", ")}</div>`
        : "";

    return `
    <div class="search-result-item" data-index="${i}">
        ${imgHtml}
        <div class="search-result-info">
            <div class="search-result-name">${escape_html(item.name)}</div>
            ${sub}
        </div>
    </div>`;
}


function update_search_footer_hint() {
    if (!search_footer_hint) { return; }
    if ((search_current_results.length > 0) && !IS_MOBILE) {
        search_footer_hint.style.display = "flex";
    } 
    else {
        search_footer_hint.style.display = "none";
    }
}


function move_search_selection(dir) {
    const items = document.querySelectorAll(".search-result-item");
    if (items.length === 0) { return; }

    if (searchSelectedIndex >= 0 && searchSelectedIndex < items.length) {
        items[searchSelectedIndex].classList.remove("selected");
    }

    searchSelectedIndex = (searchSelectedIndex + dir + items.length) % items.length;
    items[searchSelectedIndex].classList.add("selected");
    items[searchSelectedIndex].scrollIntoView({ block: "nearest" });
}


function select_search_result(item) {
    close_search();
    if (item.type === "track") {
        fetch_and_display_track_card(item.id);
    } 
    else {
        fetch_and_display_artist_card(item.id);
    }
}


function setup_search_fab() {
    floating_search_button.classList.toggle("visible")
    floating_search_button.addEventListener("click", open_search);
}


function setup_search_events() {
    search_button.addEventListener("click", open_search);
    setup_search_fab();

    search_overlay.addEventListener("click", e => {
        if (e.target.id === "search-overlay") { close_search(); }
    });

    search_input.addEventListener("input", e => {
        render_search_results(e.target.value.trim());
    });

    // arrows to navigate, enter to select, escape to close
    search_input.addEventListener("keydown", e => {
        if (e.key === "ArrowDown") { e.preventDefault(); move_search_selection(1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); move_search_selection(-1); }
        else if (e.key === "Enter") {
            if (searchSelectedIndex >= 0 && search_current_results[searchSelectedIndex]) {
                select_search_result(search_current_results[searchSelectedIndex]);
            } else if (search_current_results.length > 0) {
                select_search_result(search_current_results[0]);
            }
        }
        else if (e.key === "Escape") close_search();
    });

    // space to open (when not focused on an input/textarea)
    document.addEventListener("keydown", e => {
        if (e.key === " " && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
            e.preventDefault();
            if (search_overlay.classList.contains("active")) {
                close_search();
            }
            else {
                const zoomOverlay = document.getElementById("image-zoom-overlay");
                if (zoomOverlay?.classList.contains("visible")) {
                    close_popup_card_image_zoom();
                }
                const popupOverlay = document.getElementById("track-popup-overlay");
                if (popupOverlay?.classList.contains("visible")) {
                    close_popup_card();
                }
                open_search();
            }
        }
    });
}
