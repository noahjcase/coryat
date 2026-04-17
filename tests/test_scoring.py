from coryat.scoring import coryat


def _clue(result, value=200):
    return {"result": result, "value": value}


def test_all_correct():
    clues = [_clue("c", 200), _clue("c", 400)]
    assert coryat(clues) == 600


def test_all_wrong():
    clues = [_clue("w", 200), _clue("w", 400)]
    assert coryat(clues) == -600


def test_mixed():
    clues = [_clue("c", 400), _clue("w", 200), _clue(".", 600), _clue("u", 800)]
    assert coryat(clues) == 200


def test_dd_correct():
    clues = [_clue("dc", 600)]
    assert coryat(clues) == 600


def test_dd_wrong():
    clues = [_clue("dw", 600)]
    assert coryat(clues) == -600


def test_skipped_and_unrevealed_contribute_zero():
    clues = [_clue(".", 1000), _clue("u", 2000)]
    assert coryat(clues) == 0


def test_empty_game():
    assert coryat([]) == 0


def test_all_result_codes():
    clues = [
        _clue("c", 200),
        _clue("w", 400),
        _clue(".", 600),
        _clue("u", 800),
        _clue("dc", 1000),
        _clue("dw", 1200),
    ]
    # 200 - 400 + 0 + 0 + 1000 - 1200 = -400
    assert coryat(clues) == -400
