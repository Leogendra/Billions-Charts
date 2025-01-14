from flask import Flask, jsonify, send_file
from backend.scrapper import (
    fetch_playlist_infos,
    fetch_songs_infos,
    generate_leaderboard,
)
from backend.report import generate_report
from backend.utils import create_folder
from dotenv import load_dotenv
import datetime
import os

load_dotenv()
app = Flask(__name__, static_folder="public", static_url_path="/")
PORT = os.getenv("PORT") or 3434
BASE_IMAGE_DIR = "public"
BASE_URL = f"http://localhost:{PORT}"




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
                "output": "The search has been completed successfully.",
            }
        )
    except Exception as error:
        return jsonify(
            {
                "message": "Search failed!",
                "output": error.__str__(),
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
                "output": "The report has been generated successfully.",
            }
        )
    except Exception as error:
        return jsonify(
            {
                "message": "Report failed!",
                "output": error.__str__(),
            }
        )


@app.route("/leaderboard/", methods=["GET"])
def leaderboard():
    DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{DATE_KEY}.json"

    try:
        generate_leaderboard(dataPath)
        return jsonify(
            {
                "message": "Leaderboard updated!",
                "output": "The leaderboard has been generated successfully.",
            }
        )
    except Exception as error:
        return jsonify(
            {
                "message": "Leaderboard failed!",
                "output": error.__str__(),
            }
        )


@app.route("/", methods=["GET"])
def read_root():
    return send_file("public/index.html")




if __name__ == "__main__":
    app.run(debug=True, port=PORT)
    print(f"Server is running on http://localhost:{PORT}")