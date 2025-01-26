const track = document.getElementById("image-track");




const handleMouseMove = (e) => {
    if (track.dataset.mouseDownAt === "0") return;

    const mouseDelta = parseFloat(track.dataset.mouseDownAt) - e.clientX;
    const maxDelta = window.innerWidth / 2;

    const percentage = (mouseDelta / maxDelta) * -100;
    const nextPercentageUnconstrained = parseFloat(track.dataset.prevPercentage || "0") + percentage;

    // Allows the first and the last element to be scrolled to the center
    const nextPercentage = Math.max(Math.min(nextPercentageUnconstrained, 30), -65);

    track.dataset.percentage = nextPercentage;

    track.style.transform = `translate(${nextPercentage}%, 0%)`;
};


const handleMouseDown = (e) => {
    track.dataset.mouseDownAt = e.clientX;
};

const handleMouseUp = () => {
    track.dataset.mouseDownAt = "0";
    track.dataset.prevPercentage = track.dataset.percentage;
};