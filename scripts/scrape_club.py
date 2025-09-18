from __future__ import annotations

"""Manual CLI for scraping a club URL and printing a summary.

Usage:
  python -m scripts.scrape_club "<club_overview_url>"
"""

import sys
import os
from pathlib import Path

# Ensure src/ on path when invoked as a module from repo root
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scraping.orchestrator import scrape_club  # type: ignore  # noqa: E402
from scraping.fetch import CachedFetcher, SessionFetcher  # type: ignore  # noqa: E402

try:
    from scraping.browser_fetch import HeadlessFetcher  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover - optional dependency not installed
    HeadlessFetcher = None  # type: ignore
from scraping.convert import scheduled_to_matches  # type: ignore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Provide club overview URL as first argument.", file=sys.stderr)
        return 2
    # Simple arg parsing: --session (use SessionFetcher) --no-cache
    use_session = False
    use_headless = False
    no_cache = False
    filtered = []
    for a in argv:
        if a == "--session":
            use_session = True
            continue
        if a == "--headless":
            use_headless = True
            continue
        if a == "--no-cache":
            no_cache = True
            continue
        filtered.append(a)
    # Offline snapshot flags
    club_html_path: str | None = None
    divisions_dir: str | None = None
    teams_dir: str | None = None
    remaining = []
    it = iter(filtered)
    for token in it:
        if token == "--club-html":
            try:
                club_html_path = next(it)
            except StopIteration:
                print("--club-html requires a file path", file=sys.stderr)
                return 2
            continue
        if token == "--divisions-dir":
            try:
                divisions_dir = next(it)
            except StopIteration:
                print("--divisions-dir requires a path", file=sys.stderr)
                return 2
            continue
        if token == "--teams-dir":
            try:
                teams_dir = next(it)
            except StopIteration:
                print("--teams-dir requires a path", file=sys.stderr)
                return 2
            continue
        remaining.append(token)
    if not remaining and not club_html_path:
        print("Missing URL (unless offline --club-html given).", file=sys.stderr)
        return 2
    url = remaining[0] if remaining else "https://www.tischtennislive.de/"
    if club_html_path:
        # Offline mode: we won't need a fetcher for the club overview, but still might for divisions
        # Use a minimal CachedFetcher so downstream division fetch attempts are cached
        fetcher = CachedFetcher(throttle=0.5, ttl_seconds=0 if no_cache else 6 * 3600)
    elif use_headless:
        if HeadlessFetcher is None:
            print("Headless mode requested but Playwright not installed.", file=sys.stderr)
            return 3
        fetcher = HeadlessFetcher()
    elif use_session:
        fetcher = SessionFetcher(throttle=0.5)
    else:
        fetcher = CachedFetcher(throttle=0.5, ttl_seconds=0 if no_cache else 6 * 3600)

    debug = bool(os.environ.get("DEBUG_SCRAPE"))
    if debug:
        print("[debug] DEBUG_SCRAPE=1 -> enabling HTML dump + keyword diagnostics")
    # If debugging, fetch raw HTML once directly through fetcher to inspect before orchestration
    if debug and not club_html_path:
        try:
            raw_html = fetcher.get(url)
            dump_path = Path("latest_club_overview.html")
            dump_path.write_text(raw_html, encoding="utf-8", errors="ignore")
            contains_team = raw_html.count("Zum Team")
            contains_wb = raw_html.count("Zum Wettbewerb")
            print(f"[debug] Saved fetched HTML -> {dump_path} (len={len(raw_html)})")
            print(
                f"[debug] Occurrences: 'Zum Team'={contains_team}, 'Zum Wettbewerb'={contains_wb}"
            )
        except Exception as e:  # pragma: no cover
            print(f"[debug] Failed initial fetch for diagnostics: {e}")
    # Offline override: if club_html_path provided, read it and directly parse, then optionally load divisions/teams from dirs.
    if club_html_path:
        # We import parser locally to avoid circular issues.
        from scraping.parse_club import parse_club_overview  # type: ignore

        html = Path(club_html_path).read_text(encoding="utf-8", errors="ignore")
        teams = parse_club_overview(html, "https://www.tischtennislive.de")
        # Build minimal divisions from team division names
        from scraping.models import Division

        divisions: dict[str, Division] = {}
        for t in teams:
            if t.division_id and t.division_id not in divisions:
                divisions[t.division_id] = Division(
                    name=t.division_name, division_id=t.division_id, season=""
                )
        # Optionally load division match plans if directory given
        if divisions_dir:
            from scraping.parse_division import parse_matchplan

            for div_id, div in divisions.items():
                for half in (1, 2):
                    file_path = Path(divisions_dir) / f"{div_id}_half{half}.html"
                    if file_path.exists():
                        try:
                            dhtml = file_path.read_text(encoding="utf-8", errors="ignore")
                            matches = parse_matchplan(dhtml, half)
                            for m in matches:
                                div.add_match(m)
                        except Exception:
                            pass
        # Optionally load team player pages
        team_players: dict[str, list] | None = None
        if teams_dir:
            from scraping.parse_team import parse_team_players

            team_players = {}
            for t in teams:
                if not t.team_id:
                    continue
                file_path = Path(teams_dir) / f"{t.team_id}.html"
                if file_path.exists():
                    try:
                        thtml = file_path.read_text(encoding="utf-8", errors="ignore")
                        plist = parse_team_players(thtml)
                        if plist:
                            team_players[t.team_id] = plist
                    except Exception:
                        pass
        # Create a result-like object inline (avoid importing orchestrator complexities)
        from dataclasses import dataclass
        from typing import Any

        @dataclass
        class _Result:
            club_url: str
            teams: list
            divisions: dict
            team_players: dict | None

        result = _Result(club_url=url, teams=teams, divisions=divisions, team_players=team_players)
    else:
        result = scrape_club(url, fetcher=fetcher, include_team_players=True)
    if debug and not result.teams:
        print(
            "[debug] Parser returned 0 teams. Consider comparing latest_club_overview.html with scrape_debug_club.html"
        )
    print(f"Scraped {len(result.teams)} club teams; {len(result.divisions)} divisions")
    total_matches = sum(len(d.matches) for d in result.divisions.values())
    print(f"Total scheduled matches: {total_matches}")
    for div_id, div in result.divisions.items():
        played = sum(1 for m in div.matches if m.is_played())
        print(f" - {div.name} ({div_id}): {len(div.matches)} matches ({played} played)")
    if result.team_players:
        sample_key = next(iter(result.team_players)) if result.team_players else None
        if sample_key:
            print(
                f"Sample team {sample_key} players: {[p.name for p in result.team_players[sample_key]][:5]}"
            )
    # Convert to Match objects (example)
    all_sched = [m for d in result.divisions.values() for m in d.matches]
    converted = scheduled_to_matches(all_sched)
    print(f"Converted to {len(converted)} Match model instances.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
