from flask import Flask, jsonify, send_file, request
from backend.scrapper import fetch_playlist_infos
from backend.utils import create_folder
from backend.report import (
    generate_report,
    generate_leaderboard
)
from dotenv import load_dotenv
import datetime
import time
import os

load_dotenv()
app = Flask(__name__, static_folder="public", static_url_path="/")
PORT = os.getenv("PORT") or 3434
PASSWORD = os.getenv("PASSWORD") or 1234
BASE_URL = f"http://localhost:{PORT}"
WRITE_TO_DATABASE = True # If False, will write to json files instead of database




def check_password(password=""):
    time.sleep(1)
    if (password != PASSWORD):
        time.sleep(3)
        return jsonify(
            {
                "message": "Access denied!",
                "output": "You don't have access to this resource.",
            }
        )
    return None


def generate_sitemap(dateKey):
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://billions-charts.gatienh.fr/</loc>
        <lastmod>{dateKey}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    
    with open("public/sitemap.xml", "w") as f:
        f.write(sitemap)


@app.route("/search/", methods=["GET"])
def search():
    auth = check_password(request.args.get("password", ""))
    if auth:
        return auth
    dateKey = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    try:
        fetch_playlist_infos(dataPath, WRITE_TO_DATABASE)
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE) # Static update
        generate_sitemap(dateKey)
        return jsonify({
            "message": "Search completed!",
            "output": "The search of the playlist has been completed successfully.",
        })
    except Exception as error:
        print(f"[ERROR] {error}")
        return jsonify(
            {
                "message": "Search failed!",
                "output": error.__str__(),
            }
        )
    

@app.route("/report/<dateKey>/", methods=["GET"])
def report(dateKey):
    auth = check_password(request.args.get("password", ""))
    if auth:
        return auth
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    try:
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE)
        generate_sitemap(dateKey)
        return jsonify( {
            "message": "Report generated!",
            "output": "The report has been generated successfully.",
        })
    except Exception as error:
        return jsonify( {
            "message": "Report failed!",
            "output": error.__str__(),
        })


@app.route("/leaderboard/<dateKey>/", methods=["GET"])
def leaderboard(dateKey):
    auth = check_password(request.args.get("password", ""))
    if auth:
        return auth
    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{dateKey}.json"

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