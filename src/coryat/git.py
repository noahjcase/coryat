import subprocess
from pathlib import Path


def push_game(data_repo_path: str, date: str, score: int) -> bool:
    """Stage, commit, and push the game CSV. Returns True on success."""
    repo = Path(data_repo_path)
    csv_rel = f"games/{date}.csv"
    commit_msg = f"game: {date} (coryat: {score})"

    try:
        subprocess.run(["git", "add", csv_rel], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else ""
        print(f"git error: {stderr or e}")
        return False
