
import pytest

from coryat.board import Board, CellState, NUM_CATEGORIES, NUM_ROWS, SINGLE_VALUES, DOUBLE_VALUES


def _fully_marked_board(round_name: str, categories: list[str]) -> Board:
    board = Board(round_name=round_name, categories=categories)
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)
    return board


def test_board_completeness_empty():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)
    assert not board.all_marked
    assert board.unmarked_count() == NUM_ROWS * NUM_CATEGORIES


def test_board_completeness_full():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = _fully_marked_board("single", cats)
    assert board.all_marked
    assert board.unmarked_count() == 0


def test_board_single_values():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)
    for row_idx, val in enumerate(SINGLE_VALUES):
        for col in range(NUM_CATEGORIES):
            assert board.get(row_idx, col).value == val


def test_board_double_values():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)
    for row_idx, val in enumerate(DOUBLE_VALUES):
        for col in range(NUM_CATEGORIES):
            assert board.get(row_idx, col).value == val


def test_to_clue_dicts():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = _fully_marked_board("single", cats)
    clues = board.to_clue_dicts("20230105")
    assert len(clues) == NUM_ROWS * NUM_CATEGORIES
    assert all(c["date"] == "20230105" for c in clues)
    assert all(c["round"] == "single" for c in clues)
    assert all(c["result"] == "c" for c in clues)


def test_dd_cell_is_daily_double():
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)
    board.set_state(0, 0, CellState.DD_CORRECT)
    assert board.get(0, 0).is_daily_double


def test_date_validation_valid(tmp_path):
    """_parse_date accepts valid YYYYMMDD strings."""
    from coryat.cli import _parse_date
    assert _parse_date("20230105") == "20230105"


def test_date_validation_invalid():
    import argparse
    from coryat.cli import _parse_date
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_date("not-a-date")


def test_date_validation_wrong_format():
    import argparse
    from coryat.cli import _parse_date
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_date("2023-01-05")
