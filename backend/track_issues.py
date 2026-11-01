from backend.database import retrieve_tracks_for_issues, count_pending_tracks
from typing import Callable, Dict, List, Optional
from backend.mb_enricher import is_mb_processed
from backend.utils import create_folder
from dataclasses import dataclass
from datetime import datetime
import os
import re

TRACK_ISSUES_PATH = "data/analysis/track_issues.txt"
VERSION_TITLE_PATTERN = re.compile(r"\b(remix|version|edit|mix|remaster(ed)?|live|acoustic|sped up|slowed|rework|flip)\b", re.IGNORECASE)




@dataclass(frozen=True)
class IssueSection:
    title: str
    is_issue: Callable[[Dict], bool]
    describe: Callable[[Dict], Optional[str]] = lambda track: None


def has_manual_date(track: Dict) -> bool:
    return bool(track.get("manual_release_date"))


def is_date_replaced_by_mb(track: Dict) -> bool:
    previous_date = track.get("release_date_before_mb")
    return bool(previous_date) and (previous_date != track.get("release_date")) and not(has_manual_date(track))


def is_version_title(name: str) -> bool:
    return VERSION_TITLE_PATTERN.search(name or "") is not None


def is_unvalidated_date(track: Dict) -> bool:
    """Tracks MB has not processed yet are left out: their date correction is deferred until the next /enrich/ + /search/."""
    return not(track.get("corrected_release_date")) and is_mb_processed(track)


def describe_mb_replacement(track: Dict) -> str:
    return f"{track.get('release_date_before_mb')} -> {track.get('release_date')} (MB)"


# A track leaves these sections when it has a manual date
TO_FIX_SECTIONS = [
    IssueSection("No ISRC", lambda track: not(track.get("isrc"))),
    IssueSection("MB unmatched", lambda track: bool(track.get("mb_unmatched"))),
    IssueSection("Date not validated", is_unvalidated_date),
    IssueSection("MB date on a version title", lambda track: is_date_replaced_by_mb(track) and is_version_title(track.get("name")), describe_mb_replacement),
]


def describe_track(track: Dict) -> str:
    artists = ", ".join(track.get("artists") or [])
    return f"{track.get('id')} | {track.get('name')} | {artists} | {track.get('release_date')} ({track.get('release_date_precision')})"


def build_section_lines(section: IssueSection, tracks: List[Dict]) -> List[str]:
    lines = [f"-- {section.title} ({len(tracks)}) --"]
    for track in tracks:
        lines.append(describe_track(track))
        detail = section.describe(track)
        if detail:
            lines.append(f"    {detail}")
    lines.append("")
    return lines


def build_info_lines(tracks: List[Dict], pending_count: int) -> List[str]:
    return [
        "== INFO ==",
        f"MB pending: {pending_count}",
        f"MB suspect: {sum(bool(track.get('mb_suspect')) for track in tracks)}",
        f"Dates replaced by MB: {sum(is_date_replaced_by_mb(track) for track in tracks)}",
        f"Year-precision dates: {sum(track.get('release_date_precision') == 'year' for track in tracks)}",
        f"Manual dates: {sum(has_manual_date(track) for track in tracks)}",
    ]


def build_track_issues_lines(tracks: List[Dict], pending_count: int) -> tuple[List[str], int]:
    """Returns the report lines and the number of tracks to fix."""
    tracks_to_check = sorted((track for track in tracks if not(has_manual_date(track))), key=lambda track: track.get("name") or "")
    issues_by_section = [
        (section, [track for track in tracks_to_check if section.is_issue(track)])
        for section in TO_FIX_SECTIONS
    ]
    to_fix_count = sum(len(section_tracks) for _, section_tracks in issues_by_section)

    lines = [
        f"Track issues - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "To clear a track, give it a manual date with scripts/set_manual_release_date.py: the correct date, or its current date to confirm it.",
        "",
        f"== TO FIX ({to_fix_count}) ==",
        "",
    ]
    for section, section_tracks in issues_by_section:
        lines += build_section_lines(section, section_tracks)
    lines += build_info_lines(tracks, pending_count)
    return lines, to_fix_count


def generate_track_issues(outputPath: str = TRACK_ISSUES_PATH) -> None:
    lines, to_fix_count = build_track_issues_lines(retrieve_tracks_for_issues(), count_pending_tracks())
    create_folder(os.path.dirname(outputPath))
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Track issues written to {outputPath}: {to_fix_count} tracks to fix.")
