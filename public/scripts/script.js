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


async function call_backend() {
    console.log("Calling backend");
    fetch("/dev", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector(".result").textContent = data.message;
    })
    .catch(error => console.error("Error:", error))
}