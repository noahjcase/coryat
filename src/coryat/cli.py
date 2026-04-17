import argparse
import sys
from datetime import datetime


def _parse_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date '{value}': expected YYYYMMDD")
    return value


def main():
    parser = argparse.ArgumentParser(prog="playj", description="Track your Jeopardy! Coryat score.")
    parser.add_argument("date", nargs="?", type=_parse_date, help="air date in YYYYMMDD format")
    parser.add_argument("--season", type=int, metavar="S", help="season number (use with --episode)")
    parser.add_argument("--episode", type=int, metavar="E", help="episode number within season (use with --season)")
    parser.add_argument("--force", action="store_true", help="overwrite existing game for this date")
    parser.add_argument("--no-scrape", action="store_true", help="skip J! Archive fetch")
    parser.add_argument("--offline", action="store_true", help="skip git push; save CSV locally only")
    args = parser.parse_args()

    has_date = args.date is not None
    has_se = args.season is not None or args.episode is not None

    if has_date and has_se:
        parser.error("provide either a date or --season/--episode, not both")
    if not has_date and not has_se:
        parser.error("provide a date (YYYYMMDD) or both --season and --episode")
    if has_se and (args.season is None or args.episode is None):
        parser.error("--season and --episode must be used together")

    from . import config, data, scraper, tui, git

    cfg = config.load()
    data_repo = cfg["data_repo_path"]

    # Resolve season/episode to date + game_id if needed
    prefetched_game_id = None
    if has_se:
        resolved = scraper.find_game_by_season_episode(args.season, args.episode)
        if resolved is None:
            print(f"S{args.season}E{args.episode} not found on J! Archive.")
            sys.exit(1)
        date, prefetched_game_id = resolved
        print(f"resolved S{args.season}E{args.episode} to {date}")
    else:
        date = args.date

    # Duplicate check
    existing = data.game_exists(data_repo, date)
    if existing is not None and not args.force:
        print(f"already played {date} (coryat: {existing}). use --force to overwrite.")
        sys.exit(0)

    # Scrape categories
    single_cats = None
    double_cats = None
    scrape_status = ""
    if not args.no_scrape and not args.offline:
        single_cats, double_cats, scrape_status = scraper.fetch_categories(date, game_id=prefetched_game_id)
    else:
        scrape_status = "J! Archive: skipped, enter categories manually"

    # Run TUI
    result = tui.run_tui(date, single_cats, double_cats, scrape_status)
    if result is None:
        print("quit without saving.")
        sys.exit(0)

    clues, score = result

    # Write CSV
    path = data.write_game(data_repo, date, clues)
    print(f"saved: {path}  (coryat: {score})")

    # Git push
    if args.offline:
        print("saved locally. push manually when online:")
        print(f"  cd {data_repo} && git push")
        return

    success = git.push_game(data_repo, date, score)
    if not success:
        print("saved locally. push manually when online:")
        print(f"  cd {data_repo} && git push")
