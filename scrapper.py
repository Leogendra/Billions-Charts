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


def clean_playlist(tracksPath):
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
    with open(tracksPath, 'w', encoding='utf-8') as file:
        json.dump(playlist, file, indent=4)

    print(f"Playlist cleaned and saved in {tracksPath}")


def get_play_count_with_selenium(track_id):
    url = f"https://open.spotify.com/track/{track_id}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
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


def retrieve_playcounts(full_data, outputPath):
    tracks = full_data["data"]["items"]
    for i in range(len(tracks)):
        track = tracks[i]
        print(f"Traitement de la piste {i+1}/{len(tracks)}...", end="\r")
        if ("playcount" not in track) or (track["playcount"] is None):
            track_id = track["id"]
            play_count = get_play_count_with_selenium(track_id)
            if (play_count):
                tracks[i]["playcount"] = play_count
            else:
                print(f"Playcount manquant pour {track['name']}")

    full_data["data"]["items"] = tracks

    with open(outputPath, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=4)

    print("Mise à jour du fichier test.json terminée.")


def format_number(number):
    return f"{number/1_000_000_000:.2f}B"



if __name__ == "__main__":

    # format YYYY-MM-DD
    TIME_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks_{TIME_KEY}.json"

    fetch_tracks(dataPath)
    clean_playlist(dataPath)
    exit(0)




    if os.path.exists(dataPath):
        with open(dataPath, "r", encoding="utf-8") as f:
            tracks_data = json.load(f)
    else:
        raise FileNotFoundError("Le fichier billions.json est introuvable.")

    retrieve_playcounts(tracks_data, dataPath)

    tracks = tracks_data["data"]["items"]
    print(f"Nombre de pistes à traiter: {len(tracks)}")

    tracks.sort(key=lambda x: x["playcount"], reverse=True)

    print("Top des pistes les plus écoutées:")
    with open("data/leaderboard_tracks.txt", "w", encoding="utf-8") as f:
        for i in range(len(tracks)):
            track = tracks[i]
            f.write(f"{i+1}. {format_number(track['playcount'])} - {track['name'].split("-")[0].split("(")[0].strip()}, by {', '.join(track['artists'][i]['name'] for i in range(len(track['artists'])))}\n")

    artists_count = {}
    for track in tracks:
        for artist in track["artists"]:
            artist_name = artist["name"]
            artists_count[artist_name] = artists_count.get(artist_name, 0) + 1
    
    artists_count = [{"name": k, "count": v} for k, v in artists_count.items()]
    artists_count.sort(key=lambda x: x["count"], reverse=True)

    
    print("Top des artistes avec les plus de sons à 1B+:")
    with open("data/leaderboard_artists.txt", "w", encoding="utf-8") as f:
        for i in range(len(artists_count)):
            artist = artists_count[i]
            f.write(f"{i+1}. {artist['name']}: {artist['count']} tracks \n")
    
    artists_playcount = {}
    for track in tracks:
        for artist in track["artists"]:
            artist_name = artist["name"]
            artists_playcount[artist_name] = artists_playcount.get(artist_name, 0) + track["playcount"]
    
    artists_playcount = [{"name": k, "playcount": v} for k, v in artists_playcount.items()]
    artists_playcount.sort(key=lambda x: x["playcount"], reverse=True)

    print("Top des artistes avec les plus de streams:")
    with open("data/leaderboard_streams.txt", "w", encoding="utf-8") as f:
        for i in range(len(artists_playcount)):
            artist = artists_playcount[i]
            f.write(f"{i+1}. {artist['name']}: {format_number(artist['playcount'])} tracks \n")