# Confronto Hibrido e Enriquecimento de Nomenclaturas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar o criterio `confronto_hibrido` em `GET /recomendacoes` usando historico recente de times (5/10 rodadas) e enriquecer respostas com nomes de clube/posicao sem remover IDs.

**Architecture:** Vamos estender `recomendacoes_service` com funcoes auxiliares para identificar adversario da rodada, calcular medias cedidas por posicao em janelas curta/longa e combinar esses componentes com score individual do atleta. A rota agregadora validara novos parametros e repassara para o servico. O payload de recomendacoes sera enriquecido com metadados de clube e posicao reutilizando `clubes_service` e `utils/posicoes`.

**Tech Stack:** Python 3, Flask, unittest, unittest.mock.

---

### Task 1: Validacao de rota para novo criterio e parametros

**Files:**
- Modify: `app/routes/recomendacoes_routes.py`
- Test: `tests/test_recomendacoes.py`

- [ ] **Step 1: Write the failing test**

```python
def test_get_recomendacoes_aceita_criterio_confronto_hibrido(self):
    payload = {"criterio": "confronto_hibrido", "quantidade": 0, "recomendacoes": []}
    with patch("app.routes.recomendacoes_routes.recomendacao_por_criterio", return_value=payload):
        response = self.client.get(
            "/recomendacoes?criterio=confronto_hibrido&janela_curta=5&janela_longa=10&peso_curta=0.7&peso_longa=0.3"
        )
    self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesRouteTestCase.test_get_recomendacoes_aceita_criterio_confronto_hibrido -v`
Expected: FAIL por criterio invalido ou assinatura sem novos parametros.

- [ ] **Step 3: Write minimal implementation**

```python
CRITERIOS_SUPORTADOS = {"custo_beneficio", "destaques_rodada", "misto", "confronto_hibrido"}
# ler janela_curta, janela_longa, peso_curta, peso_longa
# validar intervalos e soma de pesos
# repassar para recomendacao_por_criterio(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesRouteTestCase.test_get_recomendacoes_aceita_criterio_confronto_hibrido -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/routes/recomendacoes_routes.py tests/test_recomendacoes.py
git commit -m "feat: validar criterio confronto_hibrido na rota de recomendacoes"
```

### Task 2: Implementacao do score de confronto hibrido no service

**Files:**
- Modify: `app/services/recomendacoes_service.py`
- Test: `tests/test_recomendacoes.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_recomendacao_confronto_hibrido_ordena_por_score_final(self):
    # mock de atletas + partidas + pontuados por rodada
    # assert ordem por score_recomendacao

def test_recomendacao_confronto_hibrido_retorna_vazio_sem_adversario(self):
    # sem partidas elegiveis
    # assert quantidade == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase.test_recomendacao_confronto_hibrido_ordena_por_score_final -v`
Expected: FAIL por funcao inexistente/criterio nao suportado.

- [ ] **Step 3: Write minimal implementation**

```python
# novos pesos internos para score final
# funcoes auxiliares:
# - identificar adversario por atleta nas partidas da rodada
# - extrair historico cedido por posicao do adversario em N rodadas
# - normalizar scores 0..10
# funcao principal recomendacao_confronto_hibrido(...)
# integrar em recomendacao_por_criterio
```

- [ ] **Step 4: Run targeted tests**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase -v`
Expected: PASS nos testes do service.

- [ ] **Step 5: Commit**

```bash
git add app/services/recomendacoes_service.py tests/test_recomendacoes.py
git commit -m "feat: adicionar criterio confronto_hibrido nas recomendacoes"
```

### Task 3: Enriquecimento de nomenclaturas de clube e posicao

**Files:**
- Modify: `app/services/recomendacoes_service.py`
- Test: `tests/test_recomendacoes.py`

- [ ] **Step 1: Write the failing test**

```python
def test_recomendacoes_incluem_nomenclaturas_sem_remover_ids(self):
    # validar clube_nome, clube_sigla, posicao_nome e ids presentes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase.test_recomendacoes_incluem_nomenclaturas_sem_remover_ids -v`
Expected: FAIL por campos ausentes.

- [ ] **Step 3: Write minimal implementation**

```python
from app.services.clubes_service import get_clubes
from app.utils.posicoes import get_posicao

# helper para enriquecer atleta com clube_nome/sigla e posicao_nome
# aplicar em custo_beneficio, misto e confronto_hibrido
```

- [ ] **Step 4: Run tests**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.RecomendacoesServiceTestCase -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/recomendacoes_service.py tests/test_recomendacoes.py
git commit -m "feat: enriquecer payload de recomendacoes com nomes de clube e posicao"
```

### Task 4: Atualizacao de documentacao

**Files:**
- Modify: `README.md`
- Modify: `docs/api-endpoints.md`

- [ ] **Step 1: Write docs changes**

```markdown
- adicionar criterio confronto_hibrido em exemplos de uso
- documentar parametros janela_curta/janela_longa/peso_curta/peso_longa
- documentar novos campos enriquecidos de clube e posicao
```

- [ ] **Step 2: Validate docs rendering quickly**

Run: `./venv/Scripts/python.exe -m unittest tests.test_recomendacoes.DocsRouteTestCase -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add README.md docs/api-endpoints.md
git commit -m "docs: atualizar recomendacoes com confronto_hibrido e nomenclaturas"
```

### Task 5: Verificacao final integrada

**Files:**
- Test: `tests/test_recomendacoes.py`

- [ ] **Step 1: Run all tests**

Run: `./venv/Scripts/python.exe -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 2: Quick smoke test manual (opcional)**

Run: `./venv/Scripts/python.exe run.py`
Then call: `GET /recomendacoes?criterio=confronto_hibrido&janela_curta=5&janela_longa=10&peso_curta=0.7&peso_longa=0.3`
Expected: resposta com `recomendacoes` e campos enriquecidos.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: confronto_hibrido com historico de times e payload enriquecido"
```
