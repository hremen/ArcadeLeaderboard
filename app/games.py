"""Référentiel des jeux gérés par le leaderboard et de leur score maximum
« humainement atteignable » (utilisé pour la règle anti-triche)."""

GAMES: dict[str, int] = {
    "pacman": 999_999,
    "tetris": 9_999_999,
    "snake": 99_999,
    "breakout": 896_980,
    "donkeykong": 1_247_700,
}
