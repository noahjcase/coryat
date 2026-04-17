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
        return self.state in (CellState.DD_CORRECT, CellState.DD_WRONG)


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
