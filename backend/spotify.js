const axios = require('axios');
const qs = require('qs');
require('dotenv').config();

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const SPOTIFY_API_URL = process.env.SPOTIFY_API_URL;
const REDIRECT_URI = process.env.REDIRECT_URI;




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


async function get_full_token(code) {
    const url = 'https://accounts.spotify.com/api/token';
    
    const authString = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');

    try {
        const response = await axios.post(url, qs.stringify({
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: REDIRECT_URI
        }), {
            headers: {
                Authorization: `Basic ${authString}`,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });

        return response.data.access_token;
    } 
    catch (error) {
        console.error(`Error getting full token: ${error}`);
        if (error.response) {
            console.log('Error response status:', error.response.status);
            console.log('Error response data:', error.response.data);
        }
        return null;
    }
}


async function get_user_id(access_token) {
    const url = `${SPOTIFY_API_URL}/me`;
    try {
        const response = await axios.get(url, {
            headers: { Authorization: `Bearer ${access_token}` }
        });
        if (response.data.error) {
            return null;
        }
        else {
            return response.data.id;
        }
    } 
    catch (error) {
        console.error(`Error getting user ID: ${error}`);
        return null;
    }
}




module.exports = { get_token, get_full_token, get_user_id };
