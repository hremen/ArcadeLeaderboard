"""Tests d'intégration légers de la couche HTTP.

Le gros de la logique est déjà couvert par tests/test_business.py ; ces
tests vérifient surtout le câblage (routes, codes de retour, sérialisation).
"""


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_games_lists_all_games_with_max_score(client):
    response = client.get("/games")
    assert response.status_code == 200
    games = {g["game"]: g["max_score"] for g in response.json()}
    assert games["pacman"] == 999_999
    assert games["tetris"] == 9_999_999


def test_submit_valid_score_returns_201_with_rank(client):
    response = client.post(
        "/scores", json={"player": "AAA", "game": "pacman", "score": 123_456}
    )
    assert response.status_code == 201
    assert response.json() == {"rank": 1}


def test_submit_score_above_max_is_rejected(client):
    response = client.post(
        "/scores", json={"player": "AAA", "game": "pacman", "score": 1_000_000}
    )
    assert response.status_code == 422


def test_submit_score_unknown_game_is_rejected(client):
    response = client.post(
        "/scores", json={"player": "AAA", "game": "pong", "score": 100}
    )
    assert response.status_code == 400


def test_submit_score_too_fast_hits_cooldown(client):
    payload = {"player": "AAA", "game": "snake", "score": 100}
    first = client.post("/scores", json=payload)
    second = client.post("/scores", json={**payload, "score": 200})
    assert first.status_code == 201
    assert second.status_code == 429


def test_leaderboard_is_sorted_best_first(client):
    client.post("/scores", json={"player": "alice", "game": "breakout", "score": 500})
    client.post("/scores", json={"player": "bob", "game": "breakout", "score": 900})
    response = client.get("/leaderboard/breakout")
    assert response.status_code == 200
    scores = [entry["score"] for entry in response.json()]
    assert scores == sorted(scores, reverse=True)


def test_leaderboard_unknown_game_returns_404(client):
    response = client.get("/leaderboard/pong")
    assert response.status_code == 404


def test_metrics_endpoint_exposes_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
