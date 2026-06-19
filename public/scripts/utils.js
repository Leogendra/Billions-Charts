const month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];




function format_release_date(date, precision) {
    if (!date) return null;
    const parts = date.split("-");
    if (precision === "year" || parts.length === 1) return parts[0];
    if (precision === "month" || parts.length === 2) return `${month_names[parseInt(parts[1]) - 1]} ${parts[0]}`;
    return `${parseInt(parts[2])} ${month_names[parseInt(parts[1]) - 1]} ${parts[0]}`;
}


function format_iso_date(isoString) {
    if (!isoString) return null;
    const d = new Date(isoString);
    return `${d.getUTCDate()} ${month_names[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}


function format_playcount(count) {
    if (count == null) { return null; }
    if (count >= 1_000_000_000) { return `${(count / 1_000_000_000).toFixed(2)}B`; }
    else if (count >= 1_000_000) { return `${(count / 1_000_000).toFixed(2)}M`; }
    else if (count >= 1_000) { return `${(count / 1_000).toFixed(2)}K`; }
    return count.toLocaleString();
}


function format_milliseconds(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = seconds % 60;
    return `${minutes}:${remaining_seconds.toString().padStart(2, '0')}`;
}


function format_number_of_days(days) {
    if (days == null) return null;
    const years = Math.floor(days / 365);
    const months = Math.floor((days % 365) / 30);
    const remainingDays = days % 365 % 30;
    const parts = [];
    if (years > 0) parts.push(`${years}y`);
    if (months > 0) parts.push(`${months}mo`);
    if (remainingDays > 0 || parts.length === 0) parts.push(`${remainingDays}d`);
    return parts.join(" ");
}


function escape_html(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}