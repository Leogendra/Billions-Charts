from backend.report import generate_report, generate_leaderboard
from flask import Flask, request, jsonify, send_file, abort
from flask_limiter.util import get_remote_address
from backend.scrapper import fetch_playlist_infos
from backend.utils import create_folder
from flask_limiter import Limiter
from dotenv import load_dotenv
from functools import wraps
import datetime
import time
import os
import re


load_dotenv()
app = Flask(__name__, static_folder="public", static_url_path="/")
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=[],
)
PORT = os.getenv("PORT") or 3434
BASE_URL = f"http://localhost:{PORT}"

WRITE_TO_DATABASE = os.getenv("WRITE_TO_DATABASE", "true").lower() == "true"
PASSWORD = os.getenv("PASSWORD", "")
if not(PASSWORD):
    raise RuntimeError("PASSWORD environment variable is not set")




def validate_date_key(dateKey):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dateKey):
        print(f"[ERROR] dateKey: {dateKey} is invalid.")
        abort(400, description="Invalid dateKey format.")
    else:
        print(f"[INFO] dateKey: {dateKey} is valid.")


def require_password(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        time.sleep(1)
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ") if auth_header.startswith("Bearer ") else ""
        if (token != PASSWORD):
            time.sleep(3)
            return jsonify({
                "message": "Access denied!",
                "output": "You don't have access to this resource.",
            })
        return f(*args, **kwargs)
    return decorated


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
@limiter.limit("5 per minute")
@require_password
def search():
    dateKey = datetime.datetime.now().strftime("%Y-%m-%d")
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    try:
        fetch_playlist_infos(dataPath, WRITE_TO_DATABASE, dateKey)
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE, dateKey)
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
@limiter.limit("5 per minute")
@require_password
def report(dateKey):
    validate_date_key(dateKey)
    dataPath = f"data/tracks/tracks_{dateKey}.json"
    reportPublicPath = f"public/data/report.json"

    try:
        reportVersion = generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE, dateKey)
        generate_sitemap(dateKey)
        return jsonify( {
            "message": "Report generated!",
            "output": f"The report has been generated successfully. Version: {reportVersion}",
        })
    except Exception as error:
        return jsonify( {
            "message": "Report failed!",
            "output": error.__str__(),
        })


@app.route("/leaderboard/<dateKey>/", methods=["GET"])
@limiter.limit("5 per minute")
@require_password
def leaderboard(dateKey):
    validate_date_key(dateKey)
    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{dateKey}.json"

    try:
        generate_leaderboard(dataPath, WRITE_TO_DATABASE, dateKey)
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
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=PORT)
    print(f"Server is running on http://localhost:{PORT}")