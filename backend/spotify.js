const axios = require('axios');
const qs = require('qs');
require('dotenv').config();

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const SPOTIFY_API_URL = process.env.SPOTIFY_API_URL;




async function get_token() {
    const url = 'https://accounts.spotify.com/api/token';
    const authString = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`, 'utf-8').toString('base64');

    try {
        const response = await axios.post(
            url, 
            qs.stringify({ grant_type: 'client_credentials' }), 
            { headers: {
                Authorization: `Basic ${authString}`,
                'Content-Type': 'application/x-www-form-urlencoded'
            }}
        );
        return response.data.access_token;
    } 
    catch (error) {
        console.error(`Error getting token: ${error}`);
        return null;
    }
}




module.exports = { get_token };
