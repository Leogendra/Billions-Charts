from flask import Flask, jsonify, send_file
from backend.scrapper import fetch_playlist_infos
from backend.utils import create_folder
from backend.report import (
    generate_report,
    generate_leaderboard
)
from dotenv import load_dotenv
import datetime
import os

load_dotenv()
app = Flask(__name__, static_folder="public", static_url_path="/")
PORT = os.getenv("PORT") or 3434
BASE_URL = f"http://localhost:{PORT}"
WRITE_TO_DATABASE = True # If False, will write to json files instead of database




@app.route("/search/", methods=["GET"])
def search():
    dateKey = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    # try:
    if 1:
        fetch_playlist_infos(dataPath, WRITE_TO_DATABASE)
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE) # Static update, TODO: make a clean backend instead of static file
        return jsonify({
            "message": "Search completed!",
            "output": "The search has been completed successfully.",
        })
    # except Exception as error:
    #     print(f"[ERROR] {error}")
    #     return jsonify(
    #         {
    #             "message": "Search failed!",
    #             "output": error.__str__(),
    #         }
    #     )
    

@app.route("/report/", methods=["GET"])
def report():
    dateKey = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    try:
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE)
        return jsonify( {
            "message": "Report generated!",
            "output": "The report has been generated successfully.",
        })
    except Exception as error:
        return jsonify( {
            "message": "Report failed!",
            "output": error.__str__(),
        })


@app.route("/leaderboard/", methods=["GET"])
def leaderboard():
    DATE_KEY = datetime.datetime.now().strftime("%Y-%m-%d")
    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{DATE_KEY}.json"

    try:
        generate_leaderboard(dataPath, WRITE_TO_DATABASE)
        return jsonify({
            "message": "Leaderboard updated!",
            "output": "The leaderboard has been generated successfully.",
        })
    except Exception as error:
        return jsonify({
            "message": "Leaderboard failed!",
            "output": error.__str__(),
        })


@app.route("/", methods=["GET"])
def read_root():
    return send_file("public/index.html")




if __name__ == "__main__":
    app.run(debug=True, port=PORT)
    print(f"Server is running on http://localhost:{PORT}")