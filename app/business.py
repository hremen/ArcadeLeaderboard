"""Logique métier pure : aucune dépendance HTTP ni base de données.

Séparer cette logique de la couche API/DB est ce qui la rend simple à tester
unitairement (voir tests/test_business.py).
"""

from __future__ import annotations

COOLDOWN_SECONDS = 2.0


def validate_score(game: str, score: int, games: dict[str, int]) -> str | None:
    """Vérifie les règles anti-triche indépendantes du temps.

    Retourne un code de motif de rejet, ou None si le score est valide.
    """
    if game not in games:
        return "unknown_game"
    if score < 0:
        return "negative_score"
    if score > games[game]:
        return "score_too_high"
    return None


def is_cooldown_active(
    last_submission_ts: float | None,
    now_ts: float,
    cooldown_seconds: float = COOLDOWN_SECONDS,
) -> bool:
    """True si le joueur a déjà soumis un score sur ce jeu il y a moins de
    `cooldown_seconds`."""
    if last_submission_ts is None:
        return False
    return (now_ts - last_submission_ts) < cooldown_seconds


def compute_rank(existing_scores: list[int], new_score: int) -> int:
    """Rang (1 = meilleur) qu'obtiendrait `new_score` parmi `existing_scores`."""
    better = sum(1 for s in existing_scores if s > new_score)
    return better + 1


def sort_leaderboard(entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Trie une liste de (joueur, score) du meilleur au moins bon."""
    return sorted(entries, key=lambda entry: entry[1], reverse=True)
