"""Parsing logic for the club teams overview page.

Relies on anchors containing "Zum Team" and "Zum Wettbewerb" within the same
row (<tr>). We keep parsing tolerant: if expected anchors are missing we skip
the row rather than raising, to remain robust against minor site changes.
"""

from __future__ import annotations

from bs4 import BeautifulSoup  # type: ignore
from typing import List, Iterable
from .models import ClubTeam


def parse_club_overview(html: str, base_url: str) -> list[ClubTeam]:
    """Parse the club overview (teams list) page.

    Real-world HTML (2025/2026 season) uses a header row with <td> cells (not <th>),
    so earlier logic searching only for <th> missed the table entirely. We now:

    1. Scan all tables; a table qualifies if ANY row contains BOTH tokens
       "Mannschaft" and "Wettbewerb" in its *cell texts* (header or otherwise).
    2. From the first qualifying table, iterate rows and extract the first two
       NON-EMPTY text cells as (team_name, division_name).
    3. In the same row locate anchors whose labels contain "Zum Team" / "Zum Wettbewerb".
    4. Only emit rows having all four data points.

    This is intentionally tolerant: cosmetic spacer cells, extra columns, or
    class / structure changes should not break parsing as long as the textual
    semantics remain.
    """
    soup = BeautifulSoup(html, "html.parser")
    teams: list[ClubTeam] = []

    def _row_texts(cells: Iterable) -> list[str]:  # helper: collect stripped cell texts
        return [c.get_text(" ", strip=True) for c in cells]

    qualifying_table = None
    for tbl in soup.find_all("table"):
        found_header = False
        for tr in tbl.find_all("tr"):
            texts = _row_texts(tr.find_all(["td", "th"]))
            if any("Mannschaft" == t for t in texts) and any("Wettbewerb" == t for t in texts):
                found_header = True
                break
        if found_header:
            qualifying_table = tbl
            break

    if qualifying_table is None:
        return teams  # no recognizable table

    for tr in qualifying_table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        texts = [t.get_text(" ", strip=True) for t in tds]
        non_empty = [t for t in texts if t]
        # We only want atomic team rows, which in live HTML have pattern:
        # ['', '', '<team name>', '<division name>', 'Zum Team', 'Zum Wettbewerb', ...]
        # Instead of relying on position 0/1 we search anchors first.
        anchors = tr.find_all("a")
        if not anchors:
            continue
        has_team_anchor = any("zum team" in a.get_text(" ", strip=True).lower() for a in anchors)
        has_div_anchor = any(
            "zum wettbewerb" in a.get_text(" ", strip=True).lower() for a in anchors
        )
        if not (has_team_anchor and has_div_anchor):
            continue
        # Filter out giant aggregate rows that concatenate many teams (heuristic: > 120 chars in first non-empty cell)
        if (
            non_empty
            and len(non_empty[0]) > 120
            and "Mannschaft" in non_empty[0]
            and "Zum Team" in non_empty[0]
        ):
            continue
        # Collect candidate text cells (exclude ones that are exactly anchor labels)
        candidate_texts = [t for t in non_empty if t.lower() not in {"zum team", "zum wettbewerb"}]
        # Remove header tokens
        candidate_texts = [t for t in candidate_texts if t not in {"Mannschaft", "Wettbewerb"}]
        if len(candidate_texts) < 2:
            continue
        team_name = candidate_texts[0]
        division_name = candidate_texts[1]
        team_href = None
        division_href = None
        for a in anchors:
            label = a.get_text(" ", strip=True).lower()
            if "zum team" in label and team_href is None:
                team_href = a.get("href") or None
            elif "zum wettbewerb" in label and division_href is None:
                division_href = a.get("href") or None
        if not (team_name and division_name and team_href and division_href):
            continue
        ct = ClubTeam(
            name=team_name,
            division_name=division_name,
            team_url=_absolute_if_needed(team_href, base_url),
            division_url=_absolute_if_needed(division_href, base_url),
        )
        ct.derive_ids()
        teams.append(ct)

    # Fallback: anchor-centric extraction in case nested tables caused us to miss rows
    if not teams:
        seen_tr_ids: set[int] = set()
        for a in soup.find_all("a"):
            label = a.get_text(" ", strip=True).lower()
            if "zum team" not in label:
                continue
            tr = a.find_parent("tr")
            if not tr:
                continue
            # ensure we only process each row once
            if id(tr) in seen_tr_ids:
                continue
            seen_tr_ids.add(id(tr))
            # confirm row also has "Zum Wettbewerb"
            if not any(
                "zum wettbewerb" in (x.get_text(" ", strip=True).lower()) for x in tr.find_all("a")
            ):
                continue
            tds = tr.find_all("td")
            texts = [t.get_text(" ", strip=True) for t in tds]
            non_empty = [t for t in texts if t]
            if len(non_empty) < 2:
                continue
            team_name, division_name = non_empty[0], non_empty[1]
            team_href = None
            division_href = None
            for aa in tr.find_all("a"):
                l2 = aa.get_text(" ", strip=True).lower()
                if "zum team" in l2 and team_href is None:
                    team_href = aa.get("href") or None
                elif "zum wettbewerb" in l2 and division_href is None:
                    division_href = aa.get("href") or None
            if not (team_name and division_name and team_href and division_href):
                continue
            ct = ClubTeam(
                name=team_name,
                division_name=division_name,
                team_url=_absolute_if_needed(team_href, base_url),
                division_url=_absolute_if_needed(division_href, base_url),
            )
            ct.derive_ids()
            teams.append(ct)

    # Final fallback: derive team/division by sibling traversal from each 'Zum Team' anchor.
    if not teams:
        processed_pairs: set[str] = set()
        for a in soup.find_all("a"):
            txt = a.get_text(" ", strip=True).lower()
            if "zum team" not in txt:
                continue
            td = a.find_parent("td")
            if not td:
                continue
            # Find division td: first previous sibling td with non-empty text not containing 'Zum'
            div_td = td
            team_td = None
            # Walk backwards
            cursor = td.previous_sibling
            found_div_text = None
            while cursor is not None:
                if getattr(cursor, "name", None) == "td":
                    text = cursor.get_text(" ", strip=True)
                    if (
                        text
                        and "zum team" not in text.lower()
                        and "zum wettbewerb" not in text.lower()
                    ):
                        if found_div_text is None:
                            found_div_text = text
                        elif team_td is None:
                            team_td = cursor
                            break
                cursor = cursor.previous_sibling
            if not (found_div_text and team_td):
                continue
            team_text = team_td.get_text(" ", strip=True)
            division_text = found_div_text
            # Fetch division href (pair anchor with same L2P but without Mannschaften param)
            team_href = a.get("href") or ""
            division_href = None
            if team_href:
                # extract division id pattern L2P=digits
                import re

                m = re.search(r"L2P=(\d+)", team_href)
                div_id = m.group(1) if m else None
                if div_id:
                    # search for a sibling anchor whose href has same L2P without L3=Mannschaften
                    for aa in td.parent.find_all("a"):
                        href2 = aa.get("href") or ""
                        if href2 == team_href:
                            continue
                        if f"L2P={div_id}" in href2 and "Mannschaften" not in href2:
                            division_href = href2
                            break
            if not division_href:
                continue
            key = team_text + "|" + division_text
            if key in processed_pairs:
                continue
            processed_pairs.add(key)
            ct = ClubTeam(
                name=team_text,
                division_name=division_text,
                team_url=_absolute_if_needed(team_href, base_url),
                division_url=_absolute_if_needed(division_href, base_url),
            )
            ct.derive_ids()
            teams.append(ct)

    return teams


def _absolute_if_needed(href: str, base_url: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    # The site uses relative query-only refs (starting with ?L1=...)
    if href.startswith("?"):
        # trim trailing slash from base if present
        return base_url.rstrip("/") + "/" + href
    return base_url.rstrip("/") + "/" + href.lstrip("/")


__all__ = ["parse_club_overview"]
