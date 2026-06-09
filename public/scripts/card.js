function create_row_card(track, position, additionalInfo = "") {
    const trackName = track.name.replace(/\([^)]*\)/g, "").trim()
    const music_card = document.createElement("div");
    music_card.classList.add("music-card");
    music_card.classList.add("item");
    music_card.style.setProperty("--position", position);

    // Generate artists links
    const artistsLinks = track.artists
        .map(artist => `<a class="cta-link" href="#" onclick="event.preventDefault(); fetch_and_display_artist_card('${artist.id}')">${artist.name}</a>`)
        .join(", ");

    const additionalInfoDiv = additionalInfo === "" ? "" : `<div class="music-infos">${additionalInfo}</div>`;

    music_card.innerHTML = `
    <a href="#" onclick="event.preventDefault(); open_popup_card_image_zoom('${track.image}')">
        <img src="${track.image}" alt="${trackName}">
    </a>
    <div class="music-card-content">
        <div class="music-title">
            <a class="cta-link" href="#" onclick="event.preventDefault(); fetch_and_display_track_card('${track.id}')">${trackName}</a>
        </div>
        <div class="music-artist">
            ${artistsLinks}
        </div>
    </div>
    ${additionalInfoDiv}
    `;

    music_card.addEventListener("click", (e) => {
        if (!e.target.closest("a")) fetch_and_display_track_card(track.id);
    });

    return music_card;
}


function create_track_popup_card(track) {
    const trackName = track.name.replace(/\([^)]*\)/g, "").trim();
    const isExplicit = track.contentRating?.toLowerCase() === "explicit";

    const artistsLinks = track.artists
        .map(a => `<a class="cta-link" data-artist-id="${a.id}" href="https://open.spotify.com/artist/${a.id}" target="_blank" rel="noopener noreferrer">${a.name}</a>`)
        .join(", ");

    const stats = [];
    if (track.playcount != null) { stats.push({ label: "Streams", value: format_playcount(track.playcount) }); }
    if (track.duration_ms != null) { stats.push({ label: "Duration", value: format_milliseconds(track.duration_ms) }); }
    if (track.release_date) { stats.push({ label: "Released", value: format_release_date(track.release_date, track.release_date_precision) }); }
    if (track.popularity != null) { stats.push({ label: "Popularity", value: `${track.popularity} / 100` }); }
    if (track.streams_per_day != null) { stats.push({ label: "Streams/day", value: format_playcount(track.streams_per_day) }); }
    if (track.added_at) { stats.push({ label: "Billion date", value: format_iso_date(track.added_at) }); }

    const statsHtml = stats.map(s => `
        <div class="popup-stat">
            <span class="popup-stat-label">${s.label}</span>
            <span class="popup-stat-value">${s.value}</span>
        </div>`).join("");

    const allGenres = [...new Set(
        track.artists.flatMap(a => a.genres || [])
    )].slice(0, 6);
    const genresHtml = allGenres.length > 0
        ? `<div class="popup-genres">${allGenres.map(g => `<span class="popup-genre-tag">${g}</span>`).join("")}</div>`
        : "";

    return `
        <button class="popup-close">✕</button>
        <div class="popup-cover">
            <img src="${track.image}" alt="${trackName}">
        </div>
        <div class="popup-track-name">
            ${trackName}
            ${isExplicit ? '<span class="popup-explicit">E</span>' : ""}
        </div>
        <div class="popup-artists">${artistsLinks}</div>
        ${genresHtml}
        <div class="popup-stats">${statsHtml}</div>
        <a class="popup-spotify-btn" href="https://open.spotify.com/track/${track.id}" target="_blank" rel="noopener noreferrer">Open in Spotify ↗</a>
    `;
}


function open_track_popup_card(track) {
    let overlay = document.getElementById("track-popup-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "track-popup-overlay";
        const popup = document.createElement("div");
        popup.classList.add("track-popup");
        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) close_popup_card();
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                const zoomOverlay = document.getElementById("image-zoom-overlay");
                if (zoomOverlay?.classList.contains("visible")) { close_popup_card_image_zoom(); }
                else { close_popup_card(); }
            }
        });
    }

    try {

        overlay.querySelector(".track-popup").innerHTML = create_track_popup_card(track);
        overlay.querySelector(".popup-close").addEventListener("click", close_popup_card);
        overlay.querySelector(".popup-cover img").addEventListener("click", (e) => {
            e.stopPropagation();
            open_popup_card_image_zoom(track.image);
        });

        overlay.querySelectorAll(".popup-artists .cta-link[data-artist-id]").forEach(link => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                const artistId = link.dataset.artistId;
                if (artistId) { fetch_and_display_artist_card(artistId); }
            });
        });

        overlay.classList.add("visible");
        document.body.style.overflow = "hidden";
    }
    catch (err) {
        console.error("Error populating popup content:", err);
        open_popup_card_error();
    }
}


function close_popup_card() {
    const overlay = document.getElementById("track-popup-overlay");
    if (overlay) {
        overlay.classList.remove("visible");
        document.body.style.overflow = "";
    }
}


function open_popup_card_image_zoom(src) {
    let overlay = document.getElementById("image-zoom-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "image-zoom-overlay";
        const img = document.createElement("img");
        overlay.appendChild(img);
        document.body.appendChild(overlay);
        overlay.addEventListener("click", close_popup_card_image_zoom);
    }

    overlay.querySelector("img").src = src;
    overlay.classList.add("visible");
}


function close_popup_card_image_zoom() {
    document.getElementById("image-zoom-overlay")?.classList.remove("visible");
}


async function fetch_and_display_track_card(trackId) {
    if (!trackId || typeof trackId !== "string" || !/^[a-zA-Z0-9]+$/.test(trackId)) {
        open_popup_card_error();
        return;
    }
    open_popup_card_loading();
    try {
        const response = await fetch(`/track/${trackId}/`);
        if (response.ok) {
            const track = await response.json();
            open_track_popup_card(track);
        }
        else { 
            throw new Error(`HTTP ${response.status}`);
        }
    } 
    catch (err) {
        open_popup_card_error();
    }
}


function open_popup_card_loading() {
    let overlay = document.getElementById("track-popup-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "track-popup-overlay";
        const popup = document.createElement("div");
        popup.classList.add("track-popup");
        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) { close_popup_card(); }
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                const zoomOverlay = document.getElementById("image-zoom-overlay");
                if (zoomOverlay?.classList.contains("visible")) { close_popup_card_image_zoom(); }
                else { close_popup_card(); }
            }
        });
    }

    const skeletonStats = Array.from({ length: 6 }, () => `
        <div class="popup-stat">
            <div class="skeleton skeleton-label"></div>
            <div class="skeleton skeleton-value"></div>
        </div>`).join("");

    overlay.querySelector(".track-popup").innerHTML = `
        <button class="popup-close">✕</button>
        <div class="skeleton skeleton-cover"></div>
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-artist"></div>
        <div class="popup-stats">${skeletonStats}</div>
        <div class="skeleton skeleton-btn"></div>
    `;
    overlay.querySelector(".popup-close").addEventListener("click", close_popup_card);
    overlay.classList.add("visible");
    document.body.style.overflow = "hidden";
}


function open_popup_card_error() {
    const popup = document.querySelector("#track-popup-overlay .track-popup");
    if (popup) {
        popup.innerHTML = `
            <button class="popup-close">✕</button>
            <div class="popup-error">Failed to load track details.</div>
        `;
        popup.querySelector(".popup-close").addEventListener("click", close_popup_card);
    }
}


function create_artist_popup_card(artist) {
    const coverHtml = artist.image
        ? `<div class="popup-cover artist-cover">
               <img src="${artist.image}" alt="${artist.name}">
           </div>`
        : "";

    const allGenres = (artist.genres || []).slice(0, 6);
    const genresHtml = allGenres.length > 0
        ? `<div class="popup-genres">${allGenres.map(g => `<span class="popup-genre-tag">${g}</span>`).join("")}</div>`
        : "";

    const totalMin = Math.floor(artist.total_duration_ms / 60000);
    const hours = Math.floor(totalMin / 60);
    const mins = totalMin % 60;
    const seconds = Math.floor((artist.total_duration_ms % 60000) / 1000);
    const durationStr = (hours > 0) ? `${hours}h ${mins}m` : `${mins}m ${seconds}s`;

    const stats = []
    if (artist.total_playcount != null) { stats.push({ label: "Total streams", value: format_playcount(artist.total_playcount) }); }
    if (artist.followers != null) { stats.push({ label: "Followers", value: format_playcount(artist.followers) }); }
    if (artist.popularity != null) { stats.push({ label: "Popularity", value: `${artist.popularity} / 100` }); }
    if (artist.total_duration_ms != null) { stats.push({ label: "Total duration", value: durationStr }); }

    const statsHtml = stats.length > 0
        ? stats.map(s => `
        <div class="popup-stat">
            <span class="popup-stat-label">${s.label}</span>
            <span class="popup-stat-value">${s.value}</span>
        </div>`).join("")
        : "";

    const tracksHtml = (artist.tracks || []).map(t => `
        <div class="popup-artist-track-item" data-track-id="${t.id}">
            <img class="popup-artist-track-img" src="${t.image}" alt="${t.name}">
            <span class="popup-artist-track-name">${t.name}</span>
            <span class="popup-artist-track-streams">${format_playcount(t.playcount)}</span>
        </div>`).join("");

    return `
        <button class="popup-close">✕</button>
        ${coverHtml}
        <div class="popup-track-name">${artist.name}</div>
        ${genresHtml}
        ${statsHtml ? `<div class="popup-stats">${statsHtml}</div>` : ""}
        <div class="popup-artist-tracks">
            <div class="popup-artist-tracks-title">Tracks in playlist (${artist.tracks?.length || 0})</div>
            <div class="popup-artist-tracks-list">${tracksHtml}</div>
        </div>
        <a class="popup-spotify-btn" href="https://open.spotify.com/artist/${artist.id}" target="_blank" rel="noopener noreferrer">Open in Spotify ↗</a>
    `;
}


function open_artist_popup_card(artist) {
    let overlay = document.getElementById("track-popup-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "track-popup-overlay";
        const popup = document.createElement("div");
        popup.classList.add("track-popup");
        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) close_popup_card();
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                const zoomOverlay = document.getElementById("image-zoom-overlay");
                if (zoomOverlay?.classList.contains("visible")) { close_popup_card_image_zoom(); }
                else { close_popup_card(); }
            }
        });
    }

    try {
        overlay.querySelector(".track-popup").innerHTML = create_artist_popup_card(artist);
        overlay.querySelector(".popup-close").addEventListener("click", close_popup_card);

        const coverImg = overlay.querySelector(".popup-cover img");
        if (coverImg) {
            coverImg.addEventListener("click", (e) => {
                e.stopPropagation();
                open_popup_card_image_zoom(artist.image);
            });
        }

        overlay.querySelectorAll(".popup-artist-track-item").forEach(item => {
            item.addEventListener("click", () => {
                close_popup_card();
                fetch_and_display_track_card(item.dataset.trackId);
            });
        });

        overlay.classList.add("visible");
        document.body.style.overflow = "hidden";
    }
    catch (err) {
        console.error("Error populating artist popup:", err);
        open_popup_card_error();
    }
}


function open_artist_popup_card_loading() {
    let overlay = document.getElementById("track-popup-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "track-popup-overlay";
        const popup = document.createElement("div");
        popup.classList.add("track-popup");
        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) close_popup_card();
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                const zoomOverlay = document.getElementById("image-zoom-overlay");
                if (zoomOverlay?.classList.contains("visible")) { close_popup_card_image_zoom(); }
                else { close_popup_card(); }
            }
        });
    }

    const skeletonStats = Array.from({ length: 5 }, () => `
        <div class="popup-stat">
            <div class="skeleton skeleton-label"></div>
            <div class="skeleton skeleton-value"></div>
        </div>`).join("");

    overlay.querySelector(".track-popup").innerHTML = `
        <button class="popup-close">✕</button>
        <div class="skeleton skeleton-cover-circle"></div>
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-genres">
            ${Array.from({ length: 3 }, () => `<div class="skeleton skeleton-tag"></div>`).join("")}
        </div>
        <div class="popup-stats">${skeletonStats}</div>
    `;
    overlay.querySelector(".popup-close").addEventListener("click", close_popup_card);
    overlay.classList.add("visible");
    document.body.style.overflow = "hidden";
}


async function fetch_and_display_artist_card(artistId) {
    if (!artistId || typeof artistId !== "string" || !/^[a-zA-Z0-9]+$/.test(artistId)) {
        open_popup_card_error();
        return;
    }
    open_artist_popup_card_loading();
    try {
        const response = await fetch(`/artist/${artistId}/`);
        if (response.ok) {
            const artist = await response.json();
            open_artist_popup_card(artist);
        }
        else {
            throw new Error(`HTTP ${response.status}`);
        }
    }
    catch (err) {
        open_popup_card_error();
    }
}