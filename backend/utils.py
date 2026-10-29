from typing import Optional
import unicodedata
import datetime
import os
import re

PRECISION_RANK = {"year": 0, "month": 1, "day": 2}




def create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def normalize_name(name: str) -> str:
    without_accents = "".join(
        c for c in unicodedata.normalize("NFKD", name or "")
        if not(unicodedata.combining(c))
    )
    return " ".join(re.sub(r"[^\w]+", " ", without_accents.lower()).split())


def normalize_title(title: str) -> str:
    """normalize_name without the version details: "(...)", "[...]" and a " - ..." suffix ("Cupid - Twin Version" -> "cupid")."""
    base_title = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", title or "")
    base_title = re.split(r"\s[-–—]\s", base_title)[0]
    # a title made only of details ("(Intro)") keeps them
    return normalize_name(base_title) or normalize_name(title)


def normalize_date_for_comparison(date: str, precision: str) -> str:
    if (precision == "month"):
        return date + "-01"
    if (precision == "year"):
        return date + "-01-01"
    return date


def is_uncertain_isrc_date(date: str, precision: str) -> bool:
    # Spotify sometimes returns wrong YYYY-01-01 with "day" precision.
    return (precision == "day") and bool(re.match(r"^\d{4}-01-01$", date))


def infer_precision_from_date_string(date_str: Optional[str]) -> Optional[str]:
    if (not date_str or not isinstance(date_str, str)):
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        return "day"
    if re.fullmatch(r"\d{4}-\d{2}", date_str):
        return "month"
    if re.fullmatch(r"\d{4}", date_str):
        return "year"
    return None


def is_new_date_preferred(
    oldDate: str, oldPrecision: str,
    newDate: str, newPrecision: str,
    oldUncertain: Optional[bool] = None,
    newUncertain: Optional[bool] = None,
) -> bool:
    # Same year + differing uncertainty -> prefer the certain one.
    if (oldUncertain is not None) and (newUncertain is not None):
        if (oldDate[:4] == newDate[:4]) and (oldUncertain != newUncertain):
            return oldUncertain  # if oldUncertain=True, then prefer new

    oldRank = PRECISION_RANK[oldPrecision]
    newRank = PRECISION_RANK[newPrecision]

    old_normalized = normalize_date_for_comparison(oldDate, oldPrecision)
    new_normalized = normalize_date_for_comparison(newDate, newPrecision)

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


def correct_uncertain_date(
    date: Optional[str],
    precision: Optional[str],
    mb_date: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    if not(is_uncertain_isrc_date(date, precision)):
        return (date, precision)

    # if the MB date is uncertain or earlier than the Spotify date, downgrade to year precision.
    mb_precision = infer_precision_from_date_string(mb_date)
    if (mb_date and mb_precision):
        if is_uncertain_isrc_date(mb_date, mb_precision):
            return (min(date[:4], mb_date[:4]), "year")
        if (mb_date[:4] <= date[:4]):
            return (mb_date, mb_precision)
    return (date[:4], "year")


def is_mb_date_preferred(stored_date: Optional[str], mb_date: Optional[str]) -> bool:
    mb_precision = infer_precision_from_date_string(mb_date)
    stored_precision = infer_precision_from_date_string(stored_date)
    if not(mb_precision) or not(stored_precision):
        return False
    if is_uncertain_isrc_date(mb_date, mb_precision):
        return False

    mb_rank = PRECISION_RANK[mb_precision]
    stored_rank = PRECISION_RANK[stored_precision]
    if (mb_rank < stored_rank):
        return False
    if (mb_rank > stored_rank):
        return mb_date[:len(stored_date)] <= stored_date
    if (mb_precision == "day"):
        gap = datetime.date.fromisoformat(stored_date) - datetime.date.fromisoformat(mb_date)
        return gap.days > 7
    return mb_date < stored_date


def validate_date_key(dateKey):
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", dateKey)


def validate_track_id(track_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", track_id)


def validate_artist_id(artist_id):
    return re.fullmatch(r"[0-9A-Za-z]{22}", artist_id)