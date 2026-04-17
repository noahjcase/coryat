def coryat(clues: list[dict]) -> int:
    score = 0
    for clue in clues:
        if clue["result"] in ("c", "dc"):
            score += int(clue["value"])
        elif clue["result"] in ("x", "dx"):
            score -= int(clue["value"])
    return score
