"""Couche de persistance : SQLite, un fichier sur disque (survit aux redémarrages
quand le fichier est sur un volume monté)."""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class ScoreRepository:
    def __init__(self, db_path: str = "data/scores.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    game TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    submitted_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scores_game ON scores(game)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scores_player ON scores(player)"
            )

    def last_submission_time(self, player: str, game: str) -> float | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT MAX(submitted_at) FROM scores
                WHERE player = ? AND game = ?
                """,
                (player, game),
            ).fetchone()
        return row[0] if row and row[0] is not None else None

    def scores_for_game(self, game: str) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT score FROM scores WHERE game = ?", (game,)
            ).fetchall()
        return [r[0] for r in rows]

    def add_score(
        self, player: str, game: str, score: int, submitted_at: float | None = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scores (player, game, score, submitted_at)
                VALUES (?, ?, ?, ?)
                """,
                (player, game, score, submitted_at or time.time()),
            )

    def leaderboard(self, game: str, limit: int = 10) -> list[tuple[str, int]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT player, score FROM scores
                WHERE game = ?
                ORDER BY score DESC
                LIMIT ?
                """,
                (game, limit),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def best_scores_for_player(self, player: str) -> list[tuple[str, int]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT game, MAX(score) FROM scores
                WHERE player = ?
                GROUP BY game
                """,
                (player,),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]
