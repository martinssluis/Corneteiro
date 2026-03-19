# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

**Setup**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the server**
```powershell
python run.py
# Serves at http://localhost:5000
```

**Run all tests**
```powershell
python -m unittest discover -s tests -v
```

**Run a single test**
```powershell
python -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase.test_recomendacao_mista_ordena_e_aplica_penalizacao
```

## Environment Variables

Required in `.env` (or shell):
- `CARTOLA_API_URL` — base URL for the Cartola FC API (e.g. `https://api.cartola.globo.com`)
- `SECRET_KEY` — Flask secret key (defaults to `"dev"`)

## Architecture

This is a **stateless Flask API** that acts as a proxy/aggregation layer on top of the public Cartola FC fantasy football API. There is no database.

### Layer overview

- **`app/__init__.py`** — `create_app()` factory. Registers all blueprints with their URL prefixes and attaches global error handlers (502 for upstream Cartola failures, 404, 500). This is the composition root.
- **`app/config.py`** — `Config` class reads environment variables into Flask config keys (`CARTOLA_API_URL`, `SECRET_KEY`).
- **`app/routes/`** — One Blueprint per domain; each file handles HTTP parameter parsing and delegates entirely to a service function. No business logic lives here.
- **`app/services/`** — All business logic. Services use `current_app.config` to get `CARTOLA_API_URL`, so they **require a Flask application context** to run (important when testing or calling from outside a request).
- **`app/utils/`** — Pure helpers with no Flask dependency: `pontuacao_scouts.py` (scout event → points table), `posicoes.py` (position ID → name map), `erros.py` (`resposta_erro()` for consistent JSON error responses), `formatadores.py`.

### Service dependency graph

```
recomendacoes_service
  ├── cartola_service          (GET /atletas/mercado, /mercado/status)
  ├── cartola_parciais_service (GET /atletas/pontuados, /atletas/pontuados/{rodada})
  ├── historico_service
  │     ├── cartola_service
  │     ├── cartola_parciais_service
  │     └── pontuacao_service
  └── pontuacao_service
        └── utils/pontuacao_scouts.py

tendencia_service
  └── historico_service (see above)
```

### Recommendation criteria (`recomendacoes_service`)

Three strategies dispatched by `recomendacao_por_criterio()`:

1. **`custo_beneficio`** — ranks athletes by `media_num / preco_num` from the market endpoint.
2. **`destaques_rodada`** — ranks athletes from the current (or a specific) round's `pontuados` by either `pontuacao_cartola` or `pontuacao_calculada`.
3. **`misto`** (most expensive) — for each athlete in the market, fetches their per-round history, then computes a weighted score:
   - `score = (0.5 × fase_recente + 0.3 × consistencia + 0.2 × custo_beneficio) × (1 − penalizacao_amostra)`
   - All sub-scores are normalized to 0–10 across the candidate pool.
   - `penalizacao_amostra` penalizes athletes with fewer valid rounds than `rodadas` requested.
   - Only rounds where `entrou_em_campo == True` count as valid data points.

### `pontuacao_calculada` vs `pontuacao_cartola`

`pontuacao_cartola` is the official score from the API. `pontuacao_calculada` is recalculated locally using `pontuacao_service.calcular_pontuacao_por_scout()` and the `PONTOS_SCOUT` table in `utils/pontuacao_scouts.py`. These may differ slightly due to rounding or rule changes.

### Testing approach

Tests use `unittest` with `unittest.mock.patch`. Route tests create a Flask test client via `create_app()`. Service-level tests mock the upstream service functions directly on the module object (e.g. `patch.object(recomendacoes_service, "get_atletas_mercado", ...)`).
