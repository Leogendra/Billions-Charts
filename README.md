# Billions Charts

Billions Charts is a website that analyzes Spotify's *Billions Club* playlist, featuring songs with over one billion streams since its creation on July 2021.  

The website is available at [billions-charts.gatienh.fr](https://billions-charts.gatienh.fr/)

## Features
- Overview of key stats: total songs, percentages, durations, etc.
- Sort and explore tracks by streams, popularity, release date, or duration
- Explore artist stats by most streamed, most songs, total playtime
- Analyze tracks over time (by year and month)
- Additional charts: stream thresholds, track durations, etc

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

## Upcoming Features
The website is still in development, and new features will be added in the future:  
- Enhancements to charts and user experience
- Addition of new types of visualizations


## Installation
If you want to contribute or use the project for another playlist, you can run the project locally:

1. Clone the repository:
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Setup a [Spotify developer account](https://developer.spotify.com/dashboard/) and create a new application to get your `CLIENT_ID` and `CLIENT_SECRET`.
4. Setup a [MongoDB](https://www.mongodb.com/) account and create a new database to get your `MONGO_URI` (update the variable `WRITE_TO_DATABASE = False` in `app.py` if you want to write in local file instead of MongoDB).
5. Create a `.env` file in the root directory and add your Spotify API and MongoDB credentials, the playlist ID you want to analyze, and a password for the `search/` and `report/` routes:
   ```bash
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    MONGO_URI=mongodb_uri
    PLAYLIST_ID=spotify_playlisyt_id
    PASSWORD=1234
   ```
6. Launch the application:
   ```bash
   python app.py
   ```

## Contact

For any questions or suggestions, feel free to open an issue on GitHub or contact me directly at contact@billions-charts.gatienh.fr