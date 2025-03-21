const next_arrow_container = document.querySelector('.next-arrow-container');




async function place_arrow() {
    try {
        const response = await fetch('assets/arrow.svg');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const svg = await response.text();
        next_arrow_container.innerHTML = svg;
    }
    catch (error) {
        console.error('Error loading the arrow:', error);
    }
}