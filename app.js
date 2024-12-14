const { fetch_playlist, get_playcount } = require("./backend/fetcher");
const { clean_playlist } = require("./backend/cleaner");
const { generate_report } = require("./backend/report");
const bodyParser = require("body-parser");
const express = require("express");
const path = require("path");
require("dotenv").config();

const VERBOSE = true;
const PORT = process.env.PORT || 3500;
const PLAYLIST_URL = process.env.PLAYLIST_URL;

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "./public")));




app.post("/dev", async (_, res) => {
    
    const tracksFile = "data/tracks.json";
    const outputFile = "data/report.json";

    try {
        const token = true
        if (token) {
            await generate_report(tracksFile, outputFile);
            res.json({ message: "Token Got" });
        }
        else {
            res.status(500).json({ message: "Unknown error." });
        }
    }
    catch (error) {
        console.error("Error retrieving genre:", error);
        res.status(500).json({ message: "Error retrieving genre." });
    }
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