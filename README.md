# Billions Charts

Billions Charts is a website that analyzes Spotify's **Billions Club** playlist, featuring songs with over one billion streams since its creation on **July 21, 2021**.  

The site is available at: [billions-charts.gatienh.fr](https://billions-charts.gatienh.fr/)

## Features
- Visualization of songs that have surpassed one billion streams
- Various statistics about the songs (release year, artists, etc.)
- Interactive charts to explore trends

## Technologies Used
Backend:  
- **Flask**
- **SpotAPI** for fetching data about the songs
- **Spotify API** for fetching data about the artists
- **MongoDB** for storing data  
  
Frontend:
- **HTML/CSS/JavaScript**
- **Chart.js** for displaying charts and statistics
- **Odometer.js** for displaying counters

## Upcoming Features
The website is still in development, and new features will be added in the future:  
- Enhancements to charts and user experience
- Addition of new types of visualizations


## Installation
If you want to test, contribute or use the project for another playlist, you can run the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/Leogendra/Billions-Charts
   ```
1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
1. Setup a [Spotify developer account](https://developer.spotify.com/dashboard/) and create a new application to get your `CLIENT_ID` and `CLIENT_SECRET`.
1. Setup a [MongoDB](https://www.mongodb.com/) account and create a new database to get your `MONGO_URI` (update the variable `WRITE_TO_DATABASE = False` in `app.py` if you want to write in local file instead of MongoDB).
1. Create a `.env` file in the root directory and add your Spotify API and MongoDB credentials, the playlist ID you want to analyze, and a password for the `search/` and `report/` routes:
   ```bash
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    MONGO_URI=mongodb_uri
    PLAYLIST_ID=spotify_playlisyt_id
    PASSWORD=1234
   ```
1. Launch the application:
   ```bash
   python app.py
   ```

## Contact

For any questions or suggestions, feel free to open an issue on GitHub or contact me directly at contact@billions-charts.gatienh.fr.