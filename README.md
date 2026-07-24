# Retro Arcade Leaderboard — code fourni

Projet realise par **REMEN Hugo** et **WOLF Bryan** — ESI CYB 25-27

Ce dossier contient l'API et les tests unitaires **déjà écrits** pour
l'évaluation Cyber. Voir `Evaluation_Cyber_Arcade_Leaderboard.md` pour
l'énoncé complet et ce qui est attendu de vous.

## Lancer l'API en local

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate sous Windows
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

L'API écoute par défaut sur `http://127.0.0.1:8000`. La base SQLite est
créée automatiquement dans `data/scores.db` (chemin surchargeable via la
variable d'environnement `DB_PATH`). Documentation interactive (Swagger)
disponible sur `http://127.0.0.1:8000/docs`.

## Tester manuellement (curl)

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/scores \
  -H "Content-Type: application/json" \
  -d '{"player": "AAA", "game": "pacman", "score": 123456}'

curl "http://127.0.0.1:8000/leaderboard/pacman?limit=5"
curl http://127.0.0.1:8000/players/AAA
curl http://127.0.0.1:8000/games
curl http://127.0.0.1:8000/metrics
```

## Lancer les tests

```bash
pytest -q
```

## Vérifier le linter

```bash
ruff check .
```

## Structure du code

```
app/
  main.py       # routes FastAPI (câblage HTTP uniquement)
  business.py   # règles métier pures (anti-triche, classement, cooldown)
  storage.py    # persistance SQLite
  metrics.py    # métriques Prometheus
  models.py     # schémas Pydantic
  games.py      # référentiel des jeux et de leur score max
tests/
  test_business.py  # tests unitaires de la logique métier
  test_api.py        # tests d'intégration de la couche HTTP
```

La logique métier (`business.py`) est volontairement indépendante de
FastAPI et de SQLite : c'est ce qui permet de la tester sans monter de
serveur ni de base de données.

---

## Lancer avec Docker

### En prod

```bash
docker compose -f docker-compose.yml up --build -d
```

### En dev (hot-reload)

```bash
docker compose up --build -d
```

En dev, le fichier `docker-compose.override.yml` est charge automatiquement par Docker Compose. Il monte le code source en volume pour le hot-reload et active les logs en mode debug. En prod, le code est copie dans l'image, pas de volume de code, et le conteneur redemarre tout seul s'il plante (`restart: unless-stopped`).

Les scores sont stockes dans une base SQLite sur un volume Docker (`app_data`), donc ils survivent aux redemarrages.

## Difference dev / prod

| | Dev | Prod |
|---|---|---|
| Stage Dockerfile | `development` | `production` |
| Hot-reload | Oui (code monte en volume) | Non (code copie dans l'image) |
| Logs | Debug | Default |
| Restart policy | `no` | `unless-stopped` |
| Deps de test | Installees | Non installees |

## Services

| Service | URL | Login |
|---------|-----|-------|
| API | http://localhost:8000 | - |
| Swagger | http://localhost:8000/docs | - |

## CI

Le pipeline GitHub Actions (`.github/workflows/ci.yml`) tourne a chaque push sur `prod` et `test` :

1. Lint avec `ruff`
2. Tests avec `pytest` (19 tests)
3. Scan de securite avec `bandit`
4. Scan des dependances avec `pip-audit`
5. Build de l'image Docker
6. Scan de l'image avec Trivy

## Kubernetes (bonus)

```bash
docker build --target production -t arcade-api .
kind load docker-image arcade-api:latest
kubectl apply -f k8s/
kubectl port-forward svc/arcade-api 8000:8000
```

Probes readiness et liveness sur `/health`.

## Choix techniques

- **Dockerfile multi-stage** : un stage dev avec les deps de test et le hot-reload, un stage prod minimal.
- **docker-compose.override.yml** : mecanisme natif de Docker Compose pour separer dev et prod.
