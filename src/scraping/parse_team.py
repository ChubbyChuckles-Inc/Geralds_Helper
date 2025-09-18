"""Parser for a single team (Mannschaften) detail page extracting player stats.

Heuristic based on screenshot: A table with headers including 'Einzel Bilanzen'
or a segment where Position / Spieler / Gesamt / LivePZ appear.
We capture player name and LivePZ (rating) plus overall balance string.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup  # type: ignore


@dataclass(slots=True)
class TeamPlayerStat:
    name: str
    live_pz: int | None
    balance: str | None


def parse_team_players(html: str) -> list[TeamPlayerStat]:
    soup = BeautifulSoup(html, "html.parser")
    players: list[TeamPlayerStat] = []
    # Find tables that have header cells containing 'Spieler' and maybe 'LivePZ'
    for tbl in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        if not headers:
            continue
        header_join = "|".join(headers).lower()
        if "spieler" in header_join and ("livepz" in header_join or "gesamt" in header_join):
            # Assume rows after header contain player stats
            for tr in tbl.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue
                name = (
                    tds[1].get_text(" ", strip=True)
                    if headers[0].lower().startswith("position")
                    else tds[0].get_text(" ", strip=True)
                )
                live_pz = None
                balance = None
                # attempt to find integer in any cell labeled LivePZ or near end
                for td in tds:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        # likely rating (heuristic: choose largest <= 3000?)
                        val = int(txt)
                        if 800 < val < 3000:
                            live_pz = val
                    if ":" in txt or txt.count("-") == 1:
                        balance = balance or txt
                players.append(TeamPlayerStat(name=name, live_pz=live_pz, balance=balance))
            break
    return players


__all__ = ["TeamPlayerStat", "parse_team_players"]
