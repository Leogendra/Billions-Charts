const { get_token, get_full_token, get_user_id } = require("./backend/spotify");
const bodyParser = require("body-parser");
const express = require("express");
const path = require("path");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 5500;
const CLIENT_ID = process.env.CLIENT_ID;
const REDIRECT_URI = process.env.REDIRECT_URI;

const VERBOSE = true;

app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, "./public")));




app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "./public/index.html"));
});


app.get("*", (req, res) => {
    res.redirect("/");
});


app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});