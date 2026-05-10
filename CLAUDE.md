# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup the virtual environment**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the development server**
```powershell
python run.py
# Serves at http://localhost:5000 with frontend SPA
```

**Run all tests**
```powershell
python -m unittest discover -s tests -v
```

**Run a single test file**
```powershell
python -m unittest tests.test_recomendacoes -v
```

**Run a specific test method**
```powershell
python -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase.test_recomendacao_mista_ordena_e_aplica_penalizacao
```

## Environment Variables

Required in `.env` (or PowerShell `$env:VAR = "value"`):
- `CARTOLA_API_URL` — base URL for the Cartola FC API (e.g. `https://api.cartola.globo.com`)
- `SECRET_KEY` — Flask secret key (optional; defaults to `"dev"`)

## Architecture Overview

This is a **stateless Flask API + vanilla JS frontend** that acts as a proxy/aggregation layer on top of the public Cartola FC fantasy football API. No database.

### Backend Architecture

**Layer separation:**
- **`app/__init__.py`** — `create_app()` factory. Registers blueprints, sets static folder for the frontend, and attaches global error handlers (502 for upstream Cartola failures, 404, 500).
- **`app/config.py`** — Reads environment variables into Flask config keys.
- **`app/routes/`** — One Blueprint per domain (e.g., `mercado_routers`, `atletas_routers`). Routes handle HTTP parameter parsing only; all business logic delegates to services.
- **`app/services/`** — All business logic lives here. **Important:** Services use `current_app.config` and **require a Flask application context** (critical when testing or calling from outside a request). Key services:
  - `cartola_service` — proxies to upstream `/atletas/mercado` and `/mercado/status` endpoints.
  - `cartola_parciais_service` — proxies `/atletas/pontuados`.
  - `recomendacoes_service` — implements ranking strategies (custo_beneficio, destaques_rodada, misto, confronto_hibrido, valorizacao).
  - `historico_service` — computes per-athlete point history.
  - `tendencia_service` — analyzes performance trends.
  - `pontuacao_service` — recalculates scores from scout events using `PONTOS_SCOUT`.
- **`app/utils/`** — Pure helpers with no Flask dependency. Notable:
  - `pontuacao_scouts.py` — lookup table for scout event → points.
  - `posicoes.py` — position ID → name mapping.
  - `erros.py` — `resposta_erro()` for consistent JSON error responses.

### Frontend Architecture

**`frontend/` is a vanilla JS single-page app:**
- **`index.html`** — Tailwind CSS + CDN build, dark mode toggle with localStorage persistence.
- **`app.js`** — Vanilla JS SPA with no framework. Consumes the Flask API at the same origin (`API_BASE = ""`). Implements:
  - Dark mode toggle with system preference detection.
  - DOM utilities (`qs`, `qsa` for query selection).
  - Currency formatting for Brazilian Real.
  - Routes for different recommendation criteria.

The frontend is served by Flask from the `frontend/` directory (see `app/__init__.py` static folder config).

## Key Patterns

**Recommendation scoring (misto criterion):**
- Fetches per-round history for all athletes.
- Computes weighted score: `(0.5 × fase_recente + 0.3 × consistencia + 0.2 × custo_beneficio) × (1 − penalizacao_amostra)`
- All sub-scores normalized to 0–10 across the pool.
- Only counts rounds where `entrou_em_campo == True`.
- Applies `penalizacao_amostra` penalty for sparse data.

**Testing:**
- Tests use `unittest` with `unittest.mock.patch`.
- Route tests create a Flask test client via `create_app()`.
- Service tests mock upstream service calls on the module object (e.g. `patch.object(recomendacoes_service, "get_atletas_mercado", ...)`).
- Routes and services are intentionally thin; test at the service layer for maximum coverage.

## Service Dependency Graph

```
recomendacoes_service
  ├── cartola_service
  ├── cartola_parciais_service
  ├── historico_service
  │     ├── cartola_service
  │     ├── cartola_parciais_service
  │     └── pontuacao_service
  └── pontuacao_service
        └── utils/pontuacao_scouts.py

tendencia_service
  └── historico_service
```
