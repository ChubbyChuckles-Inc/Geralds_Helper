"""Parser for a single team (Mannschaften) detail page extracting player stats.

Heuristic based on screenshot: A table with headers including 'Einzel Bilanzen'
or a segment where Position / Spieler / Gesamt / LivePZ appear.
We capture player name and LivePZ (rating) plus overall balance string.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re
from bs4 import BeautifulSoup  # type: ignore


@dataclass
class TeamPlayerStat:
    name: str
    live_pz: int | None
    balance: str | None


def parse_team_players(html: str) -> list[TeamPlayerStat]:
    """Parse a team detail page extracting player name, rating (LivePZ) and balance.

    Supports two layouts observed so far:
    1. Traditional table using <th> for headers (Position | Spieler | Gesamt | LivePZ)
    2. Layout where the first row is styled as header but uses only <td> cells (snippet provided by user).

    Heuristics:
    - Identify candidate table if header row (th cells OR first tr td cells) contains 'Spieler' AND ('LivePZ' or 'Gesamt').
    - Player rows usually contain an <a> tag with player name; if absent choose the longest textual cell that looks like a name.
    - Rating (LivePZ) chosen as the right‑most 3-4 digit integer 800 < n < 3000 in the row.
    - Balance chosen as the right‑most token matching \d+:\d+ (prefer overall 'Gesamt' column rather than per‑PK columns).
    - Skip summary rows containing only 'Gesamt'.
    """
    soup = BeautifulSoup(html, "html.parser")
    players: list[TeamPlayerStat] = []
    for tbl in soup.find_all("table"):
        rows = tbl.find_all("tr")
        if not rows:
            continue
        # Build header tokens: prefer <th>, else use first row <td>
        ths = rows[0].find_all("th")
        if ths:
            headers = [th.get_text(" ", strip=True) for th in ths]
        else:
            headers = [td.get_text(" ", strip=True) for td in rows[0].find_all("td")]
        header_join = "|".join(h.lower() for h in headers)
        if not ("spieler" in header_join and ("livepz" in header_join or "gesamt" in header_join)):
            continue
        # Parse subsequent rows
        for tr in rows[1:]:
            tds = tr.find_all("td")
            if not tds:
                continue
            row_text = "|".join(td.get_text(" ", strip=True).lower() for td in tds)
            # Skip summary/total rows
            if "gesamt" in row_text and not tr.find("a"):
                continue
            # Extract name
            a = tr.find("a")
            if a:
                name = a.get_text(" ", strip=True)
            else:
                # Fallback: choose the cell with the longest text that looks like a name
                cand = [
                    td.get_text(" ", strip=True)
                    for td in tds
                    if 2 <= len(td.get_text(strip=True).split()) <= 3  # 1-2 spaces typical
                ]
                name = max(cand, key=len) if cand else tds[0].get_text(" ", strip=True)
            # Derive rating (right-most plausible integer)
            live_pz = None
            for td in reversed(tds):
                txt = td.get_text(" ", strip=True)
                # Find last 3-4 digit integer in txt
                for match in re.findall(r"(\d{3,4})", txt):
                    val = int(match)
                    if 800 < val < 3000:
                        live_pz = val
                        break
                if live_pz is not None:
                    break
            # Derive balance (right-most d+:d+)
            balance = None
            for td in reversed(tds):
                txt = td.get_text(" ", strip=True)
                if re.fullmatch(r"\d+:\d+", txt):
                    balance = txt
                    break
            players.append(TeamPlayerStat(name=name, live_pz=live_pz, balance=balance))
        # Stop after first matching table
        if players:
            break
    return players


__all__ = ["TeamPlayerStat", "parse_team_players"]
