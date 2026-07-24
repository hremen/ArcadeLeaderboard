"""Tests unitaires de la logique métier (app/business.py).

Ces tests ne touchent ni HTTP ni base de données : c'est tout l'intérêt
d'avoir séparé la logique métier en fonctions pures.
"""

from app.business import compute_rank, is_cooldown_active, sort_leaderboard, validate_score
from app.games import GAMES


def test_valid_score_is_accepted():
    assert validate_score("pacman", 123_456, GAMES) is None


def test_score_above_game_max_is_rejected():
    assert validate_score("pacman", 1_000_000, GAMES) == "score_too_high"


def test_unknown_game_is_rejected():
    assert validate_score("pong", 100, GAMES) == "unknown_game"


def test_negative_score_is_rejected():
    assert validate_score("snake", -1, GAMES) == "negative_score"


def test_leaderboard_is_sorted_best_first():
    entries = [("alice", 500), ("bob", 900), ("carol", 100)]
    assert sort_leaderboard(entries) == [("bob", 900), ("alice", 500), ("carol", 100)]


def test_cooldown_rejects_submission_too_close_in_time():
    last_submission = 1_000.0
    now = 1_001.0  # 1 seconde après, cooldown = 2s
    assert is_cooldown_active(last_submission, now) is True


def test_cooldown_allows_submission_after_delay():
    last_submission = 1_000.0
    now = 1_003.0  # 3 secondes après, cooldown = 2s
    assert is_cooldown_active(last_submission, now) is False


def test_cooldown_allows_first_submission():
    assert is_cooldown_active(None, 1_000.0) is False


def test_compute_rank_first_place():
    assert compute_rank(existing_scores=[100, 200, 300], new_score=500) == 1


def test_compute_rank_last_place():
    assert compute_rank(existing_scores=[100, 200, 300], new_score=50) == 4
