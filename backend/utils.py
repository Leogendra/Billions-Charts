import os
import re



def create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def normalize_date_for_comparison(date: str, precision: str) -> str:
    if (precision == "month"):
        return date + "-01"
    if (precision == "year"):
        return date + "-01-01"
    return date


def validate_date_key(dateKey):
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", dateKey)


def validate_track_id(track_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", track_id)


def validate_artist_id(artist_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", artist_id)