const puppeteer = require('puppeteer');
const axios = require('axios');
const fs = require('fs');
require('dotenv').config();

const RAPID_API_KEY = process.env.RAPID_API_KEY;




async function fetch_playlist(playlistId, outputFile) {
    if (fs.existsSync(outputFile)) {
        console.log("File already exists. Returning cached data...");
        return JSON.parse(fs.readFileSync(outputFile, 'utf-8'));
    }

    const apiUrl = 'https://spotify-downloader9.p.rapidapi.com/playlistTracks';
    const headers = {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': 'spotify-downloader9.p.rapidapi.com',
    };

    let defaultJson = {
        total: 0,
        items: [],
        generatedTimeStamp: Date.now(),
    };

    let offset = 0;
    let isNext = true;

    while (isNext) {
        try {
            console.log(`Fetching ${offset+100} / ${response.data.data.total} tracks...`);
            const response = await axios.get(apiUrl, {
                params: {
                    id: playlistId,
                    limit: 100,
                    offset: offset,
                },
                headers: headers,
            });

            const data = response.data;
            defaultJson.data.items.push(...data.data.items);
            isNext = data.data.next;
            offset += 100;

        } 
        catch (error) {
            console.error("Error while fetching playlist:", error);
            isNext = false;
        }
    }

    fs.writeFileSync(outputFile, JSON.stringify(defaultJson, null, 4), 'utf-8');
    console.log(`Tracks saved in ${outputFile}`);
    return defaultJson;
}


async function get_playcount(trackId) {
    const url = `https://open.spotify.com/track/${trackId}`;

    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    try {
        await page.goto(url, { waitUntil: 'networkidle2' });
        const playCount = await page.$eval('span[data-testid="playcount"]', span => span.textContent.trim());
        await browser.close();
        return playCount;
    } 
    catch (error) {
        console.error("Erreur :", error);
        await browser.close();
        throw error;
    }
}




module.exports = { fetch_playlist, get_playcount };