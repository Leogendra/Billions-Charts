import os
import re

PRECISION_RANK = {"year": 0, "month": 1, "day": 2}




def create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def normalize_date_for_comparison(date: str, precision: str) -> str:
    if (precision == "month"):
        return date + "-01"
    if (precision == "year"):
        return date + "-01-01"
    return date


def is_uncertain_isrc_date(date: str, precision: str) -> bool:
    # Spotify sometimes returns wrong YYYY-01-01 with "day" precision.
    return (precision == "day") and bool(re.match(r"^\d{4}-01-01$", date))


def is_new_date_preferred(oldDate: str, oldPrecision: str, newDate: str, newPrecision: str) -> bool:
    oldRank = PRECISION_RANK[oldPrecision]
    newRank = PRECISION_RANK[newPrecision]

    old_normalized = normalize_date_for_comparison(oldDate, oldPrecision)
    new_normalized = normalize_date_for_comparison(newDate, newPrecision)

    # Truncate both to the coarser precision (lower rank = more coarse)
    coarserPrecision = oldPrecision if (oldRank <= newRank) else newPrecision

    if (coarserPrecision == "year"):
        old_cmp, new_cmp = old_normalized[:4], new_normalized[:4]
    elif (coarserPrecision == "month"):
        old_cmp, new_cmp = old_normalized[:7], new_normalized[:7]
    else:
        old_cmp, new_cmp = old_normalized, new_normalized

    if (new_cmp < old_cmp):
        return True  # genuinely earlier
    if (new_cmp == old_cmp):
        return newRank > oldRank  # same period, prefer more precise
    return False


def is_new_candidate_preferred(
    oldDate: str, oldPrecision: str, oldUncertain: bool,
    newDate: str, newPrecision: str, newUncertain: bool,
) -> bool:
    # Same year + differing uncertainty -> prefer the certain one.
    if (oldDate[:4] == newDate[:4]) and (oldUncertain != newUncertain):
        return oldUncertain # if oldUncertain=True, then prefer new
    return is_new_date_preferred(oldDate, oldPrecision, newDate, newPrecision)


def validate_date_key(dateKey):
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", dateKey)


def validate_track_id(track_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", track_id)


def validate_artist_id(artist_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", artist_id)