const puppeteer = require('puppeteer');
const axios = require('axios');
const fs = require('fs');
require('dotenv').config();

const RAPID_API_KEY = process.env.RAPID_API_KEY;




async function fetch_playlist(playlistId, outputFile) {
    if (fs.existsSync(outputFile)) {
        console.log("File already exists. Using stored data.");
        return;
    }

    console.log("Requesting playlist tracks...");
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
            const response = await axios.get(apiUrl, {
                params: {
                    id: playlistId,
                    limit: 100,
                    offset: offset,
                },
                headers: headers,
            });
            
            const data = response.data;
            if (data.success) {
                defaultJson.items.push(...data.data.items);
                defaultJson.generatedTimeStamp = data.generatedTimeStamp;
                isNext = data.data.next;
                offset += 100;
                console.log(`Fetched ${offset} / ${response.data.data.total} tracks...`);
            }
            else {
                console.error("Error with response:", data.message);
                isNext = false;
            }
        } 
        catch (error) {
            console.error("Error while fetching playlist:", error);
            isNext = false;
        }
    }

    if (defaultJson.items.length === 0) {
        console.error("No tracks found in playlist.");
    }
    else {
        defaultJson.total = defaultJson.items.length;
        fs.writeFileSync(outputFile, JSON.stringify(defaultJson, null, 4), 'utf-8');
        console.log(`Tracks saved in ${outputFile}`);
    }
}


async function get_track_playcount(trackId) {
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


async function get_playcount(tracksFile) {
    const playlist = JSON.parse(fs.readFileSync(tracksFile, 'utf-8'));
    const tracks = playlist.items;

    let nbRetries = 5;
    let nbErrors = tracks.filter(track => !track.playcount).length;

    if (nbErrors == 0) {
        console.log(`Playcounts already fetched.`);
        return;
    }

    while (nbErrors && nbRetries) {
        for (let i = 0; i < tracks.length; i++) {
            const track = tracks[i];

            if (track.playcount) {
                continue;
            }

            console.log(`Fetching playcount for "${track.name}" (${i+1}/${tracks.length})`);

            try {
                const playcount = await get_track_playcount(track.id);
                const playcountInt = parseInt(playCount.replace(/[\s,]/g, '')); 
                tracks[i].playcount = playcountInt
                console.log(`   playcount: ${playcountInt}`);
            } 
            catch (error) {
                console.error("Error while fetching playcount for title:", track.name);
            }
        }
        nbRetries--;
        nbErrors = tracks.filter(track => !track.playcount).length;

        console.log(`Retrying ${nbErrors} tracks...`);
    }

    fs.writeFileSync(tracksFile, JSON.stringify(playlist, null, 4), 'utf-8');
    if (nbErrors === 0) {
        console.log(`Playcounts saved in ${tracksFile}`);
    } 
    else {
        console.error("Error while fetching playcounts. Some tracks were not fetched.");
    }
}





module.exports = { fetch_playlist, get_playcount };