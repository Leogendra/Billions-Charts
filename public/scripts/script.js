async function call_backend() {
    console.log("Calling backend");

    const password = document.querySelector("#password").value;
    console.log("Password: ", password);

    fetch("/retrieve-tracks", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ password: password })
    })
        .then(response => response.json())
        .then(response => {
            document.querySelector(".result").textContent = response.message;
        })
        .catch(error => console.error("Error:", error))
}


async function get_report(reportPath) {
    try {
        const response = await fetch(reportPath);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } 
    catch (error) {
        console.error('Erreur lors du chargement du JSON:', error);
    }
}