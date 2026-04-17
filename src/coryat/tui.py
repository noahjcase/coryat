"""blessed-based TUI for playj."""

import sys

from blessed import Terminal

from .board import Board, CellState, NUM_CATEGORIES, NUM_ROWS

CELL_W = 13  # inner width of each cell column
CELL_H = 3   # inner height (1 content line + 2 borders counted from divider perspective)

_STATE_SYMBOL = {
    CellState.EMPTY: "",
    CellState.CORRECT: "\u2713",
    CellState.WRONG: "\u2717",
    CellState.SKIPPED: "\u00b7",
    CellState.UNREVEALED: "\u2013",
    CellState.DD_CORRECT: "DD\u2713",
    CellState.DD_WRONG: "DD\u2717",
    CellState.DD_SKIPPED: "DD\u00b7",
}


def _color_for_state(term: Terminal, state: CellState) -> str:
    if state in (CellState.CORRECT, CellState.DD_CORRECT):
        return term.green
    if state in (CellState.WRONG, CellState.DD_WRONG):
        return term.red
    if state == CellState.SKIPPED:
        return term.yellow
    if state == CellState.UNREVEALED:
        return term.dim
    return term.dim


def _prompt_categories(term: Terminal, round_label: str, prefilled: list[str] | None) -> list[str]:
    if prefilled:
        return prefilled

    print(term.clear)
    print(term.bold(f"Enter categories for {round_label} (press Enter after each):"))
    cats = []
    for i in range(NUM_CATEGORIES):
        while True:
            sys.stdout.write(f"  Category {i + 1}: ")
            sys.stdout.flush()
            name = sys.stdin.readline().rstrip("\n")
            if name.strip():
                cats.append(name.strip())
                break
    return cats


def _wrap_text(text: str, width: int) -> list[str]:
    """Wrap text into lines of max width characters."""
    lines = []
    while text:
        lines.append(text[:width])
        text = text[width:]
    return lines if lines else [""]


def _render_board(term: Terminal, board: Board, cur_row: int, cur_col: int, status: str):
    print(term.home + term.clear, end="")

    # Header
    round_label = "Single Jeopardy!" if board.round_name == "single" else "Double Jeopardy!"
    print(term.bold(f"  {round_label}"))
    print()

    # Category rows (wrapped to fit in available space)
    cat_lines = [_wrap_text(cat, CELL_W) for cat in board.categories]
    max_lines = max(len(lines) for lines in cat_lines) if cat_lines else 1

    for line_idx in range(max_lines):
        cat_row = ""
        for cat_idx, cat_line_list in enumerate(cat_lines):
            if line_idx < len(cat_line_list):
                line_text = cat_line_list[line_idx].center(CELL_W)
            else:
                line_text = " " * CELL_W
            cat_row += line_text + " "
        print("  " + cat_row)

    # Top border
    top = "\u250c" + ("\u2500" * CELL_W + "\u252c") * (NUM_CATEGORIES - 1) + "\u2500" * CELL_W + "\u2510"
    print("  " + top)

    for row_idx in range(NUM_ROWS):
        # Content row
        content = "\u2502"
        for col_idx in range(NUM_CATEGORIES):
            cell = board.get(row_idx, col_idx)
            is_active = row_idx == cur_row and col_idx == cur_col

            if cell.state == CellState.EMPTY:
                text = str(cell.value).center(CELL_W)
                color = term.dim
            else:
                sym = _STATE_SYMBOL[cell.state]
                text = sym.center(CELL_W)
                color = _color_for_state(term, cell.state)
                if cell.state in (CellState.DD_CORRECT, CellState.DD_WRONG, CellState.DD_SKIPPED):
                    color = color + term.bold

            if is_active:
                content += term.reverse(text) + "\u2502"
            else:
                content += color + text + term.normal + "\u2502"

        print("  " + content)

        # Divider or bottom border
        if row_idx < NUM_ROWS - 1:
            div = "\u251c" + ("\u2500" * CELL_W + "\u253c") * (NUM_CATEGORIES - 1) + "\u2500" * CELL_W + "\u2524"
        else:
            div = "\u2514" + ("\u2500" * CELL_W + "\u2534") * (NUM_CATEGORIES - 1) + "\u2500" * CELL_W + "\u2518"
        print("  " + div)

    print()
    print(f"  {status}")
    print()
    print("  [arrows] move  [c]orrect  [x]wrong  [.]skip  [u]nrevealed  [d]aily double")
    print("  [Tab] next round  [s]ave  [q]uit")


def _dd_overlay(term: Terminal) -> CellState | None:
    """Show the Daily Double overlay. Returns DD_CORRECT, DD_WRONG, DD_SKIPPED, or None (cancel)."""
    width = 36
    lines = [
        "\u250c" + "\u2500" * (width - 2) + "\u2510",
        "\u2502" + "      DAILY DOUBLE       ".center(width - 2) + "\u2502",
        "\u2502" + "  [c] correct [x] wrong [.] skip  ".center(width - 2) + "\u2502",
        "\u2514" + "\u2500" * (width - 2) + "\u2518",
    ]
    # Center on screen
    row_start = (term.height - len(lines)) // 2
    col_start = (term.width - width) // 2
    for i, line in enumerate(lines):
        print(term.move(row_start + i, col_start) + line, end="")
    sys.stdout.flush()

    with term.cbreak():
        while True:
            key = term.inkey()
            if key == "c":
                return CellState.DD_CORRECT
            if key == "w":
                return CellState.DD_WRONG
            if key == ".":
                return CellState.DD_SKIPPED
            if key.name == "KEY_ESCAPE" or key == "\x1b":
                return None


def _confirm(term: Terminal, message: str) -> bool:
    print(f"  {message} [y/n] ", end="")
    sys.stdout.flush()
    with term.cbreak():
        key = term.inkey()
    print()
    return str(key).lower() == "y"


def _advance_to_next_empty(board: Board, cur_row: int, cur_col: int) -> tuple[int, int]:
    """After marking a cell, advance to next empty cell if one exists."""
    next_cell = board.next_empty_cell(cur_row, cur_col)
    if next_cell is not None:
        return next_cell
    return (cur_row, cur_col)


def run_tui(
    date: str,
    single_cats: list[str] | None,
    double_cats: list[str] | None,
    scrape_status: str,
) -> tuple[list[dict], int] | None:
    """
    Run the full TUI session.
    Returns (clues, coryat_score) on successful save, or None if user quits.
    """
    term = Terminal()

    # Category entry for Single J!
    single_categories = _prompt_categories(term, "Single Jeopardy!", single_cats)
    single_board = Board(round_name="single", categories=single_categories)

    cur_row, cur_col = 0, 0
    status = scrape_status

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # --- Single Jeopardy round ---
        while True:
            _render_board(term, single_board, cur_row, cur_col, status)
            key = term.inkey()

            if key.name == "KEY_UP":
                cur_row = max(0, cur_row - 1)
            elif key.name == "KEY_DOWN":
                cur_row = min(NUM_ROWS - 1, cur_row + 1)
            elif key.name == "KEY_LEFT":
                cur_col = max(0, cur_col - 1)
            elif key.name == "KEY_RIGHT":
                cur_col = min(NUM_CATEGORIES - 1, cur_col + 1)
            elif key == "c":
                single_board.set_state(cur_row, cur_col, CellState.CORRECT)
                cur_row, cur_col = _advance_to_next_empty(single_board, cur_row, cur_col)
            elif key == "x":
                single_board.set_state(cur_row, cur_col, CellState.WRONG)
                cur_row, cur_col = _advance_to_next_empty(single_board, cur_row, cur_col)
            elif key == ".":
                single_board.set_state(cur_row, cur_col, CellState.SKIPPED)
                cur_row, cur_col = _advance_to_next_empty(single_board, cur_row, cur_col)
            elif key == "u":
                single_board.set_state(cur_row, cur_col, CellState.UNREVEALED)
                cur_row, cur_col = _advance_to_next_empty(single_board, cur_row, cur_col)
            elif key == "d":
                if not single_board.can_place_dd(cur_row, cur_col):
                    status = "Cannot place DD in first row (lowest value)"
                    continue
                # Check if already at max DDs for Single J!
                if len(single_board.get_dds()) >= 1 and not single_board.get(cur_row, cur_col).is_daily_double:
                    status = "Single Jeopardy already has 1 daily double"
                    continue
                result = _dd_overlay(term)
                if result is not None:
                    single_board.set_state(cur_row, cur_col, result)
                    cur_row, cur_col = _advance_to_next_empty(single_board, cur_row, cur_col)
            elif key.name == "KEY_TAB":
                if not single_board.all_marked:
                    status = f"cannot advance: {single_board.unmarked_count()} cell(s) unmarked. use [u] for unrevealed."
                    continue
                # Validate Single J! DD constraints
                dd_error = single_board.validate_dd_constraints()
                if dd_error:
                    status = dd_error
                    continue
                _render_board(term, single_board, cur_row, cur_col, status)
                if _confirm(term, "Switch to Double Jeopardy? All Single J! cells are filled."):
                    break
            elif key == "s":
                status = "cannot save: finish Single Jeopardy first, then use [Tab]."
            elif key == "q":
                _render_board(term, single_board, cur_row, cur_col, status)
                if _confirm(term, "Quit without saving?"):
                    return None

        # --- Category entry for Double J! ---
    # Exit fullscreen for category input, then re-enter
    double_categories = _prompt_categories(term, "Double Jeopardy!", double_cats)
    double_board = Board(round_name="double", categories=double_categories)
    cur_row, cur_col = 0, 0
    status = scrape_status

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # --- Double Jeopardy round ---
        while True:
            _render_board(term, double_board, cur_row, cur_col, status)
            key = term.inkey()

            if key.name == "KEY_UP":
                cur_row = max(0, cur_row - 1)
            elif key.name == "KEY_DOWN":
                cur_row = min(NUM_ROWS - 1, cur_row + 1)
            elif key.name == "KEY_LEFT":
                cur_col = max(0, cur_col - 1)
            elif key.name == "KEY_RIGHT":
                cur_col = min(NUM_CATEGORIES - 1, cur_col + 1)
            elif key == "c":
                double_board.set_state(cur_row, cur_col, CellState.CORRECT)
                cur_row, cur_col = _advance_to_next_empty(double_board, cur_row, cur_col)
            elif key == "x":
                double_board.set_state(cur_row, cur_col, CellState.WRONG)
                cur_row, cur_col = _advance_to_next_empty(double_board, cur_row, cur_col)
            elif key == ".":
                double_board.set_state(cur_row, cur_col, CellState.SKIPPED)
                cur_row, cur_col = _advance_to_next_empty(double_board, cur_row, cur_col)
            elif key == "u":
                double_board.set_state(cur_row, cur_col, CellState.UNREVEALED)
                cur_row, cur_col = _advance_to_next_empty(double_board, cur_row, cur_col)
            elif key == "d":
                if not double_board.can_place_dd(cur_row, cur_col):
                    status = "Cannot place DD in first row (lowest value)"
                    continue
                # Check if already at max DDs for Double J!
                dds = double_board.get_dds()
                if len(dds) >= 2 and not double_board.get(cur_row, cur_col).is_daily_double:
                    status = "Double Jeopardy already has 2 daily doubles"
                    continue
                # Check for different column constraint if placing 2nd DD
                if len(dds) == 1 and not double_board.get(cur_row, cur_col).is_daily_double:
                    if dds[0][1] == cur_col:
                        status = "2 DDs must be in different columns"
                        continue
                result = _dd_overlay(term)
                if result is not None:
                    double_board.set_state(cur_row, cur_col, result)
                    cur_row, cur_col = _advance_to_next_empty(double_board, cur_row, cur_col)
            elif key == "s":
                if not double_board.all_marked:
                    status = f"cannot save: {double_board.unmarked_count()} cell(s) unmarked. use [u] for unrevealed."
                    continue
                # Validate DD constraints
                dd_error = double_board.validate_dd_constraints()
                if dd_error:
                    status = dd_error
                    continue
                # Build clue list and return
                all_clues = (
                    single_board.to_clue_dicts(date) + double_board.to_clue_dicts(date)
                )
                from .scoring import coryat as calc_coryat
                score = calc_coryat(all_clues)
                return all_clues, score
            elif key == "q":
                _render_board(term, double_board, cur_row, cur_col, status)
                if _confirm(term, "Quit without saving?"):
                    return None
