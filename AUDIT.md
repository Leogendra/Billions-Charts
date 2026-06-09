# Audit Backend — Billions Charts

> Date : 2026-06-05  
> Périmètre : `app.py`, `backend/scrapper.py`, `backend/track_enricher.py`, `backend/database.py`, `backend/report.py`, `backend/utils.py`  
> Sévérité : 🔴 Critique · 🟠 Élevée · 🟡 Moyenne · 🔵 Faible

---


## 3. Scalabilité

### 🟠 Sc-1 — Opérations longues dans le handler HTTP (thread bloqué)

**Fichier :** `app.py:61-62`

```python
fetch_playlist_infos(dataPath, WRITE_TO_DATABASE)
generate_report(dataPath, reportPublicPath, WRITE_TO_DATABASE)
```

Ces deux appels peuvent prendre plusieurs minutes (centaines de requêtes Spotify). Tout ce temps, le thread Flask est bloqué. Avec un serveur single-worker (ex. : `flask run` ou Gunicorn par défaut), l'application est totalement indisponible pendant le scraping.

**Correction :** Exécuter ces opérations en arrière-plan (Celery, RQ, ou un simple thread avec retour de job ID), et exposer un endpoint de statut séparé.

---

### 🟠 Sc-2 — Lookups ISRC séquentiels et non parallélisés

**Fichier :** `backend/track_enricher.py:94-146`

Pour les N tracks non encore corrigés, les lookups ISRC sont séquentiels avec `time.sleep(0.1)` entre chaque appel. Pour 500 tracks non-corrigés, cela représente au minimum 50 secondes uniquement pour ces requêtes.

La condition du sleep est également incohérente : `if (i > 50)` applique le délai seulement après le 50ème track, exposant les premiers appels à un potential rate-limit Spotify.

**Correction :** Utiliser un thread pool (`concurrent.futures.ThreadPoolExecutor`) avec un sémaphore pour limiter le débit, ou l'API batch si disponible.

---

### 🟡 Sc-3 — Absence d'index MongoDB

**Fichier :** `backend/database.py`

Les requêtes fréquentes filtrent sur `{"date": date}`, `{"id": {"$in": track_ids}}` et `{"id": artist_id}`, mais aucun index n'est créé ni documenté. Sans index sur `id` et `date`, ces requêtes font un full collection scan.

**Correction :** Créer les index au démarrage ou via une migration :
```python
tracks_collection.create_index("id", unique=True)
playlists_collection.create_index("date", unique=True)
artists_collection.create_index("id", unique=True)
```

---

### 🟡 Sc-5 — `retrieve_playlist_infos_from_mongo` charge tout en mémoire

**Fichier :** `backend/database.py:151-182`

La fonction charge l'intégralité des tracks et artistes dans des dictionnaires en mémoire. Pour un rapport avec 1000+ tracks et leur données d'artistes, l'empreinte mémoire peut devenir significative.

---

## Propositions de corrections

### Sc-1 — Opérations longues bloquent le thread HTTP
La solution la plus légère pour ce projet est un thread Python lancé via `threading.Thread` avec un dictionnaire partagé pour stocker le statut du job (`pending`, `running`, `done`, `error`). Un endpoint `/status/` permet au client de poller l'avancement. Si le projet grandit, une queue de tâches dédiée (RQ avec Redis, ou Celery) offre plus de robustesse et de visibilité.

### Sc-2 — Lookups ISRC séquentiels non parallélisés
Un `ThreadPoolExecutor` avec 5 à 10 workers simultanés réduirait le temps de traitement d'un facteur équivalent, avec un sémaphore ou une `Queue` pour contrôler précisément le débit vers l'API Spotify. Le sleep actuel de 100ms par requête resterait, mais réparti sur plusieurs threads il ne serait plus bloquant.

### Sc-3 — Absence d'index MongoDB
Créer les index `id` (unique) sur `playlist_tracks` et `playlist_artists`, et `date` (unique) sur `playlists_headers` dans une fonction d'initialisation appelée au démarrage de `app.py`. PyMongo gère nativement les index idempotents (`create_index` ne recrée pas un index existant).

### Sc-5 — Chargement total en mémoire pour le rapport
Pour le volume actuel (quelques milliers de tracks), ce n'est pas un problème critique. À plus long terme, la génération du rapport pourrait être déplacée directement dans MongoDB via des agrégations (`$group`, `$sort`, `$limit`) qui exécutent les calculs côté base et ne transfèrent que les résultats finaux. Cela réduirait drastiquement la mémoire utilisée par le serveur Flask.

---

## Checklist des corrections

- [x] **S-1** — `Fix(security): pass admin password via Authorization header`
- [x] **S-2** — `Fix(security): cast PASSWORD env var to string on load`
- [x] **S-3** — `Fix(security): validate dateKey format before file path interpolation`
- [x] **S-4** — `Feat(security): add IP-based rate limiting on admin endpoints`
- [x] **S-5** — `Fix(security): hide internal error details from API responses`
- [x] **S-6** — `Fix(security): gate Flask debug mode behind FLASK_DEBUG env var`
- [x] **S-7** — `Refactor(security): replace manual password check with auth decorator`
- [x] **S-9** — `Fix: move DRY_RUN flag to environment variable`
- [x] **D-1** — `Refactor: split fetch_playlist_infos into discrete pipeline steps`
- [x] **D-2** — `Refactor: pass dateKey explicitly instead of parsing from file path`
- [x] **D-3** — `Fix: surface batch error counts instead of swallowing exceptions`
- [x] **D-4** — `Feat: add retry with exponential backoff to ISRC lookups`
- [-] **D-5** — `Feat: add Spotify token manager with auto-refresh on expiry`
- [x] **D-6** — `Fix: read WRITE_TO_DATABASE mode from environment variable`
- [x] **D-7** — `Fix: deduplicate artists by ID instead of name`
- [x] **D-8** — `Chore: remove unused flop_per_day variable`
- [x] **D-9** — `Fix: rename agregate_billions to aggregate_billions`
- [-] **Sc-1** — `Feat: run scraping pipeline in background thread`
- [x] **Sc-2** — `Perf: parallelize ISRC lookups with ThreadPoolExecutor`
- [x] **Sc-3** — `Feat: create indexes on id and date fields at startup`
- [x] **Sc-4** — `Fix: add connection timeout and startup ping to MongoDB client`
- [ ] **Sc-5** — `Perf: reduce memory footprint of playlist report generation`
- [x] **Sc-6** — `Perf: remove indentation from served report.json`
