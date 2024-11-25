const { get_token } = require("./backend/spotify");
const bodyParser = require("body-parser");
const express = require("express");
const path = require("path");
require("dotenv").config();

const VERBOSE = true;
const PORT = process.env.PORT || 3500;

const app = express();
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "./public")));




app.post("/dev", async (_, res) => {
    try {
        const token = await get_token();
        if (token) {
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