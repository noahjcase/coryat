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
    parser.add_argument("date", type=_parse_date, help="air date in YYYYMMDD format")
    parser.add_argument("--force", action="store_true", help="overwrite existing game for this date")
    parser.add_argument("--no-scrape", action="store_true", help="skip J! Archive fetch")
    parser.add_argument("--offline", action="store_true", help="skip git push; save CSV locally only")
    args = parser.parse_args()

    from . import config, data, scraper, tui, git

    cfg = config.load()
    data_repo = cfg["data_repo_path"]

    # Duplicate check
    existing = data.game_exists(data_repo, args.date)
    if existing is not None and not args.force:
        print(f"already played {args.date} (coryat: {existing}). use --force to overwrite.")
        sys.exit(0)

    # Scrape categories
    single_cats = None
    double_cats = None
    scrape_status = ""
    if not args.no_scrape and not args.offline:
        single_cats, double_cats, scrape_status = scraper.fetch_categories(args.date)
    else:
        scrape_status = "J! Archive: skipped, enter categories manually"

    # Run TUI
    result = tui.run_tui(args.date, single_cats, double_cats, scrape_status)
    if result is None:
        print("quit without saving.")
        sys.exit(0)

    clues, score = result

    # Write CSV
    path = data.write_game(data_repo, args.date, clues)
    print(f"saved: {path}  (coryat: {score})")

    # Git push
    if args.offline:
        print("saved locally. push manually when online:")
        print(f"  cd {data_repo} && git push")
        return

    success = git.push_game(data_repo, args.date, score)
    if not success:
        print("saved locally. push manually when online:")
        print(f"  cd {data_repo} && git push")
