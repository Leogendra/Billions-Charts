function save_inputs() {
    input_values = {
    }
    localStorage.setItem("input_values", JSON.stringify(input_values));
}


async function load_inputs() {
    const input_values = JSON.parse(localStorage.getItem("input_values"));
    if ((input_values) && (Object.keys(input_values).length == 0)) {
    }
    else {
    }
}


async function set_results(name, artist, release, link) {
    if (name || artist || release || link) {
        div_result_infos.style.display = "block";
        if (name) {
            result_title.style.display = "block";
            result_title.innerHTML = name;
        }
        else { result_title.style.display = "none"; }
        if (artist) {
            result_artist.style.display = "flex";
            result_artist.innerHTML = artist;
        }
        else { result_artist.style.display = "none"; }
        if (release) {
            result_release.style.display = "block";
            result_release.innerHTML = release;
        }
        else { result_release.style.display = "none"; }
        if (link) {
            result_link_container.style.display = "flex";
            result_link.href = link;
            result_link.textContent = link;
        }
        else { result_link_container.style.display = "none"; }    
    }
    else { div_result_infos.style.display = "none"; }
}


async function check_acces_token(redirectType) {
    const accessToken = localStorage.getItem("accessToken");
    const tokenValidity = localStorage.getItem("tokenValidity");
    let isTokenValid = false;
    await fetch("/check-token", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ accessToken, tokenValidity })
    })
    .then(response => response.json())
    .then(data => {
        isTokenValid = data.valid;
    })
    .catch(error => {
        console.error("Error checking token:", error);
        isTokenValid = false;
    });
    console.log("Token validity:", isTokenValid);
    if (isTokenValid) {
        return accessToken;
    }
    else {
        localStorage.removeItem("accessToken");
        localStorage.setItem("action_redirect", redirectType);
        window.location.href = "/auth";
        return null;
    }
}


async function call_backend() {
    // fetch("/backend", {
    //     method: "POST",
    //     headers: {
    //         "Content-Type": "application/json",
    //     },
    //     body: JSON.stringify({
    //         accessToken: accessToken
    //     })
    // })
    // .then(response => response.json())
    // .then(data => {
    //     // actions with data
    // })
    // .catch(error => console.error("Error:", error))
}