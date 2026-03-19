# Corneteiro API

API Flask para consultar dados do Cartola, acompanhar historico de jogadores, analisar tendencia de desempenho e gerar recomendacoes de escalação.

## O Que Este Projeto Faz

O projeto expõe endpoints para:

- consultar status do mercado
- buscar atletas e clubes
- visualizar pontuacoes por rodada
- analisar historico recente de um atleta
- calcular tendencia de desempenho
- gerar recomendacoes por diferentes criterios, incluindo o criterio `misto`

## Tecnologias

- Python
- Flask
- Requests

## Como Rodar

### 1. Criar ambiente virtual

```powershell
python -m venv venv
```

### 2. Ativar o ambiente

```powershell
venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variaveis de ambiente

Defina a URL base da API do Cartola:

```powershell
$env:CARTOLA_API_URL="https://api.cartola.globo.com"
```

Opcionalmente:

```powershell
$env:SECRET_KEY="dev"
```

### 5. Subir a aplicacao

```powershell
python run.py
```

Base local esperada:

```text
http://localhost:5000
```

## Documentacao

### Guia de endpoints

Arquivo:

- [docs/api-endpoints.md](docs/api-endpoints.md)

Endpoint servido pela aplicacao:

- `GET /docs/api-endpoints`

Esse guia mostra:

- como navegar pela API
- quais parametros cada rota aceita
- quais informacoes cada endpoint retorna
- exemplos de uso

### Swagger / OpenAPI

Arquivo:

- [docs/openapi.yaml](docs/openapi.yaml)

Endpoint servido pela aplicacao:

- `GET /docs/openapi.yaml`

Esse arquivo pode ser:

- importado no Swagger Editor
- usado em clientes API compatíveis com OpenAPI
- versionado junto do codigo para manter a documentacao alinhada com a implementacao

### Indice simples de docs

- `GET /docs`

## Principais Endpoints

### Mercado

- `GET /mercado/status`

### Atletas

- `GET /atletas/status`
- `GET /atletas/{atleta_id}`
- `GET /atletas/buscar?nome={nome}`

### Pontuados

- `GET /pontuados`
- `GET /pontuados/{rodada}`
- `GET /pontuados/atleta/{atleta_id}`
- `GET /pontuados/{rodada}/atleta/{atleta_id}`

### Clubes

- `GET /clubes`
- `GET /clubes/{clube_id}`
- `GET /clubes/buscar?slug={slug}`

### Historico e Tendencia

- `GET /historico/atleta/{atleta_id}?rodadas=5`
- `GET /tendencia/atleta/{atleta_id}?rodadas=6`

### Recomendacoes

- `GET /recomendacoes?criterio=custo_beneficio`
- `GET /recomendacoes?criterio=destaques_rodada`
- `GET /recomendacoes?criterio=misto`

Endpoints legados:

- `GET /recomendacoes/custo-beneficio`
- `GET /recomendacoes/destaques-rodada`

## Testes

Para rodar os testes atuais:

```powershell
python -m unittest discover -s tests -v
```

## Estrutura Resumida

```text
app/
  routes/
  services/
  utils/
docs/
  api-endpoints.md
  openapi.yaml
tests/
run.py
```
