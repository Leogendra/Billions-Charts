from backend.database import get_tracks_collection, get_artists_collection, MONGO_DB_NAME, DRY_RUN
from backend.utils import validate_track_id, infer_precision_from_date_string
from pymongo import UpdateOne
import datetime


DATE_FORMATS_BY_PRECISION = {"year": "%Y", "month": "%Y-%m", "day": "%Y-%m-%d"}

dates_to_update = {
    # "5gflgO9EPbIBf16n5TKnQS": "2004-03-04",  # Yo Voy
    # "2X6b7zLdIxCejd6GqVcQ9M": "2013-12-10",  # 3005
    # "2bnDTGikdoO8CwzlAPyBHR": "2010-04-27",  # Airplanes, Pt. II
    # "4gMgiXfqyzZLMhsksGmbQV": "1979-11-30",  # Another Brick in the Wall, Pt. 2
    # "4a9tbd947vo9K8Vti9JwcI": "2019-04-12",  # Boy With Luv
    # "4X5f3vT8MRuXF68pfjNte5": "2012-10-24",  # F**kin' Problems
    # "7BY005dacJkbO6EPiOh2wb": "1964-06-19",  # House Of The Rising Sun
    # "6PGoSes0D9eUDeeAafB2As": "2017-04-14",  # LOVE.
    # "7ghKr0pCYyPPyp7t1FH8k4": "2011-11-15",  # Les
    # "4Li2WHPkuyCdtmokzW2007": "2011-08-08",  # Ni**as In Paris
    # "2tTmW7RDtMQtBk7m2rYeSw": "2022-07-06",  # Quevedo: Bzrp Music Sessions
    # "4nrPB8O7Y7wsOCJdgXkthe": "2023-01-11",  # Shakira: Bzrp Music Sessions
    # "4Yaw2PmyOETOnEM3TCf98I": "2010-03-15",  # Eenie Meenie
    # "07GvNcU1WdyZJq3XxP0kZa": "1976-12-20",  # Go Your Own Way - 2004 Remaster
    # "2YpeDb67231RjR0MgVLzsG": "2019-04-05",  # Old Town Road Remix
    # "6V1bu6o1Yo5ZXnsCJU8Ovk": "2018-05-30",  # Girls Like You - Cardi B Version (MB: 2017-11-03 erroné)
    # "37BZB0z9T8Xu7U3e65qxFy": "2021-04-23",  # Save Your Tears (with Ariana Grande) (Remix)
    # "7rglLriMNBPAyuJOMGwi39": "2021-08-13",  # Cold Heart - PNAU Remix
    # "1MtUq6Wp1eQ8PC6BbPCj8P": "2015-07-24",  # I Took A Pill In Ibiza - Seeb Remix
    # "3Vo4wInECJQuz9BIBMOu8i": "2018-01-04",  # Finesse - Remix; feat. Cardi B
    # "4JNdwEfqwFRiAeEISC8RU8": "2023-02-24",  # Die For You (with Ariana Grande) - Remix
    # "2tFwfmceQa1Y6nRPhYbEtC": "2020-05-10",  # CÓMO SE SIENTE - Remix
    # "023OVLNzXhX0j7CxswUt6D": "2014-05-19",  # Cheerleader - Felix Jaehn Remix Radio Edit
    # "500mvzh7TRZ0YdnVeHhj8b": "2015-11-05",  # Light It Up - Remix
    # "72GVdRHK49beKrC1NqRCqj": "2019-09-13",  # Roses - Imanbek Remix
    # "0BZ5YlY2xnwfUmyGdiOMje": "2016-09-23",  # Call on Me - Ryan Riback Remix
    # "6WkJ2OK163XXS2oARUC9JM": "2014-06-10",  # Dancin - Krono Remix
}


def parse_manual_date(date_str: str) -> str:
    precision = infer_precision_from_date_string(date_str)
    if not(precision):
        raise ValueError(f"Invalid date format: {date_str!r}. Expected YYYY, YYYY-MM or YYYY-MM-DD.")
    try:
        datetime.datetime.strptime(date_str, DATE_FORMATS_BY_PRECISION[precision])
    except ValueError:
        raise ValueError(f"Invalid date: {date_str!r} does not exist.")
    return precision


def get_track(track_id: str) -> dict:
    track = get_tracks_collection().find_one({"id": track_id}, {"_id": 0})
    if (track is None):
        raise LookupError(f"Track {track_id} not found in database {MONGO_DB_NAME!r}.")
    return track


def get_artist_names(track: dict) -> list[str]:
    artist_ids = [artist["id"] for artist in track.get("artists", [])]
    names_by_id = {
        doc["id"]: doc.get("name")
        for doc in get_artists_collection().find({"id": {"$in": artist_ids}}, {"id": 1, "name": 1, "_id": 0})
    }
    return [names_by_id.get(artist_id) or artist_id for artist_id in artist_ids]


def print_current_dates(track: dict, new_date: str, new_precision: str) -> None:
    print(f"\nTrack:                   {track.get('name')} - {', '.join(get_artist_names(track))} ({track['id']})")
    print(f"release_date:            {track.get('release_date')}")
    print(f"corrected_release_date:  {track.get('corrected_release_date')}")
    print(f"release_date_before_mb:  {track.get('release_date_before_mb')}")
    print(f"mb_release_date:         {track.get('mb_release_date')}")
    if track.get("manual_release_date"):
        print(f"manual_release_date:     {track['manual_release_date']} -> will be replaced")
    else:
        print("manual_release_date:     none")
    print(f"New manual date:         {new_date} ({new_precision})")


def set_manual_release_dates(dates_by_track_id: dict[str, str]) -> None:
    updates = []
    for track_id, date_str in dates_by_track_id.items():
        if not(validate_track_id(track_id)):
            raise ValueError(f"Invalid track id: {track_id!r}.")
        precision = parse_manual_date(date_str)
        updates.append((get_track(track_id), date_str, precision))

    print(f"Database: {MONGO_DB_NAME}{' (DRY_RUN: nothing will be written)' if DRY_RUN else ''}")
    for track, date_str, precision in updates:
        print_current_dates(track, date_str, precision)
    input(f"\nPress Enter to set {len(updates)} manual date(s), Ctrl+C to cancel...")

    if (DRY_RUN):
        print("[Dry run] manual release dates not written.")
    else:
        get_tracks_collection().bulk_write([
            UpdateOne(
                {"id": track["id"]},
                {"$set": {"manual_release_date": date_str}},
            )
            for track, date_str, _ in updates
        ])
        print(f"{len(updates)} manual release date(s) saved. They are applied to release_date on the next /search/.")




if __name__ == "__main__":
    set_manual_release_dates(dates_to_update)
