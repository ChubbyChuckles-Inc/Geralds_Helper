"""Parsing logic for division (league) pages including Spielplan halves.

We assume caller already knows division id (L2P). We parse each Spielplan page
separately and tag matches with half=1 (Vorrunde) or 2 (Rückrunde).
"""

from __future__ import annotations

from bs4 import BeautifulSoup  # type: ignore
from datetime import datetime
from typing import List
import re

from .models import ScheduledMatch, Division, DivisionTeam


DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{2})")  # DD.MM.YY


def parse_matchplan(html: str, half: int | None = None) -> list[ScheduledMatch]:
    """Parse a Spielplan (match plan) table.

    Enhancements over earlier version:
        - Auto half detection: If caller passes half=None we infer from heading
          text containing 'Vorrunde' -> 1 or 'Rückrunde' -> 2 (defaults to 1).
        - Status flag capture: Single-letter bold markers (e.g. 'v', 't') between
          date and time columns are stored in ScheduledMatch.status_flag.
        - Match report URL: When a result cell contains an <a> to a Spielbericht
          (score or Vorbericht), we store its href.

    Markup traits:
        - Rows have id=Spiel<number>.
        - Header cells may be <td> instead of <th>.
        - Result may have score text, 'Vorbericht', or be empty; icons ignored.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: list[ScheduledMatch] = []

    # Half detection if not supplied
    if half is None:
        heading_text = soup.get_text(" ", strip=True)
        detected = 1
        if re.search(r"R[üu]ckrunde", heading_text, re.IGNORECASE):
            detected = 2
        elif re.search(r"Vorrunde", heading_text, re.IGNORECASE):
            detected = 1
        half = detected

    match_rows = soup.select("tr[id^=Spiel]")

    if not match_rows:
        # Fallback: previous generic approach (may still work for old markup)
        candidate = None
        for tbl in soup.find_all("table"):
            header_cells = [c.get_text(strip=True) for c in tbl.find_all(["th", "td"])[:12]]
            header_text = "|".join(header_cells)
            if "Heimmannschaft" in header_text and "Gastmannschaft" in header_text:
                candidate = tbl
                break
        if not candidate:
            return out
        match_rows = candidate.find_all("tr")

    SCORE_RE = re.compile(r"^(\d+):(\d+)")
    TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")

    for tr in match_rows:
        if not tr.get("id", "").startswith("Spiel"):
            # skip non-match rows that may be inside candidate table
            continue
        tds = tr.find_all("td")
        if len(tds) < 8:  # need at least up to away team
            continue

        # Extract match number (second cell usually). If that fails, look for first purely numeric cell.
        number = tds[1].get_text(strip=True) if len(tds) > 1 else ""
        if not number or not number.isdigit():
            for td in tds:
                txt = td.get_text(strip=True)
                if txt.isdigit():
                    number = txt
                    break
        # Locate date cell
        date_idx = None
        for idx, td in enumerate(tds):
            if DATE_RE.search(td.get_text(strip=True)):
                date_idx = idx
                break
        if date_idx is None:
            continue  # cannot parse without date
        date_raw = tds[date_idx].get_text(strip=True)
        dt = _parse_date(date_raw)
        if not dt:
            continue
        # Locate time after date (allow a single-letter status cell before time)
        time_idx = None
        status_flag: str | None = None
        for idx in range(date_idx + 1, len(tds)):
            txt = tds[idx].get_text(strip=True)
            if TIME_RE.match(txt):
                time_idx = idx
                break
            # capture one-letter status (bold letter often inside span/strong)
            if not status_flag and len(txt) == 1 and txt.isalpha():
                status_flag = txt
        if time_idx is None:
            continue  # skip if no time
        time_raw = tds[time_idx].get_text(strip=True)
        # Home and away are next two non-empty text cells
        home = away = ""
        next_texts: list[str] = []
        for idx in range(time_idx + 1, len(tds)):
            txt = tds[idx].get_text(" ", strip=True)
            if txt:
                next_texts.append(txt)
            if len(next_texts) >= 2:
                break
        if len(next_texts) < 2:
            continue
        home, away = next_texts[0], next_texts[1]
        # Result: scan remaining cells after away cell index
        # Determine away cell absolute index again
        away_abs_idx = None
        found_count = 0
        for idx in range(time_idx + 1, len(tds)):
            txt = tds[idx].get_text(" ", strip=True)
            if txt:
                found_count += 1
            if found_count == 2:  # away cell
                away_abs_idx = idx
                break
        result_raw = ""
        match_report_url: str | None = None
        if away_abs_idx is not None:
            for idx in range(away_abs_idx + 1, len(tds)):
                cell = tds[idx]
                txt = cell.get_text(strip=True)
                if not txt:
                    continue
                # Find anchor to Spielbericht for URL capture
                a = cell.find("a")
                if a and a.get("href") and "Spielbericht" in a.get("href"):
                    match_report_url = a.get("href")
                if SCORE_RE.match(txt) or txt.startswith("Vorbericht"):
                    result_raw = (
                        SCORE_RE.match(txt).group(0) if SCORE_RE.match(txt) else "Vorbericht"
                    )
                    # prefer anchor href if present in same cell
                    break
        sm = ScheduledMatch(
            number=number,
            date=dt.date(),
            time=time_raw,
            home=home,
            away=away,
            result_raw=result_raw,
            half=half,
            status_flag=status_flag,
            match_report_url=match_report_url,
        )
        sm.parse_scores()
        out.append(sm)
    return out


# Notes / Edge Cases handled by the heuristics above:
# - Status markers: A small cell containing a bold letter (v, t) directly after the date
#   does not interfere because we search forward for the first HH:MM time token.
# - Result icons: Additional <img> or tooltip spans after the score are ignored since
#   we only look at textual content of each cell (get_text(strip=True)).
# - Future matches: Display 'Vorbericht' often inside a cell with colspan=2. We normalize
#   result_raw to 'Vorbericht' (without trailing spaces/icons) so downstream logic can
#   detect unplayed matches via ScheduledMatch.is_played().
# - Missing scores: If neither a score nor 'Vorbericht' is present, result_raw remains ''
#   which also leads is_played() -> False.
# - Unexpected column shifts: Because we identify columns based on regex patterns for
#   date and time rather than absolute indices, insertion of new decorative columns
#   should not break parsing unless they mimic date/time formats.
# - Numeric match number fallback: If the expected second cell is not purely numeric,
#   we scan all cells for the first numeric token to assign as match number.


def parse_division_teams(html: str) -> list[DivisionTeam]:
    soup = BeautifulSoup(html, "html.parser")
    teams: list[DivisionTeam] = []
    # Find a table whose header has 'Mannschaft' only (division team list) OR use section anchor text
    for tbl in soup.find_all("table"):
        header_text = "|".join(th.get_text(strip=True) for th in tbl.find_all("th"))
        if (
            "Mannschaft" in header_text
            and "Gastmannschaft" not in header_text
            and "Heimmannschaft" not in header_text
        ):
            # treat all rows (skip header) first column as team name
            for tr in tbl.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if not tds:
                    continue
                a = tds[0].find("a")
                name = tds[0].get_text(" ", strip=True)
                href = a.get("href") if a else None
                dt = DivisionTeam(name=name, team_url=href)
                dt.derive_ids()
                teams.append(dt)
            break
    return teams


def _parse_date(txt: str):
    m = DATE_RE.search(txt)
    if not m:
        return None
    d, mth, y = m.groups()
    year_full = 2000 + int(y)
    try:
        return datetime(year_full, int(mth), int(d))
    except ValueError:
        return None


__all__ = ["parse_matchplan", "parse_division_teams"]
