"""Schémas Pydantic pour les corps de requête / réponse de l'API."""

from pydantic import BaseModel, Field


class ScoreSubmission(BaseModel):
    player: str = Field(min_length=1, max_length=64)
    game: str
    score: int


class ScoreAccepted(BaseModel):
    rank: int


class LeaderboardEntry(BaseModel):
    player: str
    score: int


class PlayerBestScore(BaseModel):
    game: str
    score: int


class GameInfo(BaseModel):
    game: str
    max_score: int


class HealthStatus(BaseModel):
    status: str
