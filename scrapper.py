import os
import json
import time
import datetime
import requests
import http.client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from threading import Lock

lock = Lock()
load_dotenv()
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
PLAYLIST_ID = os.getenv("PLAYLIST_ID")




def fetch_tracks(outputFile):
    if os.path.exists(outputFile):
        print("File already exists. Using stored data.")
        return
    
    print("Requesting playlist tracks...")
    api_url = "https://spotify-downloader9.p.rapidapi.com/playlistTracks"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "spotify-downloader9.p.rapidapi.com",
    }

    default_json = {
        "total": 0,
        "items": [],
        "generatedTimeStamp": 0,
    }

    offset = 0
    is_next = True
    while is_next:
        try:
            response = requests.get(
                api_url,
                headers=headers,
                params={
                    "id": PLAYLIST_ID,
                    "limit": 100,
                    "offset": offset,
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                default_json["items"].extend(data["data"]["items"])
                default_json["generatedTimeStamp"] = data.get("generatedTimeStamp", int(time.time() * 1000))
                is_next = data["data"].get("next", False)
                print(f"Fetched {offset+len(data["data"]["items"])} / {data['data']['total']} tracks...", end="\r")
                offset += 100
            else:
                print("Error with response:", data.get("message"))
                is_next = False
        except requests.RequestException as error:
            print("Error while fetching playlist:", error)
            is_next = False

    if not(default_json["items"]):
        print("No tracks found in playlist.")
    else:
        default_json["total"] = len(default_json["items"])
        print(f"Fetched {default_json["total"]} tracks!          ")
            
        with open(outputFile, "w", encoding="utf-8") as file:
            json.dump(default_json, file, indent=4)
        print(f"Tracks saved in {outputFile}")


def clean_playlist(tracksPath, cleanedPath):
    with open(tracksPath, 'r', encoding='utf-8') as file:
        playlist = json.load(file)

    tracks_raw = playlist["items"]
    cleaned_tracks = [
        {
            "name": track["name"],
            "artists": [
                {
                    "name": artist["name"], 
                    "id": artist["id"]
                }
                for artist in track["artists"]
            ],
            "release_date": track["album"]["release_date"],
            "release_date_precision": track["album"]["release_date_precision"],
            "duration": track["duration_ms"],
            "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "popularity": track["popularity"],
            "playcount": track["playcount"] if "playcount" in track else None,
            "duration_ms": track["duration_ms"],
            "spotify_url": track["external_urls"]["spotify"],
            "id": track["id"],
        }
        for track in tracks_raw
    ]

    playlist["items"] = cleaned_tracks
    with open(cleanedPath, 'w', encoding='utf-8') as file:
        json.dump(playlist, file, indent=4)

    print(f"Playlist cleaned and saved in {cleanedPath}")


def get_play_count_with_selenium(track_id):
    url = f"https://open.spotify.com/track/{track_id}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        play_count_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="playcount"]')))
        return int(play_count_span.text.strip().replace('\u202f', ''))
    except Exception as e:
        print(f"Erreur pour {track_id}: {e}")
        return None
    finally:
        driver.quit()


def process_track(track):
    track_id = track["id"]
    if ("playcount" in track) and (track["playcount"] is not None):
        return track
    play_count = get_play_count_with_selenium(track_id)
    if play_count is not None:
        with lock:
            track["playcount"] = play_count
    return track


def retrieve_playcounts(tracksPath):
    if os.path.exists(tracksPath):
        with open(tracksPath, "r", encoding="utf-8") as f:
            tracks_data = json.load(f)
    else:
        raise FileNotFoundError("The file does not exist.")
    
    tracks = tracks_data["items"]

    for i in range(len(tracks)):
        track = tracks[i]
        print(f"Processing track {i+1}/{len(tracks)}...", end="\r")
        if ("playcount" not in track) or (track["playcount"] is None) or (track["playcount"] <= 0):
            track_id = track["id"]
            playcount = get_play_count_with_selenium(track_id)
            if (playcount):
                tracks[i]["playcount"] = playcount
            else:
                print(f"Playcount not found for {track['name']}")

    tracks_data["items"] = tracks

    with open(tracksPath, "w", encoding="utf-8") as f:
        json.dump(tracks_data, f, ensure_ascii=False, indent=4)

    print(f"Playcounts retrieved and saved in {tracksPath}")


def format_number(number):
    return f"{number/1_000_000_000:.2f}B"



if __name__ == "__main__":

    TIME_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks_{TIME_KEY}.json"
    dataCleanedPath = f"data/tracks_{TIME_KEY}_cleaned.json"

    fetch_tracks(dataPath)
    clean_playlist(dataPath, dataCleanedPath)
    retrieve_playcounts(dataCleanedPath)