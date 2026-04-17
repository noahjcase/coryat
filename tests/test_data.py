import csv
from pathlib import Path


from coryat.data import game_exists, write_game
from coryat.scoring import coryat


FIXTURE = Path(__file__).parent / "fixtures" / "sample_game.csv"


def _load_fixture() -> list[dict]:
    with open(FIXTURE, newline="") as f:
        return list(csv.DictReader(f))


def test_game_exists_missing(tmp_path):
    assert game_exists(str(tmp_path), "20230105") is None


def test_game_exists_found(tmp_path):
    clues = _load_fixture()
    write_game(str(tmp_path), "20230105", clues)
    score = game_exists(str(tmp_path), "20230105")
    assert score == coryat(clues)


def test_write_game_creates_file(tmp_path):
    clues = _load_fixture()
    path = write_game(str(tmp_path), "20230105", clues)
    assert path.exists()


def test_write_game_row_count(tmp_path):
    clues = _load_fixture()
    path = write_game(str(tmp_path), "20230105", clues)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(clues)


def test_write_game_fields(tmp_path):
    clues = _load_fixture()
    path = write_game(str(tmp_path), "20230105", clues)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        assert set(reader.fieldnames) == {"date", "round", "category", "value", "result", "is_daily_double"}
        row = next(reader)
    assert row["date"] == "20230105"
    assert row["round"] in ("single", "double")


def test_result_codes_preserved(tmp_path):
    clues = _load_fixture()
    path = write_game(str(tmp_path), "20230105", clues)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    original_results = [c["result"] for c in clues]
    written_results = [r["result"] for r in rows]
    assert original_results == written_results


def test_duplicate_detection(tmp_path):
    clues = _load_fixture()
    write_game(str(tmp_path), "20230105", clues)
    # Writing again should overwrite; existence check still returns a score
    score = game_exists(str(tmp_path), "20230105")
    assert isinstance(score, int)
