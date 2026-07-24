"""API HTTP du Retro Arcade Leaderboard.

Contrat fonctionnel : voir le sujet d'évaluation. Ce module ne contient que
le câblage HTTP ; les règles métier vivent dans `business.py` et sont
testées indépendamment de FastAPI (voir tests/test_business.py).
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI, HTTPException, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.business import compute_rank, is_cooldown_active, sort_leaderboard, validate_score
from app.games import GAMES
from app.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    LEADERBOARD_VIEWS_TOTAL,
    SCORES_REJECTED_TOTAL,
    SCORES_SUBMITTED_TOTAL,
)
from app.models import (
    GameInfo,
    HealthStatus,
    LeaderboardEntry,
    PlayerBestScore,
    ScoreAccepted,
    ScoreSubmission,
)
from app.storage import ScoreRepository

DB_PATH = os.environ.get("DB_PATH", "data/scores.db")
DEFAULT_LEADERBOARD_LIMIT = 10
MAX_LEADERBOARD_LIMIT = 100

app = FastAPI(title="Retro Arcade Leaderboard")
repository = ScoreRepository(DB_PATH)

REJECTION_STATUS_CODES = {
    "unknown_game": 400,
    "negative_score": 422,
    "score_too_high": 422,
    "cooldown": 429,
}


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    route_path = route.path if route is not None else request.url.path

    HTTP_REQUESTS_TOTAL.labels(
        route=route_path, method=request.method, status=response.status_code
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        route=route_path, method=request.method
    ).observe(duration)
    return response


@app.post("/scores", response_model=ScoreAccepted, status_code=201)
def submit_score(submission: ScoreSubmission) -> ScoreAccepted:
    reason = validate_score(submission.game, submission.score, GAMES)

    if reason is None:
        last_submission = repository.last_submission_time(
            submission.player, submission.game
        )
        if is_cooldown_active(last_submission, time.time()):
            reason = "cooldown"

    if reason is not None:
        SCORES_REJECTED_TOTAL.labels(game=submission.game, reason=reason).inc()
        raise HTTPException(status_code=REJECTION_STATUS_CODES[reason], detail=reason)

    existing_scores = repository.scores_for_game(submission.game)
    rank = compute_rank(existing_scores, submission.score)
    repository.add_score(submission.player, submission.game, submission.score)
    SCORES_SUBMITTED_TOTAL.labels(game=submission.game).inc()

    return ScoreAccepted(rank=rank)


@app.get("/leaderboard/{game}", response_model=list[LeaderboardEntry])
def get_leaderboard(
    game: str, limit: int = Query(default=DEFAULT_LEADERBOARD_LIMIT, ge=1)
) -> list[LeaderboardEntry]:
    if game not in GAMES:
        raise HTTPException(status_code=404, detail="unknown_game")

    limit = min(limit, MAX_LEADERBOARD_LIMIT)
    LEADERBOARD_VIEWS_TOTAL.labels(game=game).inc()

    entries = sort_leaderboard(repository.leaderboard(game, limit))
    return [LeaderboardEntry(player=player, score=score) for player, score in entries]


@app.get("/players/{player}", response_model=list[PlayerBestScore])
def get_player_best_scores(player: str) -> list[PlayerBestScore]:
    scores = repository.best_scores_for_player(player)
    return [PlayerBestScore(game=game, score=score) for game, score in scores]


@app.get("/games", response_model=list[GameInfo])
def get_games() -> list[GameInfo]:
    return [GameInfo(game=game, max_score=max_score) for game, max_score in GAMES.items()]


@app.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(status="ok")


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
