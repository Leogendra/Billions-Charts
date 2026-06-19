from backend.utils import create_folder, normalize_date_for_comparison, validate_date_key, validate_track_id, validate_artist_id
from backend.report import generate_report, generate_leaderboard, generate_search_ids
from backend.database import retrieve_track_by_id, retrieve_artist_by_id
from flask import Flask, request, jsonify, send_file, abort
from flask_limiter.util import get_remote_address
from backend.scrapper import fetch_playlist_infos
from backend.og_image import generate_og_image
from flask_limiter import Limiter
from dotenv import load_dotenv
from functools import wraps
import logging.handlers
import datetime
import logging
import time
import os
import re


load_dotenv()

class StripANSIColors(logging.Formatter):
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    def format(self, record):
        msg = super().format(record)
        return self.ansi_re.sub("", msg)

os.makedirs("logs", exist_ok=True)
_handler = logging.FileHandler("logs/app.log")
_handler.setFormatter(StripANSIColors("%(asctime)s %(levelname)s %(message)s"))
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger().addHandler(_handler)

_access_handler = logging.handlers.RotatingFileHandler(
    "logs/access.log", maxBytes=10 * 1024 * 1024, backupCount=5
)
_access_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(_access_handler)
access_logger.propagate = False

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




def require_password(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
        <loc>https://billions-charts.com/</loc>
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
    searchIdsPublicPath = f"public/data/search_ids.json"

    try:
        fetch_playlist_infos(dataPath, WRITE_TO_DATABASE, dateKey)
        generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE, dateKey)
        generate_search_ids(searchIdsPublicPath)
        generate_sitemap(dateKey)
        generate_og_image(reportPublicPath)
        return jsonify({
            "message": "Search completed!",
            "output": "The search of the playlist has been completed successfully.",
        })
    except Exception as error:
        logging.exception(error)
        return jsonify(
            {
                "message": "Search failed!",
                "output": "An internal error occurred.",
            }
        )
    

@app.route("/report/<dateKey>/", methods=["GET"])
@limiter.limit("5 per minute")
@require_password
def report(dateKey):
    if not(validate_date_key(dateKey)):
        abort(400, description="Invalid dateKey format.")
    
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
        logging.exception(error)
        return jsonify( {
            "message": "Report failed!",
            "output": "An internal error occurred.",
        })


@app.route("/leaderboard/<dateKey>/", methods=["GET"])
@limiter.limit("5 per minute")
@require_password
def leaderboard(dateKey):
    if not(validate_date_key(dateKey)):
        abort(400, description="Invalid dateKey format.")

    create_folder("data/reports")
    dataPath = f"data/tracks/tracks_{dateKey}.json"

    try:
        generate_leaderboard(dataPath, WRITE_TO_DATABASE, dateKey)
        return jsonify({
            "message": "Leaderboard updated!",
            "output": "The leaderboard has been generated successfully.",
        })
    except Exception as error:
        logging.exception(error)
        return jsonify({
            "message": "Leaderboard failed!",
            "output": "An internal error occurred.",
        })


@app.route("/track/<track_id>/", methods=["GET"])
@limiter.limit("30 per minute")
def get_track(track_id):
    if not(validate_track_id(track_id)):
        abort(400, description="Invalid track_id format.")

    access_logger.info("track %s", track_id)

    try:
        track = retrieve_track_by_id(track_id)
    except Exception as error:
        logging.exception(error)
        return jsonify({"message": "Internal error", "output": "An internal error occurred."}), 500

    if (track is None):
        abort(404, description="Track not found.")

    if (track.get("corrected_release_date") and (track.get("release_date_precision") == "day") and track.get("added_at")):
        billion_date = track["added_at"].split("T")[0]
        track["billion_time"] = (datetime.datetime.strptime(billion_date, "%Y-%m-%d") - datetime.datetime.strptime(track["release_date"], "%Y-%m-%d")).days

    if (
        (track.get("corrected_release_date") is not False)
        and track.get("release_date")
        and track.get("release_date_precision")
        and (track.get("playcount") is not None)
    ):
        normalized = normalize_date_for_comparison(track["release_date"], track["release_date_precision"])
        daysSinceRelease = max((datetime.datetime.now() - datetime.datetime.strptime(normalized, "%Y-%m-%d")).days, 1)
        track["streams_per_day"] = track["playcount"] // daysSinceRelease

    track.pop("corrected_release_date", None)
    return jsonify(track)


@app.route("/artist/<artist_id>/", methods=["GET"])
@limiter.limit("30 per minute")
def get_artist(artist_id):
    if not(validate_artist_id(artist_id)):
        abort(400, description="Invalid artist_id format.")

    access_logger.info("artist %s", artist_id)

    try:
        artist = retrieve_artist_by_id(artist_id)
    except Exception as error:
        logging.exception(error)
        return jsonify({"message": "Internal error", "output": "An internal error occurred."}), 500

    if (artist is None):
        abort(404, description="Artist not found.")

    return jsonify(artist)


@app.route("/", methods=["GET"])
@limiter.limit("5 per minute")
def read_root():
    return send_file("public/index.html")




if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"Server is running on http://localhost:{PORT}")
    app.run(debug=debug, port=PORT)