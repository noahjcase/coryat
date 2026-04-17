# coryat

A terminal tool for tracking your [Coryat score](https://j-archive.com/help.php#coryatscore) while playing along live with *Jeopardy!*

After each episode, the session is saved as a CSV to a data repository, which triggers a GitHub Action that rebuilds a stats dashboard on GitHub Pages.

---

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (for installation)
- A separate `coryat-data` git repository (see below)

---

## Installation

```bash
git clone https://github.com/noahjcase/coryat.git
cd coryat
uv tool install --editable .
```

This installs the `playj` command globally.

---

## Setup

### 1. Create the data repository

Create a new git repository called `coryat-data` (public or private). This is where your game CSVs and the generated stats dashboard will live.

```bash
mkdir ~/projects/coryat-data
cd ~/projects/coryat-data
mkdir games
git init
git remote add origin git@github.com:<your-username>/coryat-data.git
git push -u origin main
```

### 2. Create the config file

```bash
mkdir -p ~/.config/playj
echo 'data_repo_path = "/path/to/coryat-data"' > ~/.config/playj/config.toml
```

Replace `/path/to/coryat-data` with the absolute path to your local `coryat-data` repo clone.

---

## Usage

```
playj [<YYYYMMDD> | --season S --episode E] [--force] [--no-scrape] [--offline]
```

Run `playj` with the air date of the episode you're tracking:

```bash
playj 20230105
```

Or use season and episode number (useful for streaming services):

```bash
playj --season 41 --episode 12
```

### Flags

| Flag | Description |
|---|---|
| `--force` | Overwrite an existing game entry for this date/episode |
| `--season` | Season number (use with `--episode`) |
| `--episode` | Episode number within season (use with `--season`) |
| `--no-scrape` | Skip J! Archive category fetch; enter categories manually |
| `--offline` | Skip J! Archive fetch and skip git push; save CSV locally only |

### Startup sequence

1. `playj` validates the date or season/episode, loads your config, and checks if the game already exists in your data repo.
2. If a game exists, it exits with a message — pass `--force` to overwrite.
3. Unless `--no-scrape` or `--offline` is set, `playj` fetches category names for that episode from J! Archive and pre-populates the board. If this fails for any reason, it falls back to manual category entry without crashing.
4. The TUI opens.

---

## The TUI

The board is rendered in your terminal and is entirely keyboard-driven.

### Board

Six categories across, five clue values down (200–1000 for Single J!, 400–2000 for Double J!). The cursor cell is highlighted.

```
  CATEGORY 1     CATEGORY 2     CATEGORY 3     CATEGORY 4     CATEGORY 5     CATEGORY 6
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│     200     │     200     │     200     │     200     │     200     │     200     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│     400     │     400     │     400     │     400     │     400     │     400     │
...
```

### Keybindings

| Key        | Action                                                      |
|------------|-------------------------------------------------------------|
| Arrow keys | Move cursor                                                 |
| `c`        | Mark correct                                                |
| `x`        | Mark wrong                                                  |
| `.`        | Mark skipped (clue revealed, no answer attempted)           |
| `u`        | Mark unrevealed (show never got to this clue)               |
| `d`        | Mark as Daily Double (opens overlay for correct/wrong/skip) |
| `Tab`      | Advance to Double J! (all Single J! cells must be filled)   |
| `s`        | Save and quit                                               |
| `q`        | Quit without saving (prompts for confirmation)              |

**Note:** After marking any cell, the cursor automatically advances to the next empty cell in reading order.

### Cell states

| State | Symbol | Color |
|---|---|---|
| Empty | `(value)` | Dim |
| Correct | `✓` | Green |
| Wrong | `✗` | Red |
| Skipped | `·` | Yellow |
| Unrevealed | `–` | Dark gray |
| DD correct | `DD✓` | Green + bold |
| DD wrong | `DD✗` | Red + bold |
| DD skipped | `DD·` | Yellow + bold |

### Daily Double

Press `d` on a cell. An overlay appears:

```
┌──────────────────────────────────┐
│           DAILY DOUBLE           │
│  [c] correct [x] wrong [.] skip  │
└──────────────────────────────────┘
```

Press `c`, `x`, or `.` to confirm, or `Escape` to cancel.

**Daily Double constraints:**
- No DD allowed in the first row (lowest value)
- Single Jeopardy: exactly 1 DD
- Double Jeopardy: at most 2 DDs
- If the Double Jeopardy board is complete, there must be exactly 2 DDs
- The 2 DDs in Double Jeopardy must be in different columns

### Saving

Press `s` to save. Every cell in both rounds must be marked — use `u` for clues the show never reached. If any cell is unmarked, save is rejected with a count of remaining cells.

On a successful save, `playj` writes a CSV to your data repo and runs `git commit` + `git push`. The commit message includes your Coryat score:

```
game: 20230105 (coryat: 1400)
```

If the push fails (or you passed `--offline`), the CSV is saved locally and you are shown the command to push manually.

---

## Coryat Score

The Coryat score measures your knowledge independent of wagering. For each clue:

- **Correct** (`c`, `dc`): add the face value
- **Wrong** (`x`, `dx`): subtract the face value
- **Skipped / Unrevealed / DD Skipped** (`.`, `u`, `d.`): no change
- **Final Jeopardy**: excluded entirely

---

## Data Format

Games are stored in `coryat-data/games/YYYYMMDD.csv`, one row per clue:

```
date,round,category,value,result,is_daily_double
20230105,single,AMERICAN HISTORY,200,c,false
20230105,single,AMERICAN HISTORY,400,x,false
20230105,single,SCIENCE,600,dc,true
20230105,double,POTPOURRI,1200,u,false
20230105,double,WORLD CAPITALS,1600,d.,true
```

Result codes: `c` (correct), `x` (wrong), `.` (skipped), `u` (unrevealed), `dc` (DD correct), `dx` (DD wrong), `d.` (DD skipped).

---

## Stats Dashboard

Once you have game data in `coryat-data`, a GitHub Action rebuilds a stats dashboard at `https://<your-username>.github.io/coryat-data` on every push. The dashboard includes:

- Coryat over time (line chart with rolling average)
- Number correct over time
- Correct percentage over time
- Accuracy by dollar value
- Accuracy by round (Single vs. Double)
- Daily Double record
- Category breakdown
- Summary stats: games played, average Coryat, best Coryat, all-time correct %, DD correct %

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check
```
