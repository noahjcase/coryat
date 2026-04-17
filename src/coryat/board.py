from dataclasses import dataclass, field
from enum import Enum


class CellState(Enum):
    EMPTY = "empty"
    CORRECT = "c"
    WRONG = "w"
    SKIPPED = "."
    UNREVEALED = "u"
    DD_CORRECT = "dc"
    DD_WRONG = "dw"
    DD_SKIPPED = "d."


SINGLE_VALUES = (200, 400, 600, 800, 1000)
DOUBLE_VALUES = (400, 800, 1200, 1600, 2000)
NUM_CATEGORIES = 6
NUM_ROWS = 5


@dataclass
class Cell:
    value: int
    state: CellState = CellState.EMPTY

    @property
    def is_marked(self) -> bool:
        return self.state != CellState.EMPTY

    @property
    def is_daily_double(self) -> bool:
        return self.state in (CellState.DD_CORRECT, CellState.DD_WRONG, CellState.DD_SKIPPED)


@dataclass
class Board:
    round_name: str
    categories: list[str]
    cells: list[list[Cell]] = field(default_factory=list)

    def __post_init__(self):
        values = SINGLE_VALUES if self.round_name == "single" else DOUBLE_VALUES
        if not self.cells:
            self.cells = [
                [Cell(value=values[row]) for _ in range(NUM_CATEGORIES)]
                for row in range(NUM_ROWS)
            ]

    def get(self, row: int, col: int) -> Cell:
        return self.cells[row][col]

    def set_state(self, row: int, col: int, state: CellState):
        self.cells[row][col].state = state

    @property
    def all_marked(self) -> bool:
        return all(cell.is_marked for row in self.cells for cell in row)

    def unmarked_count(self) -> int:
        return sum(1 for row in self.cells for cell in row if not cell.is_marked)

    def can_place_dd(self, row: int, col: int) -> bool:
        """Check if a DD can be placed at (row, col)."""
        # No DD in first row (lowest cash value)
        if row == 0:
            return False
        return True

    def get_dds(self) -> list[tuple[int, int]]:
        """Return list of (row, col) tuples for all DDs on the board."""
        dds = []
        for row_idx, row in enumerate(self.cells):
            for col_idx, cell in enumerate(row):
                if cell.is_daily_double:
                    dds.append((row_idx, col_idx))
        return dds

    def next_empty_cell(self, row: int, col: int) -> tuple[int, int] | None:
        """
        Find the next empty cell in reading order (left-to-right, top-to-bottom)
        starting after (row, col). Returns (row, col) or None if no empty cells remain.
        """
        # Start from the next position in reading order
        start_col = col + 1
        start_row = row

        # Scan rows from current row onwards
        for r in range(start_row, NUM_ROWS):
            # For the first row, start from start_col; for others, start from 0
            c_start = start_col if r == start_row else 0
            for c in range(c_start, NUM_CATEGORIES):
                if self.cells[r][c].state == CellState.EMPTY:
                    return (r, c)
        return None

    def validate_dd_constraints(self) -> str | None:
        """
        Validate DD constraints for a complete board.
        Returns error message if invalid, None if valid.
        """
        dds = self.get_dds()
        single_or_double = self.round_name

        if single_or_double == "single":
            if len(dds) != 1:
                return f"Single Jeopardy must have exactly 1 daily double (found {len(dds)})"
        elif single_or_double == "double":
            if len(dds) > 2:
                return f"Double Jeopardy can have at most 2 daily doubles (found {len(dds)})"
            # If the entire board is revealed, there must be exactly 2 DDs
            if self.all_marked and len(dds) != 2:
                return f"Double Jeopardy board is complete but has {len(dds)} daily doubles (need exactly 2)"
            # If there are 2 DDs, they must be in different columns
            if len(dds) == 2:
                if dds[0][1] == dds[1][1]:
                    return "The 2 Double Jeopardy daily doubles must be in different columns"
        return None

    def to_clue_dicts(self, date: str) -> list[dict]:
        clues = []
        for row in self.cells:
            for col_idx, cell in enumerate(row):
                clues.append(
                    {
                        "date": date,
                        "round": self.round_name,
                        "category": self.categories[col_idx],
                        "value": cell.value,
                        "result": cell.state.value,
                        "is_daily_double": str(cell.is_daily_double).lower(),
                    }
                )
        return clues
