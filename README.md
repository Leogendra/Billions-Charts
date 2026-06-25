# Billions Charts

Billions Charts is a website that analyzes Spotify's *Billions Club* playlist, featuring songs with over one billion streams since its creation on July 2021.  

The website is available at [billions-charts.com](https://billions-charts.com/)

## Features
- Overview of key stats: total songs, percentages, durations, etc.
- Sort and explore tracks by streams, popularity, release date, or duration.
- Explore artist stats by most streamed, most songs or total playtime.
- Analyze tracks over time (by year and month).
- Additional charts: stream thresholds, track durations, etc.

## Technologies Used
Backend:  
- **Flask**
- **[SpotAPI](https://github.com/Aran404/SpotAPI)** for fetching data about the songs
- **[Spotify API](https://developer.spotify.com/documentation/web-api)** for fetching data about the artists
- **[MongoDB](https://www.mongodb.com/products/platform/atlas-database?tck=exp-815&tck=exp-815)** for storing data  
  
Frontend:
- **HTML/CSS/JavaScript**
- **[Chart.js](https://www.chartjs.org/)** for displaying charts and statistics
- **[Odometer.js](https://github.hubspot.com/odometer/docs/welcome/)** for displaying counters


## Installation
If you want to contribute or use the project for another playlist, you can run the project locally:

1. Clone the repository:
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Setup a [Spotify developer account](https://developer.spotify.com/dashboard/) and create a new application to get your `CLIENT_ID` and `CLIENT_SECRET`.
4. Setup a [MongoDB](https://www.mongodb.com/) account and create a new database:
   - Get your `MONGO_URI` from the Atlas dashboard (Connect > Drivers).
   - Choose a name for your database and set it as `MONGO_DB_NAME` in `.env`.
   - Create the following 3 collections inside that database:
     - `playlists_headers`
     - `playlist_tracks`
     - `playlist_artists`
5. Create a `.env` file in the root directory and add your Spotify API and MongoDB credentials, the playlist ID you want to analyze, and a password for the `search/` and `report/` routes:
   ```bash
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    MONGO_URI=mongodb_uri
    MONGO_DB_NAME=your_database_name
    PLAYLIST_ID=spotify_playlist_id
    PASSWORD=your_password
    FLASK_DEBUG=false
   ```
6. Launch the application:
   ```bash
   python app.py
   ```

## API Endpoints

All admin endpoints require an `Authorization: Bearer <PASSWORD>` header.

`/search/` - retrieve the playlist's data and generate the report:
```bash
curl -X GET "http://localhost:3434/search/" -H "Authorization: Bearer your_password"
```

`/report/` - regenerate the report from already retrieved data:
```bash
curl -X GET "http://localhost:3434/report/2026-05-15/" -H "Authorization: Bearer your_password"
```

`/leaderboard/` - Update the leaderboard for a given date:
```bash
curl -X GET "http://localhost:3434/leaderboard/2026-05-15/" -H "Authorization: Bearer your_password"
```

## Contact

For any questions or suggestions, feel free to open an issue on GitHub or contact me directly at contact@billions-charts.com