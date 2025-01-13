from backend.scrapper import (
    fetch_playlist_infos,
    fetch_songs_infos,
    generate_leaderboard,
)
from backend.report import generate_report
from backend.utils import create_folder
from flask import Flask, jsonify
from dotenv import load_dotenv
import datetime
import os

load_dotenv()
app = Flask(__name__)
PORT = os.getenv("PORT") or 3434
BASE_IMAGE_DIR = "public"
BASE_URL = f"http://localhost:{PORT}"




def main_function():
    DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder("data/tracks")

    dataPath = f"../data/tracks/tracks_{DATE_KEY}.json"
    reportPath = f"../data/reports/report_{DATE_KEY}.json"

    fetch_playlist_infos(dataPath)
    fetch_songs_infos(dataPath)

    generate_leaderboard(dataPath)
    # generate_report(dataPath, reportPath)



@app.route("/search/", methods=["GET"])
def search():
    DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder("data/tracks")
    dataPath = f"data/tracks/tracks_{DATE_KEY}.json"

    try:
        fetch_playlist_infos(dataPath)
        fetch_songs_infos(dataPath)
        return jsonify(
            {
                "message": "Search completed!",
                "data": "The search has been completed successfully.",
            }
        )
    except Exception as error:
        return jsonify(
            {
                "message": "Search failed!",
                "data": error.__str__(),
            }
        )
    

@app.route("/report/", methods=["GET"])
def report():
    DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{DATE_KEY}.json"
    reportPath = f"data/reports/report_{DATE_KEY}.json"

    try:
        generate_report(dataPath, reportPath)
        return jsonify(
            {
                "message": "Report generated!",
                "data": "The report has been generated successfully.",
            }
        )
    except Exception as error:
        return jsonify(
            {
                "message": "Report failed!",
                "data": error.__str__(),
            }
        )


@app.route("/", methods=["GET"])
def read_root():
    return jsonify(
        {
            "message": (
                "Welcome to Billions Charts!\n"
                "This is the web API for the Billions Charts project.\n"
                "You can use the following endpoints:\n"
                "GET /search/ - To search for the latest playlist and songs.\n"
                "GET /report/ - To generate the report for the curent day."
            )
        }
    )




if __name__ == "__main__":
    app.run(debug=True, port=PORT)
    print(f"Server is running on http://localhost:{PORT}")
