let _fuseTracks = null;
let _fuseArtists = null;
let _selectedIndex = -1;
let _currentResults = [];


async function init_search() {
    const resp = await fetch("data/search_ids.json");
    const data = await resp.json();

    _fuseTracks = new Fuse(data.tracks || [], {
        keys: ["name"],
        threshold: 0.4,
        includeScore: true,
    });

    _fuseArtists = new Fuse(data.artists || [], {
        keys: ["name"],
        threshold: 0.4,
        includeScore: true,
    });

    _wire_search_events();
}


function open_search() {
    const overlay = document.getElementById("search-overlay");
    overlay.classList.add("active");
    overlay.setAttribute("aria-hidden", "false");
    const input = document.getElementById("search-input");
    input.value = "";
    _render_results("");
    setTimeout(() => input.focus(), 50);
}


function close_search() {
    const overlay = document.getElementById("search-overlay");
    overlay.classList.remove("active");
    overlay.setAttribute("aria-hidden", "true");
    _selectedIndex = -1;
    _currentResults = [];
}


function _render_results(query) {
    const container = document.getElementById("search-results");
    _selectedIndex = -1;

    let trackResults, artistResults;

    if (query.length === 0) {
        // Empty query: show nothing (or top defaults could go here)
        container.innerHTML = "";
        _currentResults = [];
        _update_footer_hint();
        return;
    }

    trackResults = _fuseTracks ? _fuseTracks.search(query).slice(0, 6) : [];
    artistResults = _fuseArtists ? _fuseArtists.search(query).slice(0, 4) : [];

    // Merge and interleave: keep best matches from both
    const tracks = trackResults.map(r => ({ type: "track", id: r.item.id, name: r.item.name, artists: r.item.artists, score: r.score }));
    const artists = artistResults.map(r => ({ type: "artist", id: r.item.id, name: r.item.name, score: r.score }));

    // Sort all by score (lower = better in Fuse.js)
    const combined = [...tracks, ...artists].sort((a, b) => a.score - b.score).slice(0, 8);
    _currentResults = combined;

    if (combined.length === 0) {
        container.innerHTML = `<div class="search-no-results">No results for "<strong>${_escape(query)}</strong>"</div>`;
        _update_footer_hint();
        return;
    }

    container.innerHTML = combined.map((item, i) => _render_item_html(item, i)).join("");

    container.querySelectorAll(".search-result-item").forEach((el, i) => {
        el.addEventListener("click", () => _select_result(_currentResults[i]));
    });

    _update_footer_hint();
}


function _render_item_html(item, i) {
    const emoji = item.type === "track" ? "🎵" : "👤";
    const phClass = `search-result-img-placeholder${item.type === "artist" ? " artist-placeholder" : ""}`;

    const imgHtml = `<div class="${phClass}">${emoji}</div>`;

    const sub = item.type === "track" && item.artists?.length
        ? `<div class="search-result-sub">${item.artists.map(_escape).join(", ")}</div>`
        : "";

    return `
    <div class="search-result-item" data-index="${i}">
        ${imgHtml}
        <div class="search-result-info">
            <div class="search-result-name">${_escape(item.name)}</div>
            ${sub}
        </div>
    </div>`;
}


function _update_footer_hint() {
    const hint = document.querySelector(".search-footer-hint");
    if (!hint) return;
    if (_currentResults.length > 0) {
        hint.style.display = "flex";
    } else {
        hint.style.display = "none";
    }
}


function _move_selection(dir) {
    const items = document.querySelectorAll(".search-result-item");
    if (items.length === 0) return;

    if (_selectedIndex >= 0 && _selectedIndex < items.length) {
        items[_selectedIndex].classList.remove("selected");
    }

    _selectedIndex = (_selectedIndex + dir + items.length) % items.length;
    items[_selectedIndex].classList.add("selected");
    items[_selectedIndex].scrollIntoView({ block: "nearest" });
}


function _select_result(item) {
    close_search();
    if (item.type === "track") {
        fetch_and_display_track_card(item.id);
    } else {
        fetch_and_display_artist_card(item.id);
    }
}


function _escape(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}


function _wire_search_events() {
    document.getElementById("search-trigger-btn").addEventListener("click", open_search);

    document.getElementById("search-overlay").addEventListener("click", e => {
        if (e.target.id === "search-overlay") close_search();
    });

    document.getElementById("search-input").addEventListener("input", e => {
        _render_results(e.target.value.trim());
    });

    document.getElementById("search-input").addEventListener("keydown", e => {
        if (e.key === "ArrowDown") { e.preventDefault(); _move_selection(1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); _move_selection(-1); }
        else if (e.key === "Enter") {
            if (_selectedIndex >= 0 && _currentResults[_selectedIndex]) {
                _select_result(_currentResults[_selectedIndex]);
            } else if (_currentResults.length > 0) {
                _select_result(_currentResults[0]);
            }
        }
        else if (e.key === "Escape") close_search();
    });

    // Space to open (when not focused on an input/textarea)
    document.addEventListener("keydown", e => {
        if (e.key === " " && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
            e.preventDefault();
            if (document.getElementById("search-overlay").classList.contains("active")) {
                close_search();
            } else {
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
        // Ctrl+K fallback
        if ((e.ctrlKey || e.metaKey) && e.key === "k") {
            e.preventDefault();
            open_search();
        }
    });
}
