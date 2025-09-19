# Table Tennis Team Manager

[![CI](https://github.com/ChubbyChuckles/project-template/actions/workflows/ci.yml/badge.svg)](https://github.com/ChubbyChuckles/project-template/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/project-template/badge/?version=latest)](https://project-template.readthedocs.io)

This project is an evolving Table Tennis Team Management Tool featuring:

- Modern PyQt6 GUI (in development)
- Player & team roster management with Q-TTR ratings
- Match scheduling + opponent roster scraping (planned)
- Optimization engine for lineup strength and availability (foundational version implemented)
- Deterministic test suite and modular architecture adhering to repository "Copilot Instructions"

Recent notable additions:

- Match reminders with timer-driven popup notifications (in-memory)
- Aggregate match statistics panel (wins / draws / losses + goals)
- Scenario history for optimization runs with markdown export & preset save/load
- Defensive GUI launcher with clearer diagnostics for PyQt6/platform plugin issues
- Initial league scraping framework (club teams, divisions, match schedules)
  - Extended: score parsing, player roster extraction (LivePZ), caching, Match model conversion (`scripts/scrape_club.py`).
  - NEW: Robust roster parser now supports alternate team page layout where the header row uses only <td> cells (no <th>) containing tokens like `Spieler`, `Gesamt`, `LivePZ`. This improves compatibility with the live `tischtennislive.de` structure for some divisions.

### NEW: GUI Team Selection, Async Loading & Schedule Import

You can now populate the Players tab directly from a scraped club team roster:

1. Click `Load Team…` in the Players tab toolbar.
2. Enter the full club overview URL (the page that lists all your club teams).
3. (Optional) Provide a saved offline HTML snapshot via `Club HTML…` for deterministic offline parsing.
4. Click `Fetch Teams` – a list of club teams appears.
5. Select the desired team and press `Load Roster`.
6. The Players table is replaced with parsed players; `LivePZ` values become `Q-TTR` (fallback 1200 if missing).

Async Enhancements (latest):

- Team fetching and roster loading now run in background threads (non-blocking UI).
- Optional "Import Schedule" checkbox (enabled by default) converts the division Spielplan into Matches automatically.
- Status messages appear in the main window status bar (e.g. "Fetching club teams…", "Importing schedule…").
- On success, imported matches populate the Matches tab (including played results where available).
- Cancellation & Retry: Long-running fetch tasks can be cancelled mid-flight; transient HTTP failures are retried with exponential backoff (jitter to be added in future iteration).

Persistence:

- The app stores recent scraping context in `config/app_settings.json` under `recent` (last club URL, team name/id, division URL) so future UX can preload values (read accessors already exposed in `AppSettings`).

Notes:

- For deterministic/offline operation, provide saved HTML snapshots via the dialog. Currently supported overrides:
  - Club Overview HTML
  - Team Page HTML (roster)
  - Division Matchplan HTML
    Paths are optional; when specified they fully bypass network I/O for that artifact.
- Schedule import is best-effort; a failure logs a warning but doesn't cancel roster loading.
- Result scores are marked as completed matches; future matches remain open with notes indicating half and status flag.

Troubleshooting:

- If no teams are parsed, confirm the URL is the club overview page containing "Zum Team" links.
- Live site variability (dynamic content or auth) may require providing an offline snapshot until authenticated/XHR scraping is implemented.

## Setup Instructions

This template automates the setup of a new Python project. Follow these steps to initialize a new project after cloning or using this template.

### Prerequisites (Outside VS Code)

Before starting, ensure the following are set up on your Windows 10 system:

1. **Install Git**:

   - Download and install Git for Windows from [https://git-scm.com/](https://git-scm.com/).
   - Verify installation by running in Command Prompt or PowerShell:
     ```powershell
     git --version
     ```
   - Ensure Git is added to your system PATH (selected during installation).

2. **Install Python**:

   - Ensure Python 3.12.3 or later is installed. Download from [https://www.python.org/](https://www.python.org/).
   - Verify installation:
     ```powershell
     python --version
     ```
   - Ensure `pip` is available:
     ```powershell
     python -m pip --version
     ```

3. **Set PowerShell Execution Policy**:

   - To run PowerShell scripts like `scripts/commit-push.ps1`, set the execution policy to allow scripts:
     ```powershell
     Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
     ```
   - Run this in an elevated PowerShell prompt (right-click PowerShell and select "Run as administrator").
   - If prompted, type `Y` to confirm.

4. **Install Visual Studio Code (Optional but Recommended)**:
   - Download and install VS Code from [https://code.visualstudio.com/](https://code.visualstudio.com/).
   - Install the Python extension for VS Code (by Microsoft) for better Python support:
     - Open VS Code, go to the Extensions view (`Ctrl+Shift+X`), search for "Python," and install the Microsoft Python extension.

### Quick Start

```powershell
git clone https://github.com/ChubbyChuckles-Inc/Geralds_Helper.git
cd Geralds_Helper
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main            # CLI bootstrap
python -m src.main --gui      # Launch GUI (early framework)
```

Logs are written to `logs/app.log`. Configuration file is created at `config/app_settings.json` on first run.

GUI preview features:

- QMainWindow base with tabbed placeholders (Players, Matches, Optimization)
- Theme switching (light/dark) via `config/app_settings.json`
- Splash screen + window size persistence
- Offscreen-friendly tests (`QT_QPA_PLATFORM=offscreen`)

Important: Always run the GUI using the virtual environment interpreter. If you see an error like `ModuleNotFoundError: No module named 'PyQt6'` you likely launched with the system Python. Activate the venv (e.g. `.venv\\Scripts\\activate`) and retry `python -m src.main --gui`.

### Current Players Tab Features (Implemented)

- Roster table with inline editable columns: `Name`, `Team`, `Q-TTR`
- Add Player dialog with validation (name required, rating >= 0)
- Case-insensitive live filtering by name or team
- JSON import/export (CSV groundwork present; coming soon)
- Deterministic, unit-tested model (`Player`) and table behaviors
- Availability management: calendar toggling (counts shown in `Avail Days` column)
- Player profile dialog (double-click row) with Q-TTR edit, team, and photo path field
- Drag-and-drop row reordering (internal move) with underlying model sync
- Bulk operations: multi-select rows, bulk team assignment, clear availability
- Stats placeholder panel (future Q-TTR history charts will render here)

Note: In environments without PyQt6 (e.g. minimal CI runners), GUI tests are gracefully skipped; non-GUI serialization and model tests still run.

### Current Matches Tab Features (Initial Increment)

- Integrated `Matches` tab with calendar + per-day match list
- Add/Edit/Delete matches via simple dialog (home, away, location, notes)
- JSON import/export for matches (round-trip serialization)
- Basic same-day team conflict detection with tooltip + row note annotation (_conflict_)
- Internal `Match` dataclass + conflict detection helper with unit tests
- Skips GUI tests gracefully when PyQt6 unavailable (mirrors Players tab strategy)

Recent Enhancements:

- Score tracking (home/away scores) and completion flag
- Result entry fields added to match dialog
- History browser capabilities: All Dates toggle + free-text search filter
- Lineup editing (comma-separated list in dialog) with serialization
- Aggregate statistics panel (totals, win/draw breakdown) + live reminder count
- Basic reminder system: schedule near-term popups for selected match (in-memory)

Planned next for Matches:

- Enhanced lineup selection integrating Players tab metadata
- Persistent reminder storage & snooze/postpone actions
- Extended statistics visualization (charts, per-team head-to-head)
- Direct navigation from schedule entries to online match report when URLs captured

### Current Optimization Tab Features (Expanded Foundation)

- Lineup size selector and objective dropdown ("qttr_max", "balance")
- Availability date filter (players with empty availability = always available; otherwise must match date)
- Instant brute-force optimization for small rosters (sum of Q-TTR or spread minimization)
- Results table listing chosen lineup (Name, Team, Q-TTR)
- Summary line with total, average, and spread metrics
- Scenario history table (ID, time, objective, size, totals, spread)
- Markdown export of scenario history (`optimization_history.md`)
- Preset save/load (size + objective) persisted to `config/optimization_presets.json`
- Deterministic test coverage: optimizer objectives, scenario export, availability filtering

Planned next for Optimization:

- Multi-scenario comparative analytics (side-by-side performance deltas)
- Reasoning / rationale narrative for lineup selection
- Genetic / heuristic algorithms for larger pools
- Multi-objective weighting (blend balance vs total strength)
- Validation and reasonableness checks (flag extreme spreads)

### Setup Steps (Legacy Template Instructions)

1. **Clone the Repository or Create a New Project**:

   - Clone this repository:
     ```powershell
     git clone https://github.com/ChubbyChuckles/project-template.git <new-project-name>
     cd <new-project-name>
     ```
   - Alternatively, use the "Use this template" button on GitHub to create a new repository, then clone it:
     ```powershell
     git clone https://github.com/<your-username>/<your-new-repo>.git
     cd <your-new-repo>
     ```

2. **Run the Bootstrap Script**:

   - Run the `bootstrap.py` script to automate setup:
     ```powershell
     python bootstrap.py
     ```
   - Follow the prompts:
     - **Enter the new project name** (e.g., `MyNewProject`).
     - **Enter the new GitHub repository URL** (e.g., `https://github.com/ChubbyChuckles/my-new-project.git`).
   - The script will:
     - Create a virtual environment (`.venv`).
     - Install dependencies from `requirements.txt` (e.g., `numpy`, `pandas`, `matplotlib`, `sphinx`, `pre-commit`).
     - Create a `.env` file in the root directory with the project name and placeholder environment variables.
     - Update `README.md`, `setup.py`, and `docs/source/conf.py` with the new project name and author.
     - Initialize a Git repository (if needed) and set the new remote URL.
     - Create and switch to a `develop` branch.
     - Run `scripts/commit-push.ps1` to stage, commit, and push changes to the `develop` branch.

3. **Inside VS Code**:
   - **Open the Project**:
     - Launch VS Code and open the project folder:
       ```powershell
       code .
       ```
     - Alternatively, open VS Code, go to `File > Open Folder`, and select the project directory (e.g., `C:\Users\Chuck\Desktop\CR_AI_Engineering\Projekte\Github_Repo_Template\<new-project-name>`).
   - **Select Python Interpreter**:
     - Press `Ctrl+Shift+P` to open the Command Palette.
     - Type `Python: Select Interpreter` and select the virtual environment (`.venv\Scripts\python.exe`).
   - **Run `bootstrap.py` in VS Code** (if not run earlier):
     - Open `bootstrap.py` in VS Code.
     - Right-click the file and select `Run Python File in Terminal`, or use the integrated terminal:
       ```powershell
       python bootstrap.py
       ```
   - **Edit Configuration Files**:
     - Update `docs/source/conf.py` for additional Sphinx settings (e.g., add custom modules for `autodoc`).
     - Modify `README.md` or `setup.py` to add project-specific details.
     - Use VS Code’s built-in Git integration (Source Control tab) to stage, commit, and push changes:
       - Click the Source Control icon in the sidebar.
       - Stage changes by clicking the `+` next to modified files.
       - Enter a commit message and click the checkmark to commit.
       - Click the `...` menu and select `Push` to push to the remote repository.
   - **Generate Sphinx Documentation**:
     - Open the integrated terminal in VS Code (`Ctrl+``).
     - Run:
       ```powershell
       cd docs
       .\make.bat html
       ```
     - Open `docs/build/html/index.html` in a browser to verify the documentation.

### Troubleshooting

- **Pre-Commit Hook Failures**:

  - If `scripts/commit-push.ps1` fails due to pre-commit hooks (e.g., `black`, `flake8`, `sphinx-build`), check the error output in the terminal.
  - Ensure all dependencies are installed:
    ```powershell
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```
  - Verify Sphinx files (`docs/Makefile`, `docs/make.bat`, `docs/source/conf.py`, `docs/source/index.rst`) exist.
  - If issues persist, open `.pre-commit-config.yaml` in VS Code and check the `sphinx-build` hook configuration:
    ```yaml
    - repo: local
      hooks:
        - id: sphinx-build
          name: Build Sphinx documentation
          entry: make html
          language: system
          files: ^docs/
    ```

- **Git Push Errors**:

  - If `git push` fails, verify the GitHub URL and ensure you have push access.
  - Use a personal access token if authentication fails:
    ```powershell
    git remote set-url origin https://<username>:<token>@github.com/<username>/<repo>.git
    ```
    Generate a token in GitHub: `Settings > Developer settings > Personal access tokens > Tokens (classic)`.

- **Dependency Issues**:

  - If `pip install -r requirements.txt` fails, check for conflicting versions in `requirements.txt`.
  - Run in the VS Code terminal:
    ```powershell
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

- **Virtual Environment Issues**:

  - Ensure `.venv` is not ignored in `.gitignore`.
  - If the virtual environment fails to activate, recreate it:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

- **.env File Issues**:
  - The `bootstrap.py` script creates a `.env` file with the project name and example variables.
  - Edit `.env` in VS Code to add project-specific environment variables (e.g., API keys, database URLs).
  - Do not commit sensitive data to `.env`. For production use, add `.env` to `.gitignore` after setup and use a `.env.example` file for templates.

**GUI Launch Issues**:

**Scraping Notes**:

- Scraping utilities live under `scraping/` (high-level: `scrape_club`).
- Provide a full club overview URL like:
  `https://leipzig.tischtennislive.de/?L1=Public&L2=Verein&L2P=2294&Page=Spielbetrieb&Sportart=96&Saison=2025`.
- Workflow:
  1. Parse club teams + associated division links.
  2. For each division, fetch both halves of the match plan (L3P=1,2).
  3. Parse match results into structured scores when available.
  4. Collect division team roster table (if present).
  5. Optionally fetch each team detail page to extract player stats (LivePZ, balance).
- Caching: `CachedFetcher` stores HTML (memory + disk) to minimize repeated hits.
- Conversion: Use `scheduled_to_matches` to obtain `data.match.Match` instances.
- Manual run:
  ```powershell
  python -m scripts.scrape_club "<club_overview_url>"
  ```
- Tests rely on minimal synthetic fixtures; they don't perform live network I/O.
- Respect robots/traffic: default throttle 0.5s; avoid parallel flooding.

- Missing PyQt6: Ensure you are in the virtual environment and run `pip install -r requirements.txt`.
- Qt platform plugin error (e.g. `Could not load the Qt platform plugin "windows"`): This is often caused by mixing system and venv interpreters. Re-activate `.venv` and retry. On CI/headless, export `QT_QPA_PLATFORM=offscreen`.
- Immediate exit: Confirm `run_gui.py` returns a non-zero exit only if there is an error; otherwise the window should appear. If running in a remote/headless environment without display, set `QT_QPA_PLATFORM=offscreen`.
- Future regressions: A smoke test (`tests/test_gui_imports.py`) ensures GUI modules import cleanly—run `pytest -k gui_imports` to verify after changes.

### Documentation

- Documentation is built with Sphinx. To generate HTML documentation:
  ```powershell
  cd docs
  .\make.bat html
  ```

## Repository Structure

- `bootstrap.py`: Automates project setup.
- `requirements.txt`: Lists dependencies (e.g., `numpy`, `pandas`, `sphinx`, `pre-commit`).
- `scripts/commit-push.ps1`: PowerShell script for staging, committing, and pushing changes.
- `docs/`: Contains Sphinx files (`Makefile`, `make.bat`, `source/conf.py`, `source/index.rst`).
- `.pre-commit-config.yaml`: Configures pre-commit hooks.
- `setup.py`: Python package configuration.
- `.env`: Template file for environment variables.
- `README.md`: This file.

For further customization, edit `setup.py`, `docs/source/conf.py`, `.env`, or add Python modules to the repository.
