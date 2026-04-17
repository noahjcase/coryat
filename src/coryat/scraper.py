import re

import requests
from bs4 import BeautifulSoup

_SEARCH_URL = "https://j-archive.com/search.php"
_GAME_URL = "https://j-archive.com/showgame.php"
_SEASON_URL = "https://j-archive.com/showseason.php"


def _find_game_id(date: str) -> int | None:
    """Resolve YYYYMMDD to a J! Archive game_id via search."""
    # J! Archive search accepts date in YYYY-MM-DD or season search;
    # the simplest approach is to search by exact date string.
    formatted = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    try:
        resp = requests.get(
            _SEARCH_URL,
            params={"search": formatted},
            timeout=8,
        )
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # Links like showgame.php?game_id=1234
    for a in soup.find_all("a", href=True):
        m = re.search(r"showgame\.php\?game_id=(\d+)", a["href"])
        if m:
            return int(m.group(1))
    return None


def _scrape_categories(game_id: int) -> tuple[list[str], list[str]] | None:
    """Return (single_cats, double_cats) or None on failure."""
    try:
        resp = requests.get(_GAME_URL, params={"game_id": game_id}, timeout=8)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    def extract(round_id: str) -> list[str]:
        table = soup.find("div", id=round_id)
        if not table:
            return []
        cats = [td.get_text(" ", strip=True) for td in table.find_all("td", class_="category_name")]
        return cats[:6]

    single = extract("jeopardy_round")
    double = extract("double_jeopardy_round")
    if len(single) == 6 and len(double) == 6:
        return single, double
    return None


def find_game_by_season_episode(season: int, episode: int) -> tuple[str, int] | None:
    """
    Resolve a season + episode number to (date_YYYYMMDD, game_id).
    Episodes are numbered from 1 in air-date order.
    Returns None on network failure or if the episode index is out of range.
    """
    try:
        resp = requests.get(_SEASON_URL, params={"season": season}, timeout=8)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []
    for a in soup.find_all("a", href=True):
        m_id = re.search(r"showgame\.php\?game_id=(\d+)", a["href"])
        if not m_id:
            continue
        m_date = re.search(r"aired\s+(\d{4}-\d{2}-\d{2})", a.get_text())
        if not m_date:
            continue
        game_id = int(m_id.group(1))
        date_str = m_date.group(1).replace("-", "")
        entries.append((date_str, game_id))

    # J! Archive lists newest episodes first; reverse to get chronological order.
    entries.reverse()

    if episode < 1 or episode > len(entries):
        return None
    return entries[episode - 1]


def fetch_categories(date: str, game_id: int | None = None) -> tuple[list[str] | None, list[str] | None, str]:
    """
    Returns (single_cats, double_cats, status_message).
    On any failure, returns (None, None, error_message).
    Accepts an optional game_id to skip the date-based search.
    """
    if game_id is None:
        game_id = _find_game_id(date)
    if game_id is None:
        return None, None, "J! Archive: unavailable, enter categories manually"

    result = _scrape_categories(game_id)
    if result is None:
        return None, None, "J! Archive: unavailable, enter categories manually"

    single, double = result
    return single, double, "J! Archive: categories loaded \u2713"
