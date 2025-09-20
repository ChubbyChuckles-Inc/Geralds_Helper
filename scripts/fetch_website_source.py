#!/usr/bin/env python3
"""
Script to fetch the source code of a website and save it to the experiment directory.
Compatible with Python 3.13.7
"""

import urllib.request
import urllib.error
import os
import re
from datetime import datetime


def fetch_website_source(url: str, output_filename: str = None) -> str:
    """
    Fetch the source code of a website and save it to the experiment directory.

    Args:
        url: The URL to fetch
        output_filename: Optional filename for the output. If not provided,
                        will use a timestamp-based filename.

    Returns:
        The path to the saved file

    Raises:
        urllib.error.URLError: If the URL cannot be accessed
        urllib.error.HTTPError: If the server returns an error
    """
    try:
        print(f"Fetching content from: {url}")

        # Create request with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')

        print(f"Successfully fetched {len(content)} characters")

        # Generate filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"website_source_{timestamp}.html"

        # Ensure experiment directory exists
        experiment_dir = "experiment"
        os.makedirs(experiment_dir, exist_ok=True)

        # Full path for output file
        output_path = os.path.join(experiment_dir, output_filename)

        # Save content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Content saved to: {output_path}")
        return output_path

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        raise
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def extract_team_links(html_content: str) -> tuple[list[str], list[str], list[str]]:
    """
    Extract team roster links from the HTML content and generate match plan links for both halves.

    Args:
        html_content: The HTML content to parse

    Returns:
        A tuple containing (team_roster_links, first_half_match_plan_links, second_half_match_plan_links)
    """
    # Extract team roster links (with L3=Mannschaften&L3P= parameter)
    team_roster_pattern = r'href="([^"]*L3=Mannschaften[^"]*)"'
    team_roster_links = re.findall(team_roster_pattern, html_content)

    # Clean up the links by removing duplicates
    team_roster_links = list(set(team_roster_links))

    # Generate match plan links for both halves from team roster links
    first_half_match_plan_links = []
    second_half_match_plan_links = []
    root_url = "https://leipzig.tischtennislive.de/"

    for roster_link in team_roster_links:
        # Extract the division part (everything up to L3=)
        division_part = re.match(r'(\?[^&]*&L2=TTStaffeln&L2P=[^&]*)', roster_link)
        if division_part:
            division_url = division_part.group(1)
            # Build the match plan links for both halves
            first_half_link = f"{root_url}{division_url}&L3=Spielplan&L3P=1"
            second_half_link = f"{root_url}{division_url}&L3=Spielplan&L3P=2"

            first_half_match_plan_links.append(first_half_link)
            second_half_match_plan_links.append(second_half_link)

    return team_roster_links, first_half_match_plan_links, second_half_match_plan_links


def fetch_team_roster_sources(team_roster_links: list[str], experiment_dir: str = "experiment") -> list[str]:
    """
    Fetch the source code of each team roster page and save to experiment directory.

    Args:
        team_roster_links: List of team roster URLs to fetch
        experiment_dir: Directory to save the files

    Returns:
        List of file paths where team roster sources were saved
    """
    saved_files = []
    root_url = "https://leipzig.tischtennislive.de/"

    for i, roster_link in enumerate(team_roster_links, 1):
        try:
            # Add root URL if not present
            if not roster_link.startswith('http'):
                full_url = f"{root_url}{roster_link}"
            else:
                full_url = roster_link

            print(f"Fetching team roster {i}/{len(team_roster_links)}: {full_url}")

            # Create request with headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')

            # Generate filename based on team identifier
            team_id = re.search(r'L2P=([^&]*)', roster_link)
            if team_id:
                filename = f"team_roster_L2P_{team_id.group(1)}.html"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"team_roster_{i}_{timestamp}.html"

            # Ensure experiment directory exists
            os.makedirs(experiment_dir, exist_ok=True)

            # Full path for output file
            output_path = os.path.join(experiment_dir, filename)

            # Save content to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            saved_files.append(output_path)
            print(f"  Saved to: {output_path}")

        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason} for {full_url}")
        except urllib.error.URLError as e:
            print(f"  URL Error: {e.reason} for {full_url}")
        except Exception as e:
            print(f"  Unexpected error: {e} for {full_url}")

    return saved_files


def extract_player_data_from_rosters(experiment_dir: str = "experiment") -> dict:
    """
    Extract player names and LivePZ values from all team roster HTML files.

    Args:
        experiment_dir: Directory containing the team roster HTML files

    Returns:
        Dictionary with team IDs as keys and list of (player_name, live_pz) tuples as values
    """
    import glob

    # Find all team roster files
    roster_files = glob.glob(os.path.join(experiment_dir, "team_roster_L2P_*.html"))

    all_players_data = {}

    for roster_file in roster_files:
        try:
            # Extract team ID from filename
            team_id = re.search(r'team_roster_L2P_(\d+)\.html', os.path.basename(roster_file))
            if not team_id:
                continue

            team_id = team_id.group(1)

            # Read the HTML content
            with open(roster_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract player data using a more targeted approach
            # Based on the HTML structure provided by the user, we need to find:
            # 1. Player names in links with href containing "Spieler"
            # 2. LivePZ values in cells with class="tooltip" and title containing "LivePZ-Wert"

            # Find all player links - including those with empty LivePZ cells
            player_links = re.findall(r'<a[^>]*href="[^"]*Spieler[^"]*"[^>]*>([^<]+)</a>', content, re.IGNORECASE)

            # Also try to find players by looking for the row structure
            # This will help capture players that might be missed by the first pattern
            additional_players = re.findall(r'<tr[^>]*>.*?Spieler[^>]*>.*?href="[^"]*Spieler[^"]*"[^>]*>([^<]+)</a>', content, re.DOTALL | re.IGNORECASE)

            # Combine and deduplicate
            all_player_links = list(set(player_links + additional_players))

            # Find all LivePZ cells - handle cases with additional text in title and HTML content
            live_pz_cells = re.findall(r'<td[^>]*class="tooltip"[^>]*title="LivePZ-Wert[^"]*"[^>]*>.*?</td>', content, re.IGNORECASE | re.DOTALL)

            # Clean up the extracted data
            clean_player_links = [name.strip() for name in all_player_links if name.strip()]

            # Clean LivePZ values - handle HTML content and extract just the number
            clean_live_pz = []
            for cell in live_pz_cells:
                # Extract content between the opening and closing tags
                cell_content = re.sub(r'<td[^>]*class="tooltip"[^>]*title="LivePZ-Wert[^"]*"[^>]*>(.*?)</td>', r'\1', cell, flags=re.IGNORECASE | re.DOTALL)

                if cell_content.strip():
                    # Remove HTML tags and extract the number
                    clean_pz = re.sub(r'<[^>]+>', '', cell_content)  # Remove HTML tags
                    clean_pz = re.sub(r'&nbsp;', '', clean_pz)  # Remove &nbsp;
                    clean_pz = re.sub(r'\s+', '', clean_pz)  # Remove extra whitespace
                    # Extract the last number found (in case there are multiple)
                    numbers = re.findall(r'\d+', clean_pz)
                    if numbers:
                        clean_live_pz.append(numbers[-1])  # Take the last number found
                    else:
                        clean_live_pz.append('')  # Empty if no number found
                else:
                    clean_live_pz.append('')  # Empty cell

            # Create a comprehensive approach to extract all players and their LivePZ values
            players = []

            # First, find ALL player names by looking for Spieler links
            all_player_names = []
            player_name_pattern = r'href="[^"]*Spieler[^"]*"[^>]*>([^<]+)</a>'
            all_player_matches = re.findall(player_name_pattern, content, re.IGNORECASE)

            for match in all_player_matches:
                clean_name = match.strip()
                if clean_name and clean_name not in all_player_names:
                    all_player_names.append(clean_name)

            # Now try to find LivePZ values for each player
            for player_name in all_player_names:
                # Look for this specific player's row
                player_row_pattern = f'href="[^"]*Spieler[^"]*"[^>]*>{re.escape(player_name)}</a>.*?<td[^>]*class="tooltip"[^>]*title="LivePZ-Wert[^"]*"[^>]*>(.*?)</td>'
                player_row_match = re.search(player_row_pattern, content, re.DOTALL | re.IGNORECASE)

                if player_row_match:
                    live_pz_content = player_row_match.group(1)
                    if live_pz_content.strip():
                        # Clean the LivePZ content
                        clean_pz = re.sub(r'<[^>]+>', '', live_pz_content)  # Remove HTML tags
                        clean_pz = re.sub(r'&nbsp;', '', clean_pz)  # Remove &nbsp;
                        clean_pz = re.sub(r'\s+', '', clean_pz)  # Remove extra whitespace
                        numbers = re.findall(r'\d+', clean_pz)
                        if numbers:
                            players.append((player_name, numbers[-1]))
                        else:
                            players.append((player_name, ''))
                    else:
                        # Empty LivePZ cell
                        players.append((player_name, ''))
                else:
                    # Player found but no LivePZ cell found - still include them
                    players.append((player_name, ''))

            # If no players found with this approach, fall back to the original method
            if not players:
                # Fallback: try to match by position
                for i, player_name in enumerate(clean_player_links):
                    if i < len(clean_live_pz):
                        players.append((player_name, clean_live_pz[i]))
                    else:
                        players.append((player_name, ''))

            # Clean up the extracted data
            players_data = []
            for player_name, live_pz in players:
                # Clean player name (remove extra whitespace)
                clean_name = re.sub(r'\s+', ' ', player_name.strip())
                # Clean LivePZ value (remove extra whitespace and &nbsp;)
                clean_pz = re.sub(r'\s+', '', live_pz.strip().replace('&nbsp;', ''))

                if clean_name and clean_pz:
                    players_data.append((clean_name, clean_pz))

            if players_data:
                all_players_data[team_id] = players_data
                print(f"  Extracted {len(players_data)} players from team {team_id}")

        except Exception as e:
            print(f"  Error processing {roster_file}: {e}")

    return all_players_data


def main():
    """Main function to run the script."""
    url = "https://leipzig.tischtennislive.de/?L1=Public&L2=Verein&L2P=2294&Page=Spielbetrieb&Sportart=96&Saison=2025"

    try:
        saved_file = fetch_website_source(url)
        print(f"\nSuccess! Website source code saved to: {saved_file}")

        # Read the saved content and extract links
        with open(saved_file, 'r', encoding='utf-8') as f:
            content = f.read()

        team_roster_links, first_half_match_plan_links, second_half_match_plan_links = extract_team_links(content)

        print(f"\n{'='*60}")
        print("EXTRACTED LINKS:")
        print(f"{'='*60}")

        # Add root URL to team roster links
        root_url = "https://leipzig.tischtennislive.de/"
        full_team_roster_links = [f"{root_url}{link}" for link in team_roster_links]

        # Define experiment directory for later use
        experiment_dir = "experiment"

        print(f"\nTeam Roster Links ({len(full_team_roster_links)} found):")
        for i, link in enumerate(full_team_roster_links, 1):
            print(f"  {i}. {link}")

        print(f"\nFirst Half Match Plan Links ({len(first_half_match_plan_links)} found):")
        for i, link in enumerate(first_half_match_plan_links, 1):
            print(f"  {i}. {link}")

        print(f"\nSecond Half Match Plan Links ({len(second_half_match_plan_links)} found):")
        for i, link in enumerate(second_half_match_plan_links, 1):
            print(f"  {i}. {link}")

        print(f"\n{'='*60}")
        print("FETCHING TEAM ROSTER SOURCES:")
        print(f"{'='*60}")

        # Fetch the source code of each team roster page
        saved_roster_files = fetch_team_roster_sources(full_team_roster_links)

        print(f"\n{'='*60}")
        print("SUMMARY:")
        print(f"{'='*60}")
        print(f"Team Roster Links Found: {len(full_team_roster_links)}")
        print(f"First Half Match Plan Links Generated: {len(first_half_match_plan_links)}")
        print(f"Second Half Match Plan Links Generated: {len(second_half_match_plan_links)}")
        print(f"Team Roster Source Files Downloaded: {len(saved_roster_files)}")
        print(f"\nFiles saved to: {experiment_dir}/")
        print(f"{'='*60}")

        # Extract player data from all roster files
        print(f"\n{'='*60}")
        print("EXTRACTING PLAYER DATA:")
        print(f"{'='*60}")

        players_data = extract_player_data_from_rosters(experiment_dir)

        # Display extracted player data
        total_players = 0
        for team_id in sorted(players_data.keys()):
            players = players_data[team_id]
            total_players += len(players)
            print(f"\nTeam {team_id} ({len(players)} players):")
            print("-" * 40)
            for i, (player_name, live_pz) in enumerate(players, 1):
                print(f"  {i:2d}. {player_name:<30} LivePZ: {live_pz}")

        print(f"\n{'='*60}")
        print("PLAYER DATA SUMMARY:")
        print(f"{'='*60}")
        print(f"Teams processed: {len(players_data)}")
        print(f"Total players found: {total_players}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nFailed to fetch website source: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())