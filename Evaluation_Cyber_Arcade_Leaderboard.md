# Évaluation Cyber : Retro Arcade Leaderboard

## Contexte

Les bornes d'arcade rétro ont la cote, et la question reste toujours la même : qui a le meilleur score ? Le back-office de cette compétition existe déjà : une API de classements multi-jeux (Pac-Man, Tetris, Snake...), avec sa logique anti-triche et ses tests unitaires, vous est fournie clé en main dans le dossier `subject/` (voir `README.md`).

Votre mission n'est pas d'écrire cette API, mais de la rendre exploitable en production comme en vrai : intégrée en continu, conteneurisée, monitorée et alertée. Ce qu'on évalue, c'est votre capacité à prendre en main une application existante et à l'entourer de tout ce qui fait qu'elle tient la charge en production.

## Modalités

- Durée : 3h.
- Travail en solo ou en groupe de 2.
- Notation sur 20 (voir le barème en fin de sujet).
- Stack technique imposée pour le code fourni : Python (FastAPI). Le reste (CI, conteneurisation, monitoring...) reste libre dans le choix des outils, tant que les contraintes ci-dessous sont respectées.
- Livraison : un dépôt Git, avec un `.gitignore` correct, des commits réguliers et un `README.md` qui explique comment lancer le projet.
- Si le dépôt est privé, ajoutez-moi en tant que collaborateur (cbrasseur) et envoyez-moi le lien du repo sur Discord.

## Information 1 : l'API (code fourni, à ne pas réécrire)

L'API HTTP est déjà implémentée dans `app/` et respecte le contrat ci-dessous. Vous n'avez rien à coder dans cette partie : votre travail consiste à comprendre ce contrat, car c'est lui que vous allez conteneuriser, monitorer et solliciter en test de charge.

### Les jeux et leurs scores maximum

Cinq jeux sont gérés, chacun avec un score maximum « humainement atteignable » qui sert à l'anti-triche (voir `app/games.py`) :

```
pacman      ->   999 999
tetris      -> 9 999 999
snake       ->    99 999
breakout    ->   896 980
donkeykong  -> 1 247 700
```

### Les routes disponibles

- `POST /scores`
  - Corps : `{ "player": "AAA", "game": "pacman", "score": 123456 }`
  - Succès : 201 avec le rang obtenu, ex. `{ "rank": 4 }`.
  - Applique les règles anti-triche (voir plus bas).
- `GET /leaderboard/{game}?limit=10`
  - Renvoie le top des scores du jeu, trié du meilleur au moins bon.
  - `limit` est optionnel (défaut 10, plafonné à 100).
- `GET /players/{player}`
  - Renvoie les meilleurs scores du joueur, tous jeux confondus.
- `GET /games`
  - Renvoie la liste des jeux gérés et leur score maximum.
- `GET /health`
  - Renvoie l'état de santé du service, ex. `{ "status": "ok" }`. À utiliser pour le healthcheck Docker.
- `GET /metrics`
  - Expose les métriques au format Prometheus (voir Partie 5).

### Règles anti-triche déjà implémentées

Un score est rejeté (code `4xx` approprié : `400`, `422`, `429`) si :
- le jeu n'existe pas dans la liste gérée (`400`) ;
- le score est négatif ou dépasse le maximum autorisé du jeu (`422`) ;
- le joueur soumet trop vite : cooldown de 2 secondes entre deux soumissions du même joueur sur le même jeu (`429`).

Chaque rejet est comptabilisé dans une métrique avec son motif (voir Partie 5). C'est ce qui vous permettra de visualiser et d'alerter sur les tentatives de triche.

### Persistance

Les scores sont stockés dans une base SQLite (`app/storage.py`), sur un fichier dont le chemin est configurable via la variable d'environnement `DB_PATH`. Pour survivre à un redémarrage du conteneur, ce fichier doit se trouver sur un volume monté : c'est à vous de le prévoir dans votre configuration Docker.

## Information 2 : tests unitaires (fournis, à faire passer en CI)

Les tests unitaires ciblant la logique métier sont déjà écrits dans `tests/test_business.py` (anti-triche, tri du classement, cooldown) et `tests/test_api.py` (intégration HTTP). Vous n'avez pas à en écrire de nouveaux : votre CI doit les exécuter et échouer s'ils échouent.

Info : la logique métier est volontairement séparée de la couche HTTP et de la base (`app/business.py`, sans dépendance à FastAPI ni SQLite). C'est ce qui la rend simple à tester unitairement — gardez ce principe en tête si vous devez toucher au code fourni.

## Prise en main : démarrer et tester l'API fournie

Avant d'attaquer la CI, assurez-vous de savoir faire tourner le code fourni en local. Depuis le dossier `subject/` :

```bash
# 1. Installer les dépendances (runtime + tests + linter)
pip install -r requirements-dev.txt

# 2. Démarrer l'API en local (rechargement automatique du code)
uvicorn app.main:app --reload
```

L'API écoute alors sur `http://127.0.0.1:8000`. Une documentation interactive est générée automatiquement par FastAPI sur `http://127.0.0.1:8000/docs` : pratique pour explorer les routes sans écrire de `curl`.

### Tester les routes manuellement (curl) - Optionnel !!  

**(optionnel) - Cette partie vous permet juste de comprendre / tester ce qui existe déjà. Mais normalement... Je dis bien normalement, tout marche déjà !**

Dans un autre terminal, une fois l'API démarrée :

```bash
# Vérifier que le service répond
curl http://127.0.0.1:8000/health
# => {"status":"ok"}

# Lister les jeux gérés et leur score max
curl http://127.0.0.1:8000/games

# Soumettre un score
curl -X POST http://127.0.0.1:8000/scores \
  -H "Content-Type: application/json" \
  -d '{"player": "AAA", "game": "pacman", "score": 123456}'
# => 201 {"rank":1}

# Consulter le classement d'un jeu
curl "http://127.0.0.1:8000/leaderboard/pacman?limit=5"

# Consulter les meilleurs scores d'un joueur
curl http://127.0.0.1:8000/players/AAA

# Voir les métriques Prometheus exposées
curl http://127.0.0.1:8000/metrics
```

Essayez aussi de déclencher un rejet, pour vérifier les codes d'erreur : un score au-dessus du maximum (`422`), un jeu inconnu (`400`), ou deux soumissions du même joueur/jeu en moins de 2 secondes (`429`).

### Lancer les tests automatisés (nouveau terminal)

```bash
pytest -q
```

Vous devez voir tous les tests passer (19 au total). C'est cette même commande que votre CI doit exécuter à chaque push.

## Partie 1 (à faire !) : intégration continue (la plus complète possible)

Mettez en place une CI (GitHub Actions, GitLab CI...) qui s'exécute à chaque push. Elle doit enchaîner au minimum :
- Build : installation des dépendances Python (`requirements-dev.txt`).
- Linter : analyse statique du code (`ruff check .` déjà configuré via `pyproject.toml`, ou pylint).
- Tests : exécution des tests fournis (`pytest`).
- Analyse de sécurité (SAST) : recherche de vulnérabilités dans le code (Bandit, Semgrep...).
- Analyse des dépendances : recherche de CVE connues dans les dépendances (pip-audit, Trivy...).
- Scan de l'image Docker : analyse de l'image construite (Trivy).

Bonus : une analyse SonarQube / SonarCloud intégrée à la CI (qualité, couverture, code smells).

Ce qu'on attend :
- Le pipeline est vert sur votre dépôt (capture d'écran ou lien dans le README).
- Un échec d'une étape (test qui casse, CVE critique...) fait bien échouer le pipeline. Vous pouvez le démontrer en cassant volontairement un test ou en épinglant une dépendance vulnérable, puis en revenant en arrière.

## Partie 2 (à faire !) : conteneurisation (dev et prod séparés)

L'application doit être entièrement conteneurisée.
- Un `Dockerfile` (idéalement multi-stage) pour construire l'image de l'application à partir du code fourni.
- Une orchestration Docker Compose avec deux environnements distincts :
  - Développement : rechargement à chaud du code (hot-reload), code source monté en volume, logs verbeux, bref de quoi itérer vite.
  - Production : image construite (pas de montage du code source), serveur applicatif, politiques de redémarrage (`restart`).
- Un volume dédié pour la base SQLite (`data/scores.db` ou équivalent via `DB_PATH`), pour que les scores survivent à un redémarrage du conteneur.

On doit pouvoir lancer toute la stack (API + monitoring) avec une seule commande `docker compose ... up`.

Info : la différence dev/prod peut se faire avec deux fichiers compose (override) ou des profils. L'important, c'est que les deux modes soient réels et justifiés, pas un simple copier-coller.

## Partie 3 (à faire !) : monitoring (Prometheus + Grafana)

L'application est déjà observable côté code : elle expose `GET /metrics` au format Prometheus avec, au minimum :
- nombre de requêtes HTTP (par route et par code de statut) ;
- latence des requêtes (histogramme) ;
- nombre de scores soumis (par jeu) ;
- nombre de scores rejetés (par jeu et par motif) ;
- nombre de consultations de classement.

À vous de :
- faire en sorte que Prometheus scrape l'application ;
- construire un dashboard Grafana avec au moins : trafic, latence (p95), taux d'erreur, et un panneau « tentatives de triche » (scores rejetés).

La configuration peut se faire de deux façons : soit par des fichiers de provisioning montés dans les conteneurs (`prometheus.yml`, datasource et dashboard Grafana en `.yml` / `.json`), ce qui est la méthode recommandée car reproductible, soit manuellement dans Grafana et Prometheus si vous préférez. Dans tous les cas, le résultat doit être démontrable.

## Partie 4 (à faire !) : alerting en continu

Mettez en place des alertes qui surveillent le service en permanence. Au minimum trois alertes parmi :
- Service indisponible (l'application ne répond plus / `up == 0`).
- Latence élevée (p95 au-dessus d'un seuil).
- Taux d'erreur élevé (trop de réponses 5xx).
- Pic de triche (taux de scores rejetés anormalement haut).

Les alertes peuvent être gérées via les règles Prometheus + Alertmanager, ou via le système d'alerting de Grafana. Vous devez pouvoir démontrer le déclenchement d'au moins une alerte, par exemple en arrêtant l'API ou en lançant le test de charge de la Partie 7.

## Partie 5 (à faire) : test de montée en charge

Écrivez un test de charge avec k6 (recommandé) ou JMeter qui :
- monte progressivement en charge (ramp-up de la concurrence) ;
- sollicite les routes principales de l'API fournie (soumission de scores et consultation de classements) ;
- permet d'observer l'impact dans Grafana (montée du trafic, de la latence) ;
- est capable de déclencher au moins une alerte de la Partie 6.

Ce qu'on attend :
- Le script de charge est fourni dans le dépôt.
- Une capture d'écran (ou une démo) montre l'effet de la charge dans Grafana et/ou une alerte déclenchée.

## Bonus (optionnel) : déploiement Kubernetes minimal

Après la courte intro Kubernetes faite en cours, si vous avez le temps, déployez l'API sur un cluster Kubernetes local (kind, minikube, ou le cluster intégré à Docker Desktop). Trois briques suffisent :

- **Pod** : la plus petite unité déployable, un ou plusieurs conteneurs qui partagent réseau et stockage. Vous n'en créez jamais un directement.
- **Deployment** : garde un nombre donné de Pods identiques en vie (les recrée s'ils crashent), à partir d'un modèle de Pod — ici, l'image Docker construite en Partie 2.
- **Service** : une adresse réseau stable qui route le trafic vers les Pods du Deployment, même quand ceux-ci sont recréés (leur IP change à chaque fois).

Concrètement :
- Réutilisez l'image Docker construite en Partie 2 (pas besoin de la publier sur un registry : chargez-la directement dans le cluster local, ex. `kind load docker-image ...` ou l'équivalent minikube).
- Un `Deployment` qui fait tourner l'API à partir de cette image.
- Un `Service` qui expose l'API dans le cluster (`ClusterIP` + `kubectl port-forward`, ou `NodePort` si vous préférez y accéder directement).
- Des probes `readiness` et `liveness` sur `GET /health` (l'endpoint existe déjà, aucune modification de code nécessaire).

Ce qu'on attend :
- Les fichiers YAML (`k8s/deployment.yaml`, `k8s/service.yaml` ou équivalent) dans le dépôt.
- Une démonstration que le pod est bien `Running` / `Ready` (`kubectl get pods`) et que l'API répond via le Service (`kubectl port-forward` + `curl /health`) — capture d'écran ou lien dans le README.

Hors scope pour ce bonus, volontairement, faute de temps : Ingress, autoscaling (HPA), ConfigMap/Secret dédiés, Helm, ou l'intégration du monitoring Prometheus/Grafana dans le cluster. Le monitoring de la Partie 3 peut rester en Docker Compose classique, indépendamment de ce bonus.

## Livrables

- Le dépôt Git complet : le code fourni (API + tests, non modifiés sauf nécessité justifiée), le `Dockerfile` et les fichiers Compose (dev + prod), la configuration CI, la configuration Prometheus/Grafana/alerting, et le script de charge.
- (Si bonus tenté) les manifestes Kubernetes (`k8s/`).
- Un `README.md` qui explique les choix techniques, comment lancer le projet (dev et prod), et où voir le monitoring et les alertes.
- Quelques captures d'écran : CI verte, dashboard Grafana, alerte déclenchée.

## Barème (sur 20) - Il sera pas respecté à la lettre, c'est un barème "indicatif"

Le respect complet et fonctionnel des attendus donne 17/20. Les 3 points restants récompensent ce qui dépasse les attentes : qualité, soin, bonus Sonar, pertinence des alertes, dashboard travaillé, documentation soignée, sécurité poussée.

- CI (build, linter, tests fournis, SAST, dépendances, scan image) qui échoue quand il le faut : 7 pts
- Conteneurisation : Dockerfile + dev/prod réellement distincts, volume de persistance, stack lançable en une commande : 4 pts
- Monitoring : Prometheus qui scrape `/metrics`, dashboard Grafana lisible : 3 pts
- Alerting : au moins 3 alertes, déclenchement démontré : 2 pts
- Montée en charge : script k6/JMeter fonctionnel, impact observable : 1 pt
- Dépassement des attentes (bonus Sonar, qualité, soin, doc, sécurité...) : 3 pts

### Bonus Kubernetes (en plus du /20)

- Déploiement Kubernetes minimal fonctionnel (Deployment + Service + probes `/health`, pod `Ready`, accès démontré) : +1 pt bonus.

Pénalités possibles :
- Dépôt sans `.gitignore` ou avec des secrets/artefacts commités : -2 pts.
- Pas de séparation dev/prod réelle : -2 pts.
- Application qui ne démarre pas en l'état : -3 pts.
- Code fourni (API/tests) modifié sans justification claire dans le README : -1 pt.

Bon courage.
