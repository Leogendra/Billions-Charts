const { fetch_playlist, get_playcount } = require("./backend/fetcher");
const { clean_playlist } = require("./backend/cleaner");
const { generate_report } = require("./backend/report");
const bodyParser = require("body-parser");
const express = require("express");
const path = require("path");
require("dotenv").config();

const VERBOSE = true;
const PORT = process.env.PORT || 3500;
const PLAYLIST_ID = process.env.PLAYLIST_ID;
const reportFile = "data/report.json";

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "./public")));




app.post("/get-report", async (_, res) => {
    // get the most recent tracks file
    const tracksFile = fs.readdirSync("data").filter(file => file.startsWith("tracks_")).sort().reverse()[0];
    try {
        if (fs.existsSync(reportFile)) {
            const report = JSON.parse(fs.readFileSync(reportFile, "utf-8"));
            res.json(report);
        }
        else {
            await generate_report(tracksFile, reportFile);
            const report = JSON.parse(fs.readFileSync(reportFile, "utf-8"));
            res.json(report);
        }
    }
    catch (error) {
        console.error("Error while retrieving report:", error);
        res.status(500).json({ message: "Error retrieving report." });
    }
});


app.post("/retrieve-tracks", async (req, res) => {
    const { password } = req.body;

    // date with format YYYY-MM-DD
    const tracksFile = `data/tracks_${new Date().toISOString().split("T")[0]}.json`;
    console.log("Tracks file:", tracksFile);

    if (password === process.env.PASSWORD) {
        // Fetch tracks
        try {
            console.log("Fetching tracks...");
            await fetch_playlist(PLAYLIST_ID, tracksFile);
        }
        catch (error) {
            console.error("Error while retrieving tracks:", error);
            res.status(500).json({ message: "Error retrieving tracks." });
        }

        // Then get playcounts
        try {
            console.log("Getting playcounts...");
            await get_playcount(tracksFile);
        }
        catch (error) {
            console.error("Error while retrieving playcounts:", error);
            res.status(500).json({ message: "Error retrieving playcounts." });
        }

        // Then clean playlist
        try {
            console.log("Cleaning playlist...");
            await clean_playlist(tracksFile);
        }
        catch (error) {
            console.error("Error while cleaning playlist:", error);
            res.status(500).json({ message: "Error cleaning playlist." });
        }

        // Then generate report
        try {
            console.log("Generating report...");
            await generate_report(tracksFile, reportFile);
        }
        catch (error) {
            console.error("Error while generating report:", error);
            res.status(500).json({ message: "Error generating report." });
        }

        res.json({ message: "Tracks retrieved and report generated." });
    }
    else {
        console.log("# Invalid password attempt.");
        res.status(401).json({ message: "Invalid password." });
    }
});


app.post("/dev", async (_, res) => {
    res.json({ message: "Ping!" });
});




app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "./public/index.html"));
});


app.get("*", (req, res) => {
    res.redirect("/");
});


app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});