import pytest
from fastapi.testclient import TestClient

from app import main
from app.storage import ScoreRepository


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Client de test avec une base SQLite isolée et vide pour chaque test."""
    fresh_repository = ScoreRepository(str(tmp_path / "test_scores.db"))
    monkeypatch.setattr(main, "repository", fresh_repository)
    return TestClient(main.app)
