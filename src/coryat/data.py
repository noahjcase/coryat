import csv
from pathlib import Path

from .scoring import coryat

FIELDNAMES = ["date", "round", "category", "value", "result", "is_daily_double"]


def game_path(data_repo_path: str, date: str) -> Path:
    return Path(data_repo_path) / "games" / f"{date}.csv"


def game_exists(data_repo_path: str, date: str) -> int | None:
    """Return the Coryat score if a game CSV exists for this date, else None."""
    path = game_path(data_repo_path, date)
    if not path.exists():
        return None
    with open(path, newline="") as f:
        clues = list(csv.DictReader(f))
    return coryat(clues)


def write_game(data_repo_path: str, date: str, clues: list[dict]):
    path = game_path(data_repo_path, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(clues)
    return path
