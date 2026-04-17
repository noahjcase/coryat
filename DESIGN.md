# `playj` — Design Document

## Overview

A terminal-based tool for tracking performance playing along live with *Jeopardy!* ("J!"). After each episode, the session is saved as a CSV row-per-clue to a data repo, which triggers a GitHub Action that rebuilds a stats dashboard on GitHub Pages.

---

## Repositories

### `coryat` (public)
The tool itself: CLI, TUI, data-writing logic, tests, and documentation.

**Owner:** noahjcase

### `coryat-data` (public or private, your choice)
Game data CSVs and the generated GitHub Pages dashboard. No application code lives here.

**Owner:** noahjcase  
**GitHub Pages URL:** `https://noahjcase.github.io/coryat-data`

---

## Tech Stack

- **Python 3.14**, managed with `uv`
- **`blessed`** for the TUI
- **`requests` + `beautifulsoup4`** for J! Archive scraping (v1 feature)
- **`subprocess`** for git operations (not `gitpython` — keep dependencies minimal)
- **`tomllib`** (stdlib in 3.11+) for config parsing
- **`pytest`** for tests
- **`ruff`** for linting

### Project setup

```
uv init coryat
uv add blessed requests beautifulsoup4
uv add --dev pytest ruff
```

The CLI entry point is registered as a `uv tool` / `pipx`-style script:

```toml
# pyproject.toml
[project.scripts]
playj = "coryat.cli:main"
```

Install globally with:
```
uv tool install --editable .
```

---

## Configuration

Config file lives at `~/.config/playj/config.toml`:

```toml
data_repo_path = "/Users/noahjcase/projects/coryat-data"
```

`playj` reads this on startup and fails with a clear error if it doesn't exist, prompting the user to create it.

---

## CLI Interface

```
playj <YYYYMMDD>
```

### Startup sequence

1. Parse and validate the date argument. Reject non-dates with a clear error.
2. Load config from `~/.config/playj/config.toml`.
3. Check the data repo for a game already logged with that date. If found, print:
   ```
   already played 20230105 (coryat: 1400). use --force to overwrite.
   ```
   Exit unless `--force` is passed.
4. **(v1 feature)** Attempt to scrape categories for that date from J! Archive. If scraping fails or is unavailable, fall back to manual category entry.
5. Open the TUI.

### Flags

| Flag | Behavior |
|---|---|
| `--force` | Overwrite an existing game entry for this date |
| `--no-scrape` | Skip J! Archive fetch, go straight to manual category entry |
| `--offline` | Skip J! Archive fetch and skip git push at the end; save CSV locally only |

---

## TUI Design

Built with `blessed`. The board renders in the terminal and is entirely keyboard-driven. No mouse required.

### Board layout

```
  CATEGORY 1     CATEGORY 2     CATEGORY 3     CATEGORY 4     CATEGORY 5     CATEGORY 6
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│     200     │     200     │     200     │     200     │     200     │     200     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│     400     │     400     │     400     │     400     │     400     │     400     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│     600     │     600     │     600     │     600     │     600     │     600     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│     800     │     800     │     800     │     800     │     800     │     800     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│    1000     │    1000     │    1000     │    1000     │    1000     │    1000     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

- Single J! rows: 200 / 400 / 600 / 800 / 1000
- Double J! rows: 400 / 800 / 1200 / 1600 / 2000
- The active cell is highlighted (reverse video or bold border)
- Marked cells show their state symbol centered in the cell (see Cell States below)
- The current round (Single / Double) is shown in a header line

### Category entry (if manual)

Before the board is interactive, the user is prompted to enter category names. A simple sequential prompt at the top of the screen:

```
Enter categories for Single Jeopardy (press Enter after each):
Category 1: _
```

Category names are displayed truncated to fit the column width (13 chars). Full names are stored in the CSV.

### Navigation

| Key | Action |
|---|---|
| Arrow keys | Move cursor around the board |
| `c` | Mark cell: correct |
| `w` | Mark cell: wrong |
| `.` | Mark cell: skipped (clue revealed, no answer attempted) |
| `u` | Mark cell: unrevealed (show never got to it) |
| `d` | Mark cell: Daily Double — opens subprompt |
| `Tab` | Advance to Double Jeopardy (prompts for confirmation + new categories) |
| `s` | Save and quit (triggers validation, then CSV write + git push) |
| `q` | Quit without saving (prompts for confirmation) |

### Daily Double subprompt

When `d` is pressed on a cell, the board dims and a small centered overlay appears:

```
┌─────────────────────────┐
│      DAILY DOUBLE       │
│   correct or wrong?     │
│       [c]   [w]         │
└─────────────────────────┘
```

Press `c` or `w` to confirm. Press `Escape` to cancel (cell stays unmarked). The cell then displays `DD✓` or `DD✗` as appropriate.

### Round transition

When `Tab` is pressed, a confirmation prompt asks:
```
Switch to Double Jeopardy? All Single J! cells must be filled. [y/n]
```
If confirmed, the board resets to Double J! values (400–2000) and prompts for 6 new category names. Single J! data is preserved internally.

### Save and validation

When `s` is pressed, `playj` checks that every cell in both rounds has a non-empty state. If any cell is untouched, save is rejected:

```
cannot save: 3 cells unmarked. use [u] for unrevealed clues.
```

If validation passes, the game is written to CSV and pushed.

### Visual language

| State | Display | Color |
|---|---|---|
| Empty | `(value)` | Dim |
| Correct | `✓` | Green |
| Wrong | `✗` | Red |
| Skipped | `·` | Yellow |
| Unrevealed | `–` | Dark gray |
| DD correct | `DD✓` | Green + bold |
| DD wrong | `DD✗` | Red + bold |

---

## Data Schema

### File structure in `coryat-data`

```
coryat-data/
  games/
    20230105.csv
    20230106.csv
    ...
  dashboard/         ← generated by GH Action, do not edit manually
    index.html
    ...
```

### Per-game CSV format

One file per game, named `YYYYMMDD.csv`. One row per clue.

```
date,round,category,value,result,is_daily_double
20230105,single,AMERICAN HISTORY,200,c,false
20230105,single,AMERICAN HISTORY,400,w,false
20230105,single,SCIENCE,600,dc,true
20230105,double,POTPOURRI,1200,u,false
...
```

#### Field definitions

| Field | Type | Values |
|---|---|---|
| `date` | string | `YYYYMMDD` |
| `round` | string | `single`, `double` |
| `category` | string | Full category name |
| `value` | integer | Face value of the clue (200–2000) |
| `result` | string | `c`, `w`, `.`, `u`, `dc`, `dw` |
| `is_daily_double` | boolean | `true` / `false` |

#### Result codes

| Code | Meaning |
|---|---|
| `c` | Correct |
| `w` | Wrong |
| `.` | Skipped |
| `u` | Unrevealed |
| `dc` | Daily Double, correct |
| `dw` | Daily Double, wrong |

---

## Coryat Score Calculation

**Definition:** For each clue with result `c` or `dc`, add face value. For each clue with result `w` or `dw`, subtract face value. Skipped (`.`) and unrevealed (`u`) clues contribute 0. Final Jeopardy is excluded entirely.

```python
def coryat(clues: list[dict]) -> int:
    score = 0
    for clue in clues:
        if clue["result"] in ("c", "dc"):
            score += clue["value"]
        elif clue["result"] in ("w", "dw"):
            score -= clue["value"]
    return score
```

---

## J! Archive Scraping (v1 Feature)

On startup, `playj` attempts to:

1. Resolve the air date to a J! Archive game ID (via a search request to `j-archive.com`)
2. Scrape categories for Single and Double J! from `j-archive.com/showgame.php?game_id=<id>`
3. Pre-populate the TUI board with those category names

If scraping fails for any reason (network down, date not found, parse error), `playj` silently falls back to manual category entry — never crashes. A small status line informs the user:

```
J! Archive: categories loaded ✓
```
or
```
J! Archive: unavailable, enter categories manually
```

---

## Git Workflow

After a successful save, `playj` runs the following in the `data_repo_path`:

```bash
git add games/YYYYMMDD.csv
git commit -m "game: 20230105 (coryat: 1400)"
git push
```

All via `subprocess.run()`. Errors are caught and reported clearly. If offline (`--offline` flag or push fails), the CSV is saved locally with a message:

```
saved locally. push manually when online:
  cd ~/projects/coryat-data && git push
```

---

## GitHub Actions

### `coryat` repo — CI

**Trigger:** push to `main`

**Steps:**
1. Set up Python 3.14 with `uv`
2. Install dependencies
3. Run `ruff check`
4. Run `pytest`

### `coryat-data` repo — Dashboard build

**Trigger:** push to `main` (i.e., any new game CSV commit)

**Steps:**
1. Set up Python 3.14 with `uv`
2. Install dashboard build dependencies (pandas, jinja2, matplotlib or similar)
3. Run build script: reads all CSVs in `games/`, generates `dashboard/index.html`
4. Commit and push `dashboard/` back to repo (or use GH Pages deploy action)

---

## Dashboard

Static HTML page deployed to GitHub Pages at `https://noahjcase.github.io/coryat-data`.

### Visualizations

| Chart | Description |
|---|---|
| **Coryat over time** | Line chart, one point per game, with a rolling average |
| **Number correct over time** | Line chart, raw count per game |
| **Correct percentage over time** | Line chart, `(c + dc) / (c + w + dc + dw)` per game — excludes skips and unrevealed |
| **Accuracy by dollar value** | Bar chart: for each face value (200–2000), correct % |
| **Accuracy by round** | Grouped bar: Single vs Double J! correct % |
| **Daily Double record** | Single stat: `dc / (dc + dw)` across all games, with count |
| **Category breakdown** | Table or heatmap: most and least accurate categories over time |

### Summary stats (top of page)

- Games played
- Average Coryat
- Best Coryat (with date)
- All-time correct %
- DD correct %

---

## Tests

All in `coryat` repo, run via `pytest`.

### Unit tests

- **Coryat calculation:** known clue sets → expected scores, including DD edge cases
- **Completeness validation:** boards with missing cells rejected, fully marked boards accepted
- **Duplicate detection:** CSV with existing date triggers duplicate error
- **Result code parsing:** all six result codes parsed correctly
- **CSV write:** a simulated game writes the expected rows in the expected format

### Integration tests

- Full CLI invocation with a mock game (no real terminal, no real git push)
- Dashboard build script: given fixture CSVs, output HTML contains expected stat values

---

## Project Structure (`coryat` repo)

```
coryat/
  pyproject.toml
  README.md
  DESIGN.md
  src/
    coryat/
      __init__.py
      cli.py           ← entry point, arg parsing, startup sequence
      tui.py           ← blessed-based board rendering and input loop
      board.py         ← board state model, cell states, round logic
      data.py          ← CSV read/write, duplicate detection, validation
      scoring.py       ← Coryat and other stat calculations
      scraper.py       ← J! Archive fetch (v1)
      git.py           ← subprocess git operations
      config.py        ← config file loading
  tests/
    test_scoring.py
    test_data.py
    test_cli.py
    fixtures/
      sample_game.csv
```

---

## Out of Scope (for now)

- Final Jeopardy tracking (Coryat excludes it; can be added later as a separate optional prompt)
- Any kind of GUI or web interface for input
- Multiplayer / tracking other contestants
- Importing historical data retroactively (the CSV format is simple enough to do manually if desired)
