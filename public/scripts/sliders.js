const scrollable_section = document.querySelector("#div-scrollable");




const handleMouseMove = (e) => {
    if (scrollable_section.dataset.mouseDownAt === "0") { return; };
    const mouseDelta = parseFloat(track.dataset.mouseDownAt) - e.clientX;
    const maxDelta = window.innerWidth / 2;

    const percentage = (mouseDelta / maxDelta) * -100;
    const nextPercentageUnconstrained = parseFloat(scrollable_section.dataset.prevPercentage || "0") + percentage;

    // Allows the first and the last element to be scrolled to the center
    const nextPercentage = Math.max(Math.min(nextPercentageUnconstrained, 30), -65);
    scrollable_section.dataset.percentage = nextPercentage;
    scrollable_section.style.transform = `translate(${nextPercentage}%, 0%)`;
};


const handleMouseDown = (e) => {
    scrollable_section.dataset.mouseDownAt = e.clientX;
};

const handleMouseUp = () => {
    scrollable_section.dataset.mouseDownAt = "0";
    scrollable_section.dataset.prevPercentage = scrollable_section.dataset.percentage;
};

// add events
scrollable_section.addEventListener("mousedown", handleMouseDown);
scrollable_section.addEventListener("mousemove", handleMouseMove);
scrollable_section.addEventListener("mouseup", handleMouseUp);
scrollable_section.addEventListener("mouseleave", handleMouseUp);
