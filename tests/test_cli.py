
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


# Daily Double constraint tests
def test_dd_cannot_be_in_first_row():
    """DDs cannot be placed in the first row (lowest value)."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)
    # Row 0 is the lowest value row
    assert not board.can_place_dd(0, 0)
    assert not board.can_place_dd(0, 5)
    # Row 1 and above should allow DD
    assert board.can_place_dd(1, 0)
    assert board.can_place_dd(4, 5)


def test_single_jeopardy_exactly_one_dd():
    """Single Jeopardy must have exactly 1 DD when board is complete."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # No DDs - should fail
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)
    assert board.validate_dd_constraints() == "Single Jeopardy must have exactly 1 daily double (found 0)"

    # Add 1 DD - should pass
    board.set_state(1, 0, CellState.DD_CORRECT)
    assert board.validate_dd_constraints() is None

    # Add 2nd DD - should fail
    board.set_state(2, 1, CellState.DD_WRONG)
    assert board.validate_dd_constraints() == "Single Jeopardy must have exactly 1 daily double (found 2)"


def test_double_jeopardy_at_most_two_dds():
    """Double Jeopardy can have 0, 1, or 2 DDs, but not more."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)

    # Mark all as correct first
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)

    # Add 3 DDs - should fail
    board.set_state(1, 0, CellState.DD_CORRECT)
    board.set_state(1, 1, CellState.DD_WRONG)
    board.set_state(1, 2, CellState.DD_SKIPPED)
    assert "at most 2" in board.validate_dd_constraints()


def test_double_jeopardy_two_dds_requires_different_columns():
    """If Double Jeopardy has 2 DDs, they must be in different columns."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)

    # Mark all as correct
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)

    # Put 2 DDs in same column - should fail
    board.set_state(1, 0, CellState.DD_CORRECT)
    board.set_state(2, 0, CellState.DD_WRONG)
    assert "different columns" in board.validate_dd_constraints()

    # Put 2 DDs in different columns - should pass
    board.set_state(2, 0, CellState.CORRECT)
    board.set_state(2, 1, CellState.DD_WRONG)
    assert board.validate_dd_constraints() is None


def test_double_jeopardy_complete_board_requires_exactly_two_dds():
    """If every Double Jeopardy cell is marked, there must be exactly 2 DDs."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)

    # Mark all as correct (no DDs yet) - should fail
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)
    assert "exactly 2" in board.validate_dd_constraints()

    # Add 1 DD - still should fail
    board.set_state(1, 0, CellState.DD_CORRECT)
    assert "exactly 2" in board.validate_dd_constraints()

    # Add 2nd DD in different column - should pass
    board.set_state(2, 1, CellState.DD_WRONG)
    assert board.validate_dd_constraints() is None


def test_double_jeopardy_incomplete_board_allows_fewer_dds():
    """Incomplete Double Jeopardy board can have 0 or 1 DD."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)

    # Mark all but one cell
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            if not (row == 0 and col == 0):
                board.set_state(row, col, CellState.CORRECT)

    # 0 DDs on incomplete board - no validation error (only checked on complete board)
    assert board.validate_dd_constraints() is None

    # 1 DD on incomplete board - no validation error
    board.set_state(1, 0, CellState.DD_CORRECT)
    assert board.validate_dd_constraints() is None


def test_get_dds_returns_all_dd_positions():
    """get_dds() returns list of all DD positions."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # No DDs
    assert board.get_dds() == []

    # Add DDs with different states
    board.set_state(1, 0, CellState.DD_CORRECT)
    board.set_state(2, 1, CellState.DD_WRONG)
    board.set_state(2, 2, CellState.DD_SKIPPED)

    dds = board.get_dds()
    assert len(dds) == 3
    assert (1, 0) in dds
    assert (2, 1) in dds
    assert (2, 2) in dds


def test_dd_skipped_is_recognized_as_daily_double():
    """DD_SKIPPED state should be recognized as a daily double."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    board.set_state(1, 0, CellState.DD_SKIPPED)
    assert board.get(1, 0).is_daily_double
    assert len(board.get_dds()) == 1


# Cell advancement tests
def test_next_empty_cell_advances_right():
    """next_empty_cell should advance right within the same row."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # Mark first cell, find next empty
    board.set_state(0, 0, CellState.CORRECT)
    next_cell = board.next_empty_cell(0, 0)
    assert next_cell == (0, 1)


def test_next_empty_cell_wraps_to_next_row():
    """next_empty_cell should wrap to next row when current row is full."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # Mark all cells in row 0
    for col in range(NUM_CATEGORIES):
        board.set_state(0, col, CellState.CORRECT)

    # From last cell in row 0, next empty should be first cell in row 1
    next_cell = board.next_empty_cell(0, NUM_CATEGORIES - 1)
    assert next_cell == (1, 0)


def test_next_empty_cell_skips_marked_cells():
    """next_empty_cell should skip over already-marked cells."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # Mark cells 1, 2, 3 in row 0
    board.set_state(0, 1, CellState.CORRECT)
    board.set_state(0, 2, CellState.WRONG)
    board.set_state(0, 3, CellState.SKIPPED)

    # From cell 0, next empty should be cell 4 (skipping 1-3)
    next_cell = board.next_empty_cell(0, 0)
    assert next_cell == (0, 4)


def test_next_empty_cell_returns_none_when_all_marked():
    """next_empty_cell should return None if no empty cells remain."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="single", categories=cats)

    # Mark all cells
    for row in range(NUM_ROWS):
        for col in range(NUM_CATEGORIES):
            board.set_state(row, col, CellState.CORRECT)

    # No more empty cells
    next_cell = board.next_empty_cell(NUM_ROWS - 1, NUM_CATEGORIES - 1)
    assert next_cell is None


def test_next_empty_cell_handles_partial_board():
    """next_empty_cell should find next empty even with scattered marked cells."""
    cats = [f"CAT{i}" for i in range(NUM_CATEGORIES)]
    board = Board(round_name="double", categories=cats)

    # Mark row 0, col 0 and row 1, col 2
    board.set_state(0, 0, CellState.CORRECT)
    board.set_state(1, 2, CellState.WRONG)

    # From (0, 0), next empty is (0, 1)
    assert board.next_empty_cell(0, 0) == (0, 1)

    # From (0, NUM_CATEGORIES - 1), next empty is (1, 0)
    assert board.next_empty_cell(0, NUM_CATEGORIES - 1) == (1, 0)

    # From (1, 2), next empty is (1, 3)
    assert board.next_empty_cell(1, 2) == (1, 3)

