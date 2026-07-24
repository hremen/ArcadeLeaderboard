"""Métriques Prometheus exposées par l'application (voir GET /metrics)."""

from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Nombre de requêtes HTTP reçues",
    ["route", "method", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Latence des requêtes HTTP",
    ["route", "method"],
)

SCORES_SUBMITTED_TOTAL = Counter(
    "scores_submitted_total",
    "Nombre de scores soumis avec succès",
    ["game"],
)

SCORES_REJECTED_TOTAL = Counter(
    "scores_rejected_total",
    "Nombre de scores rejetés",
    ["game", "reason"],
)

LEADERBOARD_VIEWS_TOTAL = Counter(
    "leaderboard_views_total",
    "Nombre de consultations de classement",
    ["game"],
)
