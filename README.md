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
5. Create a `.env` file in the root directory and add your Spotify API and MongoDB credentials, the playlist ID you want to analyze, and a password for the admin routes. Set `DRY_RUN=true` to run without writing to the database:
   ```bash
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    MONGO_URI=mongodb_uri
    MONGO_DB_NAME=your_database_name
    PLAYLIST_ID=spotify_playlist_id
    PASSWORD=your_password
    FLASK_DEBUG=false
    DRY_RUN=false
   ```
6. Launch the application:
   ```bash
   python app.py
   ```

## API Endpoints

All admin endpoints require an `Authorization: Bearer <PASSWORD>` header.  
Only one admin task runs at a time: a call made while another one is running answers `409`.  
Admin endpoints answer `200` even when the task fails: check the `message` field.

`/search/` - retrieve the playlist's data and generate the report:
```bash
curl -X GET "http://localhost:3434/search/" -H "Authorization: Bearer your_password"
```

`/enrich/` - fetch MusicBrainz data for the tracks and artists not processed yet.
It's meant to run from a crontab at an off-peak hour, far enough from `/search/` (it will take more than an hour on a full database):
```bash
curl -X GET "http://localhost:3434/enrich/" -H "Authorization: Bearer your_password"
```

`/report/` - regenerate the report from already retrieved data:
```bash
curl -X GET "http://localhost:3434/report/2026-05-15/" -H "Authorization: Bearer your_password"
```

`/leaderboard/` - Update the leaderboard for a given date:
```bash
curl -X GET "http://localhost:3434/leaderboard/2026-05-15/" -H "Authorization: Bearer your_password"
```

## Release dates

Spotify often returns the date of a later album or compilation instead of the original release date. The dates are corrected in two steps:

- `/search/` searches Spotify for the earliest release sharing the track's ISRC, then applies the MusicBrainz data already stored in the database.
- `/enrich/` looks up each track's ISRC on MusicBrainz and stores the their fields (`mb_id`, `mb_title`, `mb_artists`, `mb_release_date`...). A recording whose title and artists do not match the Spotify track is flagged `mb_suspect`. An ISRC unknown to MusicBrainz is flagged `mb_unmatched`. Tracks and artists already processed are skipped.

The MusicBrainz date replaces the stored date only if the match is not suspect and the MusicBrainz date is earlier (by more than 7 days at day precision). The previous date is kept in `release_date_before_mb`.

## Contact

For any questions or suggestions, feel free to open an issue on GitHub or contact me directly at contact@billions-charts.com